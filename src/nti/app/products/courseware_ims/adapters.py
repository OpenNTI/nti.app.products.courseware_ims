#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.annotation import IAnnotations

from nti.app.products.courseware_ims.lti import CourseConfiguredToolContainer


TOOLS_ANNOTATION_KEY = 'lti_configured_tools'


def course_to_configured_tool_container(course, create=True):
    annotations = IAnnotations(course)
    tools = annotations.get(TOOLS_ANNOTATION_KEY)
    if create and not tools:
        tools = CourseConfiguredToolContainer()
        tools.__parent__ = course
        annotations[TOOLS_ANNOTATION_KEY] = tools
    return tools
