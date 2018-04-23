#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

from hamcrest import assert_that
from hamcrest import has_length
from hamcrest import is_

import fudge

import shutil
import tempfile

from nti.app.products.courseware.tests import PersistentInstructedCourseApplicationTestLayer

from nti.app.products.courseware_ims.exporter import IMSCourseSectionExporter

from nti.app.products.courseware_ims.importer import IMSCourseSectionImporter

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.app.products.courseware_ims.tests import create_configured_tool

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.cabinet.filer import DirectoryFiler

from nti.contenttypes.courses.courses import ContentCourseInstance

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


class TestIMSCourseSectionImportExport(ApplicationLayerTest):
    """
    Validate IMS import/export
    """

    layer = PersistentInstructedCourseApplicationTestLayer

    def _validate_target_data(self, source_course, target_course):
        source_tool_container = ICourseConfiguredToolContainer(source_course)
        target_tool_container = ICourseConfiguredToolContainer(target_course)

        assert_that(target_tool_container,
                    has_length(len(source_tool_container)))

        for source_key, target_key in zip(source_tool_container.values(),
                                          target_tool_container.values()):
            assert_that(target_key, is_(source_key))

    @fudge.patch('nti.app.products.courseware_ims.internalization.find_object_with_ntiid')
    @WithMockDSTrans
    def test_import_export(self, mock_find_object):
        tmp_dir = tempfile.mkdtemp(dir="/tmp")
        export_filer = DirectoryFiler(tmp_dir)
        source_course = ContentCourseInstance()
        target_course = ContentCourseInstance()
        conn = mock_dataserver.current_transaction
        conn.add(source_course)
        conn.add(target_course)

        exporter = IMSCourseSectionExporter()
        importer = IMSCourseSectionImporter()

        # No data
        try:
            exporter.export(source_course, export_filer)
            importer.process(target_course, export_filer)
        finally:
            shutil.rmtree(tmp_dir)
        self._validate_target_data(source_course, target_course)

        # Data
        tool1 = create_configured_tool()
        tool2 = create_configured_tool()
        tool_container = ICourseConfiguredToolContainer(source_course)
        tool_container.add_tool(tool1)  # This method is inherited from ConfiguredToolContainer
        tool_container.add_tool(tool2)

        fake_find = mock_find_object.is_callable()
        fake_find.returns(tool1)
        fake_find.next_call().returns(tool2)

        tmp_dir = tempfile.mkdtemp(dir="/tmp")
        try:
            exporter.export(source_course, export_filer)
            importer.process(target_course, export_filer)
        finally:
            shutil.rmtree(tmp_dir)
        self._validate_target_data(source_course, target_course)
