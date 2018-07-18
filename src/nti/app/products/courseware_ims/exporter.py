#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from nti.app.products.courseware_ims import IMS_CONFIGURED_TOOLS_FILE_NAME

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.contenttypes.courses.exporter import BaseSectionExporter

from nti.contenttypes.courses.interfaces import ICourseInstance
from nti.contenttypes.courses.interfaces import ICourseSectionExporter

from nti.externalization.externalization import to_external_object

from nti.externalization.interfaces import StandardExternalFields

from nti.ntiids.ntiids import find_object_with_ntiid

ITEMS = StandardExternalFields.ITEMS

logger = __import__('logging').getLogger(__name__)


@interface.implementer(ICourseSectionExporter)
class IMSCourseSectionExporter(BaseSectionExporter):

    def _get_new_ntiid(self, ntiid, salt):
        result = ntiid
        obj = find_object_with_ntiid(ntiid)
        if obj is not None:
            result = self.hash_ntiid(ntiid, salt)
        return result

    def _export_configured_tools(self, course, filer, backup, salt):
        """
        Exports the tools in the ICourseConfiguredToolContainer for this course.
        """
        tool_container = ICourseConfiguredToolContainer(course)
        ext_tools = to_external_object(tool_container)
        if not backup:
            tool_map = ext_tools.get(ITEMS) or {}
            new_tool_map = {}
            for oid, ext_tool in tool_map.items():
                new_oid = self._get_new_ntiid(oid, salt)
                new_tool_map[new_oid] = ext_tool
            ext_tools[ITEMS] = new_tool_map
        if ext_tools is not None:
            source = self.dump(ext_tools)
            filer.default_bucket = bucket = self.course_bucket(course)
            filer.save(IMS_CONFIGURED_TOOLS_FILE_NAME,
                       source,
                       overwrite=True,
                       bucket=bucket,
                       contentType="application/x-json")

    def export(self, context, filer, backup=True, salt=None):
        course = ICourseInstance(context)
        self._export_configured_tools(course, filer, backup, salt)
