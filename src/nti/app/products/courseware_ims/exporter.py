#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.app.products.courseware_ims import IMS_CONFIGURED_TOOLS_FILE_NAME

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.contenttypes.courses.exporter import BaseSectionExporter

from nti.contenttypes.courses.interfaces import ICourseInstance
from nti.contenttypes.courses.interfaces import ICourseSectionExporter

from nti.externalization.externalization import to_external_object

from nti.ntiids.ntiids import find_object_with_ntiid


@interface.implementer(ICourseSectionExporter)
class IMSCourseSectionExporter(BaseSectionExporter):

    def _get_new_ntiid(self, ntiid, salt):
        result = ntiid
        obj = find_object_with_ntiid(ntiid)
        if obj is not None:
            result = self.hash_ntiid(obj, salt)
        return result

    def _export_configured_tools(self, course, filer, backup, salt):
        """
        Exports the tools in the ICourseConfiguredToolContainer for this course.
        """
        tool_container = ICourseConfiguredToolContainer(course)
        ext_tools = to_external_object(tool_container)
        if not backup:
            ext_tools['tools'] = [self._get_new_ntiid(tool_ntiid, salt)
                                  for tool_ntiid in ext_tools['tools']]
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
