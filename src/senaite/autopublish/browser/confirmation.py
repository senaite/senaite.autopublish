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

from collections import OrderedDict
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.autopublish import messageFactory as _
from senaite.autopublish.adapters.queue import AUTOPUBLISH_TASK_ID
from senaite.queue.api import is_queued
from senaite.queue.api import add_task

from bika.lims import api
from bika.lims.browser import BrowserView
from bika.lims.catalog import CATALOG_ANALYSIS_REQUEST_LISTING


class AutopublishConfirmationView(BrowserView):
    """Confirmation view for auto-publishing of samples
    """
    template = ViewPageTemplateFile("templates/auto_publish_confirm.pt")

    def __init__(self, context, request):
        super(AutopublishConfirmationView, self).__init__(context, request)
        self.context = context
        self.request = request
        self.back_url = self.context.absolute_url()

    def __call__(self):
        form = self.request.form

        # Form submit toggle
        form_submitted = form.get("submitted", False)

        # Buttons
        form_confirm = form.get("button_confirm", False)
        form_cancel = form.get("button_cancel", False)

        samples = self.get_samples()
        if not samples:
            # No samples selected
            return self.redirect(message=_("No samples selected"),
                                 level="warning")

        # Handle cancel
        if form_submitted and form_cancel:
            return self.redirect(message=_("Auto-publish of samples cancelled"))

        # Handle confirm
        if form_submitted and form_confirm:

            # Queue samples for auto-publish
            uids = form.get("selected_uids", [])
            samples = map(self.queue_sample, uids)
            if not samples:
                return self.redirect(message=_("No samples selected"),
                                     level="info")

            ids = map(api.get_id, samples)
            message = _("{} samples enqueued for auto-publish: {}").format(
                len(samples), ", ".join(ids))
            return self.redirect(message=message)

        return self.template()

    def queue_sample(self, uid):
        """Queue a sample (by uid) to the auto-publish task
        """
        sample = api.get_object_by_uid(uid)
        kwargs = {"unique": True, "__ac": api.get_request().get("__ac", "")}
        add_task(AUTOPUBLISH_TASK_ID, sample, **kwargs)
        return sample

    def get_uids(self):
        """Returns a list of uids coming from the request
        """
        uids = self.request.form.get("uids", "")
        if not uids:
            # check for the `items` parameter
            uids = self.request.form.get("items", "")
        if isinstance(uids, six.string_types):
            uids = uids.split(",")
        unique_uids = OrderedDict().fromkeys(uids).keys()
        return unique_uids

    def get_samples(self):
        """Returns a list of samples coming from the "uids" request parameter
        """
        uids = self.get_uids()
        query = dict(portal_type="AnalysisRequest", UID=uids,
                     review_state="verified")
        objects = api.search(query, CATALOG_ANALYSIS_REQUEST_LISTING)
        # Boil-out queued samples
        samples = filter(lambda o: not is_queued(o), objects)
        return map(api.get_object, samples)

    def get_samples_data(self):
        """Returns a list of Samples data
        """
        for sample in self.get_samples():
            info = self.get_base_info(sample)
            analyses = sample.getAnalyses(full_objects=False,
                                          review_state="verified")
            analyses = map(lambda an: api.get_title(an), analyses)
            analyses = sorted(list(set(analyses)))
            info.update({
                "date_received": sample.getDateReceived(),
                "date_verified": sample.getDateVerified(),
                "contact_fullname": sample.getContactFullName(),
                "contact_email": sample.getContactEmail(),
                "verified_by": sample.getVerifier(),
                "sampletype": self.get_base_info(sample.getSampleType()),
                "client": self.get_base_info(sample.getClient()),
                "analyses": ", ".join(analyses),
            })
            yield info

    def get_base_info(self, obj):
        """Extract the base info from the given object
        """
        obj = api.get_object(obj)
        return {
            "obj": obj,
            "id": api.get_id(obj),
            "uid": api.get_uid(obj),
            "title": api.get_title(obj),
            "path": api.get_path(obj),
            "url": api.get_url(obj),
        }

    def redirect(self, redirect_url=None, message=None, level="info"):
        """Redirect with a message
        """
        if redirect_url is None:
            redirect_url = self.back_url
        if message is not None:
            self.add_status_message(message, level)
        return self.request.response.redirect(redirect_url)

    def add_status_message(self, message, level="info"):
        """Set a portal status message
        """
        return self.context.plone_utils.addPortalMessage(message, level)
