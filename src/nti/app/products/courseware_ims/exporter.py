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


@interface.implementer(ICourseSectionExporter)
class IMSCourseSectionExporter(BaseSectionExporter):

    def _export_configured_tools(self, course, filer):
        """
        Exports the tools in the ICourseConfiguredToolContainer for this course.
        """
        tool_container = ICourseConfiguredToolContainer(course)
        ext_tools = to_external_object(tool_container)
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
        self._export_configured_tools(course, filer)
