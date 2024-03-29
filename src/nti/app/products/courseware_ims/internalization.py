#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from nti.app.products.courseware_ims.interfaces import IExternalToolAsset
from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.dataserver.interfaces import IDeletedObjectPlaceholder

from nti.externalization.datastructures import InterfaceObjectIO

from nti.externalization.interfaces import IInternalObjectUpdater
from nti.externalization.interfaces import StandardExternalFields

from nti.externalization.internalization import find_factory_for
from nti.externalization.internalization import update_from_external_object

from nti.ntiids.ntiids import find_object_with_ntiid

ITEMS = StandardExternalFields.ITEMS
PARSE_VALS = ('title', 'description', 'launch_url')

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
            # If we can't find it, we have hashed the ntiid and need to
            # recreate the obj
            if tool_obj is None:
                logger.warning('Cannot find tool (%s)',
                               oid)
                factory = find_factory_for(tool)
                tool_obj = factory()
                update_from_external_object(tool_obj, tool)
                if tool['deleted']:
                    interface.alsoProvides(tool_obj, IDeletedObjectPlaceholder)
            self._ext_self[tool_obj.id] = tool_obj  # We are updating the tool id from external and want to preserve
        return result


@interface.implementer(IInternalObjectUpdater)
class ExternalToolAssetUpdater(InterfaceObjectIO):

    _ext_iface_upper_bound = IExternalToolAsset

    __external_oids__ = ('ConfiguredTool',)

    def updateFromExternalObject(self, parsed, *args, **kwargs):
        # This checks to see if title and/or description have no value. If they do not, we delete
        # them so that this information is instead gleaned off the
        # ConfiguredTool
        for attr in PARSE_VALS:
            if attr in parsed and not parsed[attr]:
                del parsed[attr]
        return super(ExternalToolAssetUpdater, self).updateFromExternalObject(parsed, *args, **kwargs)
