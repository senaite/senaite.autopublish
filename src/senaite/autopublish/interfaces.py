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

from senaite.lims.interfaces import ISenaiteLIMS
from senaite.queue.interfaces import ISenaiteQueueLayer

from bika.lims.interfaces import IBikaLIMS
from zope.interface import Interface


class ISenaiteAutopublishLayer(IBikaLIMS, ISenaiteLIMS, ISenaiteQueueLayer):
    """Zope 3 browser Layer interface specific for senaite.autopublish
    This interface is referred in profiles/default/browserlayer.xml.
    All views and viewlets register against this layer will appear in the site
    only when the add-on installer has been run.
    """


class IAutopublishConfirmationView(Interface):
    """Marker interface for Auto-publish confirmation view
    """
