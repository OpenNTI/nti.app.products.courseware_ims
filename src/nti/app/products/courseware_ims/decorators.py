#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from pyramid.threadlocal import get_current_request

from zope import component
from zope import interface

from nti.app.products.courseware_ims import LTI_CONFIGURED_TOOLS
from nti.app.products.courseware_ims import LTI_EXTERNAL_TOOL_ASSETS
from nti.app.products.courseware_ims import EXTERNAL_TOOL_ASSET_LAUNCH

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer
from nti.app.products.courseware_ims.interfaces import IExternalToolAsset

from nti.contenttypes.courses.interfaces import ICourseInstance

from nti.externalization.interfaces import IExternalMappingDecorator
from nti.externalization.interfaces import StandardExternalFields

from nti.externalization.singleton import Singleton

from nti.links import Link

from nti.ntiids.ntiids import find_object_with_ntiid

LINKS = StandardExternalFields.LINKS

LAUNCH_PATH = '@@launch'

logger = __import__('logging').getLogger(__name__)


@component.adapter(ICourseInstance)
@interface.implementer(IExternalMappingDecorator)
class _CourseInstanceLinkDecorator(Singleton):

    def decorateExternalMapping(self, context, result):
        tools = ICourseConfiguredToolContainer(context)
        if tools is not None:
            _links = result.setdefault(LINKS, [])
            _links.append(Link(tools, rel=LTI_CONFIGURED_TOOLS))


@component.adapter(IExternalToolAsset)
@interface.implementer(IExternalMappingDecorator)
class _ExternalToolAssetInstanceLinkDecorator(Singleton):

    def decorateExternalMapping(self, context, result):
        request = get_current_request()
        course = ICourseInstance(request, None)
        # XXX: We should always have a course here, but because of some of the handshaking
        # required for the tool launch there are cases where the web app GETs the asset again
        # midway through the process. The course is passed in the query params in these cases
        if course is None:
            # see if the course is in the request params
            course_ntiid = request.params.get('course', None)
            course = find_object_with_ntiid(course_ntiid)
        _links = result.setdefault(LINKS, [])
        # If we can find a course, we want to decorate a link that allows for traversal
        if course is not None:
            context_ntiid = context.ntiid
            _links.append(
                Link(course,
                     rel=EXTERNAL_TOOL_ASSET_LAUNCH,
                     elements=(LTI_EXTERNAL_TOOL_ASSETS, context_ntiid, LAUNCH_PATH))
            )
        # This is less than ideal but we will directly resolve here
        else:
            logger.info(u'Unable to locate a course for External Tool Asset link decoration')
            _links.append(
                Link(context, rel=EXTERNAL_TOOL_ASSET_LAUNCH, elements=(LAUNCH_PATH,))
            )
