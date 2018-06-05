#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from nti.externalization.internalization import find_factory_for, update_from_external_object
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
        container = parsed.get(ITEMS) or {}
        for oid, tool in container.iteritems():
            tool_obj = find_object_with_ntiid(oid)
            # If we can't find it, we have hashed the ntiid and need to recreate the obj
            if tool_obj is None:
                logger.warning('Cannot find tool (%s)',
                               oid)
                factory = find_factory_for(tool)
                tool_obj = factory()
                update_from_external_object(tool_obj, tool)
            self._ext_self.add_tool(tool_obj)
        return result
