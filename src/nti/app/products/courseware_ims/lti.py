#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.annotation import IAnnotations

from zope import interface

from zope.container.contained import Contained

from zope.traversing.interfaces import IPathAdapter

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.dataserver import authorization as nauth

from nti.dataserver.authorization_acl import ace_allowing
from nti.dataserver.authorization_acl import acl_from_aces

from nti.dataserver.interfaces import ACE_DENY_ALL


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
class LTIConfiguredToolsAdapter(Contained):

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.__parent__ = context

    # TODO update to correct privileges
    def __acl__(self):
        aces = [ace_allowing(nauth.ROLE_ADMIN, type(self)),
                ACE_DENY_ALL]
        acl = acl_from_aces(aces)
        return acl
