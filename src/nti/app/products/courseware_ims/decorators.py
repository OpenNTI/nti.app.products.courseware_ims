#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer
from zope import component
from zope import interface

from nti.app.products.courseware_ims import LTI_CONFIGURED_TOOLS

from nti.contenttypes.courses.interfaces import ICourseInstance

from nti.externalization.interfaces import IExternalMappingDecorator
from nti.externalization.interfaces import StandardExternalFields

from nti.externalization.singleton import Singleton

from nti.links import Link

LINKS = StandardExternalFields.LINKS

logger = __import__('logging').getLogger(__name__)


@component.adapter(ICourseInstance)
@interface.implementer(IExternalMappingDecorator)
class _CourseInstanceLinkDecorator(Singleton):

    def decorateExternalMapping(self, context, result):
        tools = ICourseConfiguredToolContainer(context)
        if tools:
            _links = result.setdefault(LINKS, [])
            _links.append(Link(tools, rel=LTI_CONFIGURED_TOOLS))
