#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

from hamcrest import assert_that
from hamcrest import has_length
from hamcrest import is_
from hamcrest import is_not

import fudge

import shutil

import simplejson

from sympy.core.compatibility import cStringIO

import tempfile

from nti.app.products.courseware.tests import InstructedCourseApplicationTestLayer

from nti.app.products.courseware_ims.exporter import IMSCourseSectionExporter

from nti.app.products.courseware_ims.importer import IMSCourseSectionImporter

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.app.products.courseware_ims.lti import LTI_EXTERNAL_TOOL_ASSET_MIMETYPE

from nti.app.products.courseware_ims.tests import create_configured_tool

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.cabinet.filer import DirectoryFiler
from nti.cabinet.filer import read_source

from nti.contenttypes.courses.courses import ContentCourseInstance

from nti.contenttypes.presentation.group import NTICourseOverViewGroup

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.ims.lti.consumer import ConfiguredTool

from nti.ntiids.oids import to_external_ntiid_oid

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

TOOL_DATA = {
    "consumer_key": "Test Key",
    "secret": "Test Secret",
    "title": "Test",
    "description": "A test tool",
    "launch_url": "http://www.test.com",
    "secure_launch_url": "https://www.test.com",
    "MimeType": ConfiguredTool.mimeType,
    "formselector": "input"
}

ASSET_JSON = {
    "Class": "LessonOverView",
    "Items": [
        {
            "Class": "CourseOverviewGroup",
            "Items": [
                {
                    "Class": "ExternalToolAsset",
                    "ConfiguredTool": {
                        "ID": "Test"
                    },
                    "MimeType": LTI_EXTERNAL_TOOL_ASSET_MIMETYPE
                }
            ],
            "MimeType": NTICourseOverViewGroup.mimeType
        }
    ],
}


class TestIMSCourseSectionImportExport(ApplicationLayerTest):
    """
    Validate IMS import/export
    """

    layer = InstructedCourseApplicationTestLayer

    def _load(self, source):
        data = read_source(source)
        return simplejson.loads(data)

    def _dump(self, ext_obj):
        source = cStringIO()
        simplejson.dump(ext_obj,
                        source,
                        indent='\t',
                        sort_keys=True)
        source.seek(0)
        return source

    def _validate_target_data(self, source_course, target_course, copied=True):
        ntiid_copy_check = is_ if copied else is_not
        source_tool_container = ICourseConfiguredToolContainer(source_course)
        target_tool_container = ICourseConfiguredToolContainer(target_course)

        assert_that(target_tool_container,
                    has_length(len(source_tool_container)))

        for source_key, target_key in zip(source_tool_container.values(),
                                          target_tool_container.values()):
            assert_that(target_key, ntiid_copy_check(source_key))

    def _validate_asset(self, export_filer, tool, course):
        json = export_filer.get('Lessons/test.json')
        ext_obj = self._load(json)
        container = ICourseConfiguredToolContainer(course)
        tool = container.get(tool.id)
        tool_oid = to_external_ntiid_oid(tool)
        assert_that(ext_obj['Items'][0]['Items'][0]['ConfiguredTool'], is_(tool_oid))

    @fudge.patch('nti.app.products.courseware_ims.internalization.find_object_with_ntiid',
                 'nti.app.products.courseware_ims.exporter.find_object_with_ntiid')
    @WithMockDSTrans
    def test_import_export(self, mock_internal_find_object, mock_exporter_find_object):
        tmp_dir = tempfile.mkdtemp(dir="/tmp")
        export_filer = DirectoryFiler(tmp_dir)
        source_course = ContentCourseInstance()
        target_course = ContentCourseInstance()
        conn = mock_dataserver.current_transaction
        conn.add(source_course)
        conn.add(target_course)

        exporter = IMSCourseSectionExporter()
        importer = IMSCourseSectionImporter()

        # Backup with no data
        try:
            exporter.export(source_course, export_filer, backup=True, salt=1111)
            importer.process(target_course, export_filer)
        finally:
            shutil.rmtree(tmp_dir)
        self._validate_target_data(source_course, target_course, copied=True)

        # No backup with no data
        tmp_dir = tempfile.mkdtemp(dir="/tmp")
        try:
            exporter.export(source_course, export_filer, backup=False, salt=1111)
            importer.process(target_course, export_filer)
        finally:
            shutil.rmtree(tmp_dir)
        self._validate_target_data(source_course, target_course, copied=False)

        # Backup with Data
        tool1 = create_configured_tool()
        tool2 = create_configured_tool()
        conn.add(tool1)
        conn.add(tool2)
        tool_container = ICourseConfiguredToolContainer(source_course)
        tool_container.add_tool(tool1)  # This method is inherited from ConfiguredToolContainer
        tool_container.add_tool(tool2)

        fake_internal_find = mock_internal_find_object.is_callable()
        fake_internal_find.returns(tool1)
        fake_internal_find.next_call().returns(tool2)

        tmp_dir = tempfile.mkdtemp(dir="/tmp")
        try:
            exporter.export(source_course, export_filer, backup=True, salt='1111')
            importer.process(target_course, export_filer)
        finally:
            shutil.rmtree(tmp_dir)
        self._validate_target_data(source_course, target_course, copied=True)

        # No backup with data
        fake_internal_find.next_call().returns(None)
        fake_internal_find.next_call().returns(None)

        fake_exporter_find = mock_exporter_find_object.is_callable()
        fake_exporter_find.returns(tool1)
        fake_exporter_find.next_call().returns(tool2)

        target_course = ContentCourseInstance()
        conn.add(target_course)
        tmp_dir = tempfile.mkdtemp(dir="/tmp")
        lesson_source = self._dump(ASSET_JSON)
        try:
            exporter.export(source_course, export_filer, backup=False, salt='1111')
            export_filer.save('test.json', lesson_source,
                              overwrite=True,
                              bucket='Lessons',
                              contentType="application/x-json")
            importer.process(target_course, export_filer)
        finally:
            shutil.rmtree(tmp_dir)
        self._validate_target_data(source_course, target_course, copied=False)
        self._validate_asset(export_filer, tool1, target_course)
