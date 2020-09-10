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

from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.z3cform import layout
from senaite.autopublish import messageFactory as _
from zope import schema
from zope.interface import Interface


class IAutopublishControlPanel(Interface):
    """Control panel Settings
    """
    timeout = schema.Int(
        title=_(u"Timeout"),
        description=_(
            "Maximum number of seconds to wait for an url or xpath to load "
            "before being considered unreachable. Default: 10"),
        default=10,
        required=True,
    )


class AutopublishControlPanelForm(RegistryEditForm):
    schema = IAutopublishControlPanel
    schema_prefix = "senaite.autopublish"
    label = _("SENAITE AUTOPUBLISH Settings")


AutopublishControlPanelView = layout.wrap_form(AutopublishControlPanelForm,
                                               ControlPanelFormWrapper)
