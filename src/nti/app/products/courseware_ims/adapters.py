#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.annotation import IAnnotations

from ZODB.interfaces import IConnection

from nti.app.products.courseware_ims.lti import CourseConfiguredToolContainer

TOOLS_ANNOTATION_KEY = 'lti_configured_tools'


def course_to_configured_tool_container(course, create=True):
    annotations = IAnnotations(course)
    tools = annotations.get(TOOLS_ANNOTATION_KEY)
    if create and not tools:
        tools = CourseConfiguredToolContainer()
        tools.__parent__ = course
        tools.__name__ = TOOLS_ANNOTATION_KEY
        annotations[TOOLS_ANNOTATION_KEY] = tools
        connection = IConnection(course, None)
        if connection is not None and IConnection(tools, None) is None:
            connection.add(tools)
    return tools
