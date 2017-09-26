#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope.annotation import IAnnotations

from nti.app.products.courseware_ims.lti import CourseConfiguredToolContainer

from nti.contenttypes.courses.interfaces import ICourseInstance

TOOLS_ANNOTATION_KEY = 'lti_configured_tools'


def course_to_configured_tool_container(context, create=True):
    course = ICourseInstance(context)
    annotations = IAnnotations(course)
    tools = annotations.get(TOOLS_ANNOTATION_KEY)
    if create and tools is None:
        tools = CourseConfiguredToolContainer()
        tools.__parent__ = course
        tools.__name__ = TOOLS_ANNOTATION_KEY
        annotations[TOOLS_ANNOTATION_KEY] = tools
    return tools
