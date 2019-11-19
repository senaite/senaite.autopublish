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

from senaite.autopublish import messageFactory as _
from senaite.core.listing.interfaces import IListingView
from senaite.core.listing.interfaces import IListingViewAdapter
from zope.component import adapts
from zope.interface import implements

from bika.lims.browser.workflow import RequestContextAware
from bika.lims.interfaces import IWorkflowActionUIDsAdapter


class AnalysisRequestsListingViewAdapter(object):
    """Adapter that customizes the list of Samples by adding an Auto-publish
    custom transition at the bottom of the listing
    """
    adapts(IListingView)
    implements(IListingViewAdapter)

    def __init__(self, listing, context):
        self.listing = listing
        self.context = context

    def before_render(self):
        """Adds the button auto-publish (custom transition) at the bottom of
        the listing for when the filter "verified" is selected
        """
        # Custom auto-publish transition
        auto_publish = {
            "id": "auto_publish",
            "title": _("Auto-publish"),
            "help": "Unattended publication of results",
            "url": "workflow_action?action=auto_publish"
        }
        verified = filter(lambda action: action["id"] == "verified",
                          self.listing.review_states)[0]
        default_actions = verified.get("custom_transitions", [])
        default_actions.append(auto_publish)
        verified.update({"custom_transitions": default_actions})

    def folder_item(self, obj, item, index):
        return item


class WorkflowActionAutoPublishAdapter(RequestContextAware):
    """Adapter that intercepts the action auto-publish when the Auto-publish
    transition button is pressed in Samples listing and redirects to the
    auto-publish confirmation view
    """
    implements(IWorkflowActionUIDsAdapter)

    def __call__(self, action, uids):
        """Redirects to the auto-publish confirmation view
        """
        uids_str = ",".join(uids)
        url = "{}/auto_publish_confirm?uids={}".format(self.back_url, uids_str)
        return self.redirect(redirect_url=url)
