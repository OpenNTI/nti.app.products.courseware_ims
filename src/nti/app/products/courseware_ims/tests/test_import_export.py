#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

from hamcrest import assert_that
from hamcrest import has_length
from hamcrest import is_
from hamcrest import is_not
from hamcrest import not_none

import fudge

import shutil
import tempfile

from nti.app.contenttypes.presentation import VIEW_CONTENTS

from nti.app.products.courseware.tests import InstructedCourseApplicationTestLayer

from nti.app.products.courseware_ims.adapters import TOOLS_ANNOTATION_KEY

from nti.app.products.courseware_ims.exporter import IMSCourseSectionExporter

from nti.app.products.courseware_ims.importer import IMSCourseSectionImporter

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.app.products.courseware_ims.lti import LTIExternalToolAsset

from nti.app.products.courseware_ims.tests import create_configured_tool

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.cabinet.filer import DirectoryFiler

from nti.contenttypes.courses.courses import ContentCourseInstance

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.ims.lti.consumer import ConfiguredTool
from nti.ntiids.ntiids import find_object_with_ntiid

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


class TestIMSCourseSectionImportExport(ApplicationLayerTest):
    """
    Validate IMS import/export
    """

    layer = InstructedCourseApplicationTestLayer

    default_origin = 'http://janux.ou.edu'

    course_ntiid = 'tag:nextthought.com,2011-10:NTI-CourseInfo-Fall2015_CS_1323'
    course_url = '/dataserver2/%2B%2Betc%2B%2Bhostsites/platform.ou.edu/%2B%2Betc%2B%2Bsite/Courses/Fall2015/CS%201323'

    group_ntiid = 'tag:nextthought.com,2011-10:OU-NTICourseOverviewGroup-CS1323_F_2015_Intro_to_Computer_Programming.lec:01.01_LESSON.0'
    group_url = '/dataserver2/Objects/' + group_ntiid + '/' + VIEW_CONTENTS

    tool_url = course_url + '/' + TOOLS_ANNOTATION_KEY

    @classmethod
    def course_entry(cls):
        return find_object_with_ntiid(cls.course_ntiid)

    def _create_asset(self):
        # Create a Configured Tool in the CourseConfiguredToolContainer
        self.testapp.post_json(self.tool_url, TOOL_DATA, status=201)

        # Retrieve the newly created tool's ntiid
        res = self.testapp.get(self.tool_url)
        res = res.json_body
        tool = res.get('Items')[0]
        assert_that(tool.get("MimeType"), is_(ConfiguredTool.mimeType))
        self.tool_ntiid = tool.get('NTIID')

        # POST asset information to a CourseOverviewGroup for creation and
        # insertion
        asset_data = {
            "MimeType": LTIExternalToolAsset.mimeType,
            "ConfiguredTool": self.tool_ntiid
        }

        res = self.testapp.post_json(self.group_url, asset_data, status=201)

        # Test attributes of the asset info returned
        res = res.json_body
        asset_href = res.get('href')
        self.asset_ntiid = res.get('NTIID')
        assert_that(asset_href, not_none())
        assert_that(res.get("MimeType"), is_(LTIExternalToolAsset.mimeType))
        assert_that(res.get('Creator'), is_('sjohnson@nextthought.com'))

    def _validate_target_data(self, source_course, target_course, copied=True):
        ntiid_copy_check = is_ if copied else is_not
        source_tool_container = ICourseConfiguredToolContainer(source_course)
        target_tool_container = ICourseConfiguredToolContainer(target_course)

        assert_that(target_tool_container,
                    has_length(len(source_tool_container)))

        for source_key, target_key in zip(source_tool_container.values(),
                                          target_tool_container.values()):
            assert_that(target_key, ntiid_copy_check(source_key))

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
        try:
            exporter.export(source_course, export_filer, backup=False, salt='1111')
            importer.process(target_course, export_filer)
        finally:
            shutil.rmtree(tmp_dir)
        self._validate_target_data(source_course, target_course, copied=False)
