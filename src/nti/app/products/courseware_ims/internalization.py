#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from zope import component
from zope import interface

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.externalization.datastructures import InterfaceObjectIO

from nti.externalization.interfaces import IInternalObjectUpdater
from nti.externalization.interfaces import StandardExternalFields

from nti.ntiids.ntiids import find_object_with_ntiid

ITEMS = StandardExternalFields.ITEMS

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


@component.adapter(ICourseConfiguredToolContainer)
@interface.implementer(IInternalObjectUpdater)
class _CourseConfiguredToolContainerUpdater(InterfaceObjectIO):

    _ext_iface_upper_bound = ICourseConfiguredToolContainer

    def updateFromExternalObject(self, parsed, *args, **kwargs):
        result = super(_CourseConfiguredToolContainerUpdater, self).updateFromExternalObject(parsed, *args, **kwargs)
        tools = parsed.get('tools') or ()
        for ntiid in tools:
            obj = find_object_with_ntiid(ntiid)
            if obj is None:
                logger.warning('Cannot find tool (%s)',
                               ntiid)
            self._ext_self.add_tool(obj)
        return result
