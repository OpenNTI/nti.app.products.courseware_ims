#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.traversing.interfaces import IPathAdapter

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer


@interface.implementer(IPathAdapter)
def _course_to_configured_tool_container_path_adapter(context, unused):
    return ICourseConfiguredToolContainer(context)
