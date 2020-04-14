#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import


from nti.app.products.courseware_ims.interfaces import ISiteLicenseLTIPolicy

from nti.site_license.utils import get_site_license_feature_policy


def can_add_lti_tools():
    """
    Uses the site license to determine whether this site can add
    LTI tools. If a site does not have a license or policy, we
    default to `True`.
    """
    result = True
    policy = get_site_license_feature_policy(ISiteLicenseLTIPolicy)
    if policy is not None:
        result = policy.can_add_lti_tools()
    return result


def can_add_lti_asset():
    """
    Uses the site license to determine whether this site can add
    LTI tool to a lesson. If a site does not have a license or policy, we
    default to `True`.
    """
    result = True
    policy = get_site_license_feature_policy(ISiteLicenseLTIPolicy)
    if policy is not None:
        result = policy.can_add_lti_asset()
    return result
