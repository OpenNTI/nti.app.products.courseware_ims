#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

from nti.ims.lti.consumer import ConfiguredToolContainer
from zope.annotation import IAnnotations
from zope.component import interface

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


TOOLS_ANNOTATION_KEY = 'lti_configured_tools'

@interface.implementer(ICourseConfiguredToolContainer)
class CourseConfiguredToolContainer(ConfiguredToolContainer):
    pass


def course_to_configured_tool_container(course, create=True):

    annotation = IAnnotations(course)
    tools = annotation[TOOLS_ANNOTATION_KEY]
    if create and not tools:
        tools = CourseConfiguredToolContainer()
        tools.__parent__ = course
    return tools