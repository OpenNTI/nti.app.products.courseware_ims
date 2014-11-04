#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904,E1121

from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that

import os

from zope import component

from nti.contenttypes.courses.interfaces import ICourseCatalog

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.app.testing.webtest import TestApp
from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.products.courseware.tests import InstructedCourseApplicationTestLayer

class TestWorkflow(ApplicationLayerTest):
	
	layer = InstructedCourseApplicationTestLayer

	default_origin = str('http://janux.ou.edu')
	course_ntiid = 'tag:nextthought.com,2011-10:NTI-CourseInfo-Fall2013_CLC3403_LawAndJustice'

	@classmethod
	def catalog_entry(self):
		catalog = component.getUtility(ICourseCatalog)
		for entry in catalog.iterCatalogEntries():
			if entry.ntiid == self.course_ntiid:
				return entry
	
	@WithSharedApplicationMockDS(testapp=True,users=True)
	def test_create_users(self):
		ims_xml = os.path.join(os.path.dirname(__file__), 'ims_enroll.xml')
		
		environ = self._make_extra_environ()
		environ[b'HTTP_ORIGIN'] = b'http://platform.ou.edu'

		data = {'ims_file':ims_xml}
		testapp = TestApp(self.app)
		res = testapp.post_json('/dataserver2/IMS/@@create_users', data,
				  				extra_environ=environ,
						  		status=200)
		
		assert_that(res.json_body, has_entry('Created', has_length(2)))