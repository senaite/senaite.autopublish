# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.AUTOPUBLISH.
#
# SENAITE.AUTOPUBLISH is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright 2019-2020 by it's authors.
# Some rights reserved, see README and LICENSE.

import six
import time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from senaite.autopublish import logger
from senaite.queue.interfaces import IQueuedTaskAdapter
from zope.component import adapts
from zope.interface import implements

from bika.lims import api
from bika.lims import workflow as wf
from bika.lims.interfaces import IAnalysisRequest

# Id of the queue
AUTOPUBLISH_TASK_ID = "senaite.autopublish.task_autopublish"


class QueuedAutopublishTaskAdapter(object):
    """Adapter in charge to auto-publish the queued samples
    """
    implements(IQueuedTaskAdapter)
    adapts(IAnalysisRequest)

    def __init__(self, context):
        self.context = context
        self.task = None
        self._timeout = None

    @property
    def timeout(self):
        """Returns the maximum number of seconds to wait for an url or xpath
        to load before being considered unreachable
        """
        if self._timeout is None:
            # Get the time out from the settings
            registry_id = "senaite.autopublish.timeout"
            timeout = api.get_registry_record(registry_id, None)
            self._timeout = api.to_int(timeout, default=10)
        return self._timeout

    @property
    def report_only(self):
        """Returns whether the generation of the results report has been
        requested for the on-going task
        """
        report_only = self.request.get("report_only", "0")
        return report_only == "1"

    @property
    def request(self):
        """Return the current request
        """
        return api.get_request()

    def process(self, task):
        """Processes the task of auto-publishing a queued sample
        """
        self.task = task
        if api.get_uid(self.context) != task.context_uid:
            raise ValueError("Task's context does not match with self.context")

        # Do not auto-publish if the sample is in published status already
        if api.get_review_status(self.context) not in ["verified"]:
            logger.warn("Not a verified sample: {}".format(repr(self.context)))
            return

        # Auto-publish task
        self.auto_publish(self.context, self.report_only)

    def auto_publish(self, sample, report_only):
        """Does the auto-publish of the sample
        """
        logger.info("Auto-publishing sample {} ...".format(repr(sample)))

        # New headless browser session
        browser = None
        try:
            browser = self.get_headless_browser_session()
            if report_only:
                self.generate_report_only(browser, sample)
                wf.doActionFor(sample, "publish")
            else:
                self.generate_report_and_email(browser, sample)
        except Exception as e:
            self.close_session(browser)
            raise e

        self.close_session(browser)

    def close_session(self, browser):
        """Closes the browser windows and terminates chromedriver
        """
        if browser:
            try:
                browser.quit()
            except:
                pass

    def generate_report_only(self, browser, sample):
        """Generates and stores the results report for the sample passed in
        """
        # Generate preview
        self.generate_preview(browser, sample)

        # Save the report
        logger.info("Saving the report for {} ...".format(repr(sample)))
        browser.find_element_by_name("save").click()

    def generate_report_and_email(self, browser, sample):
        """Generates and emails the results report for the sample passed in
        """
        # Generate preview
        self.generate_preview(browser, sample)

        # Generate email view
        logger.info("Generating email view for {} ...".format(repr(sample)))
        browser.find_element_by_name("email").click()

        # Wait until the view gets rendered
        xpath = "//form[@id='send_email_form']/input[@name='send']"
        self.wait_for_xpath(browser, xpath)

        # Send the Email
        logger.info("Sending report {} ...".format(repr(sample)))
        browser.find_element_by_name("send").click()

        # Wait until the send process finishes
        #xpath = "//span[@class='documentFirstHeading']"
        #self.wait_for_xpath(browser, xpath)

    def generate_preview(self, browser, sample):
        """Generates the results report preview for the sample passed in
        """
        logger.info("Generating preview for {} ...".format(repr(sample)))
        xpath = "//div[@id='preview']/div[@class='report']/img"
        publish_url = self.get_publish_url(api.get_uid(sample))
        self.get(browser, publish_url, xpath=xpath)

    def get_publish_url(self, uids):
        """Returns the senaite's publish url
        """
        if isinstance(uids, six.string_types):
            uids = [uids]
        return "{}/analysisrequests/publish?items={}".format(
            self.portal_url, ",".join(uids))

    def has_xpath_element(self, browser, xpath):
        """Returns whether an xpath element exists in the browser
        """
        try:
            if browser.find_element_by_xpath(xpath):
                return True
        except:
            return False

    def get_headless_browser_session(self):
        """Returns a headless browser session in senaite
        """
        browser = None
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('disable-infobars')
            options.add_argument("--disable-extensions")
            options.add_argument('--ignore-certificate-errors')
            browser = webdriver.Chrome(chrome_options=options)
            self.authenticate(browser)
        except Exception as e:
            self.close_session(browser)
            raise e

        return browser

    def get(self, browser, url, xpath=None):
        """Returns True when the url provided has been loaded succesfully in
        the browser instance passed in.
        :param browser: the webdriver's browser instance
        :param url: the url to load
        :param timeout: max. number of seconds to wait for the page to render
        :param xpath: the element to wait for after the page is loaded
        :param xpath_timeout: max. number of seconds to wait for the xpath
        """
        # Load the URL provided
        url = self.resolve_url(url)
        logger.info("URL: {}".format(url))
        browser.set_page_load_timeout(self.timeout)
        browser.get(url)
        logger.info("Loaded: {}".format(url))
        if xpath:
            # We need to wait for xpath to be rendered
            self.wait_for_xpath(browser, xpath)

        return True

    def resolve_url(self, url):
        """Resolves the url to the zeo client configured in settings
        """
        registry_id = "senaite.autopublish.base_url"
        base_url = api.get_registry_record(registry_id)
        if not base_url:
            return url

        # Replace the current base url with registry's
        return url.replace(self.portal_url, base_url)

    def wait_for_xpath(self, browser, xpath):
        """Waits for an xpath to be rendered in the current browser page
        """
        start = time.time()
        while not self.has_xpath_element(browser, xpath):
            end = time.time()
            if end - start > self.timeout:
                msg = "Timeout for xpath='{}' [SKIP]".format(xpath)
                raise TimeoutException(msg)
            # Look for the xpath in 1sec.
            time.sleep(1)

    @property
    def portal_url(self):
        """Returns senaite's base url
        """
        return api.get_url(api.get_portal())

    def authenticate(self, browser):
        """Authenticates the browser session against senaite
        """
        logger.info("Trying to authenticate ...")

        # We add the cookie of the current authenticated user, cause login_as
        # form is only accessible to users with ModifyPortal privileges
        ac = self.request.get("__ac", "")
        # To add the cookie we need to visit the site first. Just visit an
        # static resource to make the thing faster
        queue_resource = "++resource++senaite.queue.static/queued.gif"
        dummy_url = "{}/{}".format(self.portal_url, queue_resource)
        self.get(browser, dummy_url)
        browser.add_cookie({"name": "__ac", "value": ac})

        # Login as the user who triggered the auto-publish task
        login_as = "{}/{}".format(api.get_url(self.context), "login_as")
        if self.get(browser, login_as):
            if "username" in browser.page_source:
                username = browser.find_element_by_id("username")
                task_uid = browser.find_element_by_id("taskuid")
                if username:
                    username.send_keys(self.task.username)
                    task_uid.send_keys(self.task.task_uid)
                    browser.find_element_by_name("submit").click()
                    return "Authenticated" in browser.page_source

        raise RuntimeError("Unable to Authenticate")

    def members(self):
        """ lists all members on this Plone site """
        membership = api.get_tool('portal_membership')
        members = membership.listMembers()
        results = []
        for member in members:
            results.append({'username': member.id,
                            'fullname': member.getProperty('fullname')})
        return results
