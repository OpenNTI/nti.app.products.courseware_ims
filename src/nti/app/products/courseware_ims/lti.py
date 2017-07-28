#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.annotation import IAnnotations

from zope import interface

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.ims.lti.consumer import ConfiguredToolContainer

TOOLS_ANNOTATION_KEY = 'lti_configured_tools'


@interface.implementer(ICourseConfiguredToolContainer)
class CourseConfiguredToolContainer(ConfiguredToolContainer):
    pass


def course_to_configured_tool_container(course, create=True):

    annotation = IAnnotations(course)
    tools = annotation.get(TOOLS_ANNOTATION_KEY)
    if create and not tools:
        tools = CourseConfiguredToolContainer()
        tools.__parent__ = course
    return tools
