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

import time

import six
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from senaite.autopublish import logger
from senaite.queue import api as queue_api
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

    @property
    def timeout(self):
        """Returns the maximum number of seconds to wait for an url or xpath
        to load before being considered unreachable
        """
        return 300

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

        # Auto-publish task
        self.auto_publish(self.context, self.report_only, self.timeout)

    def auto_publish(self, sample, report_only, timeout):
        """Does the auto-publish of the sample
        """
        logger.info("Auto-publishing sample {} ...".format(repr(sample)))

        # New headless browser session
        browser = None
        try:
            browser = self.get_headless_browser_session()
            if report_only:
                self.generate_report_only(browser, sample, timeout)
                wf.doActionFor(sample, "publish")
            else:
                self.generate_report_and_email(browser, sample, timeout)
        except (WebDriverException, TimeoutException, RuntimeError,
                Exception) as e:
            if browser:
                # Close the browser gracefully
                try:
                    browser.quit()
                except:
                    pass
            raise e

    def generate_report_only(self, browser, sample, timeout):
        """Generates and stores the results report for the sample passed in
        """
        # Generate preview
        self.generate_preview(browser, sample, timeout)

        # Save the report
        logger.info("Saving the report for {} ...".format(repr(sample)))
        browser.find_element_by_name("save").click()

    def generate_report_and_email(self, browser, sample, timeout):
        """Generates and emails the results report for the sample passed in
        """
        # Generate preview
        self.generate_preview(browser, sample, timeout)

        # Generate email view
        logger.info("Generating email view for {} ...".format(repr(sample)))
        browser.find_element_by_name("email").click()

        # Wait until the view gets rendered
        xpath = "//form[@id='send_email_form']/input[@name='send']"
        self.wait_for_xpath(browser, xpath, timeout=timeout)

        # Send the Email
        logger.info("Sending report {} ...".format(repr(sample)))
        browser.find_element_by_name("send").click()

        # Wait until the send process finishes
        xpath = "//span[@class='documentFirstHeading']"
        self.wait_for_xpath(browser, xpath)

    def generate_preview(self, browser, sample, timeout):
        """Generates the results report preview for the sample passed in
        """
        logger.info("Generating preview for {} ...".format(repr(sample)))
        xpath = "//div[@id='preview']/div[@class='report']/img"
        publish_url = self.get_publish_url(api.get_uid(sample))
        self.get(browser, publish_url, xpath=xpath, timeout=timeout)

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
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        browser = webdriver.Chrome(chrome_options=options)
        self.authenticate(browser)
        return browser

    def get(self, browser, url, timeout=600, xpath=None, xpath_timeout=300):
        """Returns True when the url provided has been loaded succesfully in
        the browser instance passed in.
        :param browser: the webdriver's browser instance
        :param url: the url to load
        :param timeout: max. number of seconds to wait for the page to render
        :param xpath: the element to wait for after the page is loaded
        :param xpath_timeout: max. number of seconds to wait for the xpath
        """
        # Load the URL provided
        logger.info("URL: {}".format(url))
        browser.set_page_load_timeout(timeout)
        browser.get(url)
        logger.info("Loaded: {}".format(url))
        if xpath:
            # We need to wait for xpath to be rendered
            self.wait_for_xpath(browser, xpath, timeout=xpath_timeout)

        return True

    def wait_for_xpath(self, browser, xpath, timeout=300):
        """Waits for an xpath to be rendered in the current browser page
        """
        start = time.time()
        while not self.has_xpath_element(browser, xpath):
            end = time.time()
            if end - start > timeout:
                msg = "Timeout for xpath='{}' [SKIP]".format(xpath)
                raise TimeoutException(msg)
            elif (end - start) % 5 == 0:
                logger.info("Sleep 5s ...")
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
        dummy_url = queue_api.get_queue_image_url("queued.gif")
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
