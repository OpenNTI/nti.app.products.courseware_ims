#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from nti.app.products.courseware_ims.interfaces import ISiteLicenseLTIPolicy


@interface.implementer(ISiteLicenseLTIPolicy)
class StarterSiteLicenseLTIPolicy(object):

    def can_add_lti_tools(self):
        return False
    can_add_lti_asset = can_add_lti_tools

TrialSiteLicenseLTIPolicy = StarterSiteLicenseLTIPolicy


@interface.implementer(ISiteLicenseLTIPolicy)
class GrowthSiteLicenseLTIPolicy(object):

    def can_add_lti_tools(self):
        return True
    can_add_lti_asset = can_add_lti_tools

EnterpriseSiteLicenseLTIPolicy = GrowthSiteLicenseLTIPolicy

