#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.annotation import IAnnotations

from zope import component
from zope import interface

from zope.traversing.interfaces import IPathAdapter

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.dataserver import authorization as nauth

from nti.dataserver.authorization_acl import ace_denying
from nti.dataserver.authorization_acl import ace_allowing
from nti.dataserver.authorization_acl import acl_from_aces

from nti.dataserver.interfaces import IACLProvider

from nti.ims.lti.consumer import ConfiguredToolContainer

TOOLS_ANNOTATION_KEY = 'lti_configured_tools'

CRUD = (nauth.ACT_CREATE.id,
        nauth.ACT_READ.id,
        nauth.ACT_UPDATE.id,
        nauth.ACT_DELETE.id,)

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


@interface.implementer(IACLProvider)
@component.adapter(ICourseConfiguredToolContainer)
class _CourseConfiguredToolContainerACLProvider(object):

    def __init__(self, context):
        course = context.__parent__

        aces = [ace_allowing(x, CRUD)
                for x in course.instructors]
        aces.append(ace_allowing(nauth.ROLE_CONTENT_EDITOR, CRUD))

        self.__acl__ = acl_from_aces(aces)