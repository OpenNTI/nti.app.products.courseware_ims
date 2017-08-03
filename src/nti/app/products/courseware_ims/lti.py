#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.annotation import IAnnotations

from zope import interface

from zope.traversing.interfaces import IPathAdapter

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.ims.lti.consumer import ConfiguredToolContainer

TOOLS_ANNOTATION_KEY = 'lti_configured_tools'


@interface.implementer(ICourseConfiguredToolContainer)
class CourseConfiguredToolContainer(ConfiguredToolContainer):
    pass


def course_to_configured_tool_container(course, create=True):
    annotations = IAnnotations(course)
    tools = annotations.get(TOOLS_ANNOTATION_KEY)
    if create and not tools:
        tools = CourseConfiguredToolContainer()
        tools.__parent__ = course
        annotations[TOOLS_ANNOTATION_KEY] = tools
    return tools


@interface.implementer(IPathAdapter)
def _course_to_configured_tool_container_path_adapter(context, request):
    return ICourseConfiguredToolContainer(context)


def _create_tool_path_adapter(context, request):
    pass


def _edit_tool_path_adapter(context, request):
    pass


def _delete_tool_path_adapter(context, request):
    pass
