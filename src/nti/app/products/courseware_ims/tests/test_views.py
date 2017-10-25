#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904,E1121

from hamcrest import is_, not_none
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that

import os
import fudge

from zope import component

from nti.contenttypes.courses.interfaces import ICourseCatalog
from nti.contenttypes.courses.interfaces import ICourseInstance

from nti.app.contenttypes.presentation import VIEW_CONTENTS

from nti.app.products.courseware.tests import InstructedCourseApplicationTestLayer

from nti.app.products.courseware_ims.adapters import TOOLS_ANNOTATION_KEY

from nti.app.products.courseware_ims.lti import LTIExternalToolAsset

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.app.testing.webtest import TestApp

from nti.dataserver.tests import mock_dataserver

from nti.ims.lti.consumer import ConfiguredTool

from nti.ntiids.ntiids import find_object_with_ntiid

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


class TestLTIAsset(ApplicationLayerTest):

    layer = InstructedCourseApplicationTestLayer

    default_origin = 'http://janux.ou.edu'

    course_ntiid = 'tag:nextthought.com,2011-10:NTI-CourseInfo-Fall2015_CS_1323'
    course_url = '/dataserver2/%2B%2Betc%2B%2Bhostsites/platform.ou.edu/%2B%2Betc%2B%2Bsite/Courses/Fall2015/CS%201323'

    group_ntiid = 'tag:nextthought.com,2011-10:OU-NTICourseOverviewGroup-CS1323_F_2015_Intro_to_Computer_Programming.lec:01.01_LESSON.0'
    group_url = '/dataserver2/Objects/' + group_ntiid + '/' + VIEW_CONTENTS

    tool_url = course_url + '/' + TOOLS_ANNOTATION_KEY

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_asset(self):
        # Create a Configured Tool in the CourseConfiguredToolContainer
        self.testapp.post_json(self.tool_url, TOOL_DATA, status=201)

        # Retrieve the newly created tool's ntiid
        res = self.testapp.get(self.tool_url)
        res = res.json_body
        tool = res.get('Items')[0]
        assert_that(tool.get("MimeType"), is_(ConfiguredTool.mimeType))
        tool_ntiid = tool.get('NTIID')

        # POST asset information to a CourseOverviewGroup for creation and
        # insertion
        asset_data = {
            "MimeType": LTIExternalToolAsset.mimeType,
            "ConfiguredTool": tool_ntiid
        }
        res = self.testapp.post_json(self.group_url, asset_data, status=201)

        # Test attributes of the asset info returned
        res = res.json_body
        asset_href = res.get('href')
        asset_ntiid = res.get('NTIID')
        assert_that(asset_href, not_none())
        assert_that(res.get("MimeType"), is_(LTIExternalToolAsset.mimeType))
        assert_that(res.get('Creator'), is_('sjohnson@nextthought.com'))

        # Test that the contained ConfiguredTool is the right object
        with mock_dataserver.mock_db_trans(self.ds, 'janux.ou.edu'):
            asset = find_object_with_ntiid(asset_ntiid)
            tool = find_object_with_ntiid(tool_ntiid)
            assert_that(asset.ConfiguredTool, is_(tool))
            assert_that(tool.secret, is_(TOOL_DATA.get('secret')))
            assert_that(tool.consumer_key, is_(TOOL_DATA.get('consumer_key')))
            assert_that(tool.launch_url, is_(TOOL_DATA.get('launch_url')))
            assert_that(tool.secure_launch_url, is_(TOOL_DATA.get('secure_launch_url')))
            # these properties should not be None
            assert_that(asset.title, is_(TOOL_DATA.get('title')))
            assert_that(asset.description, is_(TOOL_DATA.get('description')))

    def test_subscribers(self):
        pass

class TestWorkflow(ApplicationLayerTest):

    layer = InstructedCourseApplicationTestLayer

    default_origin = 'http://janux.ou.edu'
    course_ntiid = 'tag:nextthought.com,2011-10:NTI-CourseInfo-Fall2013_CLC3403_LawAndJustice'

    @classmethod
    def catalog_entry(self):
        catalog = component.getUtility(ICourseCatalog)
        for entry in catalog.iterCatalogEntries():
            if entry.ntiid == self.course_ntiid:
                return entry

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_create_users(self):
        ims_xml = os.path.join(os.path.dirname(__file__), 'ims_enroll.xml')

        environ = self._make_extra_environ()
        environ['HTTP_ORIGIN'] = 'http://platform.ou.edu'

        data = {'ims_file': ims_xml}
        testapp = TestApp(self.app)
        res = testapp.post_json('/dataserver2/IMS/@@nti_create_users', data,
                                extra_environ=environ,
                                status=200)

        assert_that(res.json_body, has_entry('Items', has_length(2)))
        assert_that(res.json_body, has_entry('Total', is_(2)))

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_workflow_process_invalid_file(self):
        ims_xml = os.path.join(os.path.dirname(__file__), 'foo.xml')

        environ = self._make_extra_environ()
        environ['HTTP_ORIGIN'] = 'http://platform.ou.edu'

        data = {'ims_file': ims_xml}
        testapp = TestApp(self.app)
        testapp.post_json('/dataserver2/IMS/@@nti_enrollment', data,
                          extra_environ=environ,
                          status=422)

    @WithSharedApplicationMockDS(testapp=True, users=True)
    @fudge.patch('nti.app.products.courseware_ims.views.find_ims_courses')
    def test_ims_courses(self, mock_fic):
        environ = self._make_extra_environ()
        environ['HTTP_ORIGIN'] = 'http://platform.ou.edu'

        with mock_dataserver.mock_db_trans(self.ds, site_name='platform.ou.edu'):
            entry = self.catalog_entry()
            course = ICourseInstance(entry)
            courses = {'26235.20131': course}
            mock_fic.is_callable().with_args().returns(courses)

        testapp = TestApp(self.app)
        res = testapp.get('/dataserver2/IMS/@@nti_courses',
                          extra_environ=environ,
                          status=200)
        assert_that(res.json_body, has_entry('Total', 1))
