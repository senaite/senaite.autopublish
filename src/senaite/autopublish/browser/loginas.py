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

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.queue.api import get_queue

from bika.lims import api
from bika.lims.interfaces import IAnalysisRequest


class LoginAs(BrowserView):

    template = ViewPageTemplateFile("templates/loginas.pt")

    def __init__(self, context, request):
        super(LoginAs, self).__init__(context, request)
        self.context = context
        self.request = request

    def __call__(self):
        # We only allow access to this page if the current context is a queued
        # Sample and it's status is "verified"
        if not IAnalysisRequest.providedBy(self.context):
            return "Not a sample"
        if api.get_review_status(self.context) != "verified":
            return "Not in verified status"

        form = self.request.form
        form_submitted = form.get("submitted", False)
        form_login = form.get("submit", False)

        # Handle login
        if form_submitted and form_login:
            username = form.get("username", "")
            if not username:
                return "No username provided"

            task_uid = form.get("taskuid", "")
            if not task_uid:
                return "No task UID provided"

            # Check if a task for the given task uid exists
            qtool = get_queue()
            task = qtool.get_task(task_uid)
            if not task:
                return "No task found for {}".format(task_uid)

            # Check if the user passed-in is responsible of this task
            if not task.username:
                return "No user defined for {}".format(task_uid)

            if task.username != username:
                return "No valid user {} for task {}".format(username, task_uid)

            # Check if the current context is the same as the task's
            if task.context_uid != api.get_uid(self.context):
                return "No valid context for task {}".format(task_uid)

            # Get the user
            acl_users = api.get_tool("acl_users")
            if not acl_users.getUserById(username):
                return "User does not exist: {}".format(username)

            # Authenticate
            acl_users.session._setupSession(username, self.request.response)
            return "Authenticated"

        return self.template()
