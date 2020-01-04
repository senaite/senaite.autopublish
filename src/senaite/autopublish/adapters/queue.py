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
# Copyright 2019 by it's authors.
# Some rights reserved, see README and LICENSE.

import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from senaite.autopublish import api
from senaite.autopublish import logger
from senaite.queue.adapters import QueuedTaskAdapter
from zope.component import adapts

from bika.lims import workflow as wf
from bika.lims.interfaces import IAnalysisRequest

# Id of the queue
AUTOPUBLISH_TASK_ID = "senaite.autopublish.task_autopublish"


class QueuedAutopublishTaskAdapter(QueuedTaskAdapter):
    """Adapter in charge to auto-publish the queued samples
    """
    adapts(IAnalysisRequest)

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

    def process(self, task, request):
        """Processes the task of auto-publishing a queued sample
        """
        self.request = request
        self.task = task
        if self.context != task.context:
            logger.error("Task's context does not match with self.context")
            return False

        # Auto-publish task
        success = self.auto_publish(self.context, self.report_only, self.timeout)
        if success:
            # Update the sample object (we've done the publish in a new thread)
            task.context._p_jar.sync()

        return success

    def auto_publish(self, sample, report_only, timeout):
        """Does the auto-publish of the sample
        """
        logger.info("Auto-publishing sample {} ...".format(repr(sample)))

        # New headless browser session
        browser = self.get_headless_browser_session()
        if not browser:
            return False

        success = False
        if report_only:
            if self.generate_report_only(browser, sample, timeout):
                success = wf.doActionFor(sample, "publish")
        else:
            success = self.generate_report_and_email(browser, sample, timeout)

        # Close the browser gracefully
        browser.close()
        return success

    def generate_report_only(self, browser, sample, timeout):
        """Generates and stores the results report for the sample passed in
        """
        # Generate preview
        if not self.generate_preview(browser, sample, timeout):
            return False

        # Save the report
        logger.info("Saving the report for {} ...".format(repr(sample)))
        browser.find_element_by_name("save").click()
        return True

    def generate_report_and_email(self, browser, sample, timeout):
        """Generates and emails the results report for the sample passed in
        """
        # Generate preview
        if not self.generate_preview(browser, sample, timeout):
            return False

        # Generate email view
        logger.info("Generating email view for {} ...".format(repr(sample)))
        browser.find_element_by_name("email").click()

        # Wait until the view gets rendered
        xpath = "//form[@id='send_email_form']/input[@name='send']"
        if not self.wait_for_xpath(browser, xpath, timeout=timeout):
            return False

        # Send the Email
        logger.info("Sending report {} ...".format(repr(sample)))
        browser.find_element_by_name("send").click()
        return True

    def generate_preview(self, browser, sample, timeout):
        """Generates the results report preview for the sample passed in
        """
        logger.info("Generating preview for {} ...".format(repr(sample)))
        xpath = "//div[@id='preview']/div[@class='report']/img"
        publish_url = self.get_publish_url(api.get_uid(sample))
        return self.get(browser, publish_url, xpath=xpath, timeout=timeout)

    def get_publish_url(self, uids):
        """Returns the senaite's publish url
        """
        if isinstance(uids, basestring):
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
            options.add_argument('headless')
            browser = webdriver.Chrome(chrome_options=options)
            if browser and self.authenticate(browser):
                return browser
        except WebDriverException as ex:
            logger.error("WebDriverException: {}".format(ex.msg))

        if browser:
            # Close the browser session gracefully
            browser.quit()
        return None

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
        try:
            browser.set_page_load_timeout(timeout)
            browser.get(url)
        except TimeoutException:
            logger.warn("Timeout ({}s) when loading {}".format(timeout, url))
            return False
        logger.info("Loaded: {}".format(url))

        if xpath:
            # We need to wait for xpath to be rendered
            return self.wait_for_xpath(browser, xpath, timeout=xpath_timeout)

        return True

    def wait_for_xpath(self, browser, xpath, timeout=300):
        """Waits for an xpath to be rendered in the current browser page
        """
        start = time.time()
        while not self.has_xpath_element(browser, xpath):
            end = time.time()
            if end - start > timeout:
                logger.error("Timeout for xpath='{}' [SKIP]".format(xpath))
                return False
            elif (end - start) % 5 == 0:
                logger.info("Sleep 5s ...")
            # Look for the xpath in 1sec.
            time.sleep(1)

        return True

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
        dummy_url = api.get_queue_image_url("queued.gif")
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

        logger.error("Unable to Authenticate")
        return False

    def members(self):
        """ lists all members on this Plone site """

        membership = api.get_tool('portal_membership')
        members = membership.listMembers()
        results = []
        for member in members:
            results.append({'username': member.id,
                            'fullname': member.getProperty('fullname')})
        return results
