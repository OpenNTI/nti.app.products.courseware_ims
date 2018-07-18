#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from zope.traversing.interfaces import IPathAdapter

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IPathAdapter)
def _course_to_configured_tool_container_path_adapter(context, unused_req):
    return ICourseConfiguredToolContainer(context)
