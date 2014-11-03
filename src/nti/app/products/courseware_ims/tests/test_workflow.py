#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904,E1121

from hamcrest import is_
from hamcrest import none
from hamcrest import is_in
from hamcrest import is_not
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property

import os
import fudge

from zope import component

from nti.app.products.courseware_ims.workflow import process
from nti.app.products.courseware_ims.workflow import cmp_proxy
from nti.app.products.courseware_ims.workflow import create_users

from nti.dataserver.users import User

from nti.contenttypes.courses.interfaces import ES_PUBLIC
from nti.contenttypes.courses.interfaces import ES_CREDIT_DEGREE

from nti.contenttypes.courses.interfaces import ICourseCatalog
from nti.contenttypes.courses.interfaces import ICourseInstance
from nti.contenttypes.courses.interfaces import ICourseEnrollments

from nti.ims.feed.enterprise import Enterprise

import nti.dataserver.tests.mock_dataserver as mock_dataserver
from nti.dataserver.tests.mock_dataserver import WithMockDSTrans
from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.products.courseware.tests import InstructedCourseApplicationTestLayer

class TestWorkflow(ApplicationLayerTest):
	
	_PROTECTED_SCOPE = ES_CREDIT_DEGREE
	_PROTECTED_SCOPE_NAME = _PROTECTED_SCOPE
	
	layer = InstructedCourseApplicationTestLayer

	default_origin = str('http://janux.ou.edu')
	course_ntiid = 'tag:nextthought.com,2011-10:NTI-CourseInfo-Fall2013_CLC3403_LawAndJustice'

	@classmethod
	def catalog_entry(self):
		catalog = component.getUtility(ICourseCatalog)
		for entry in catalog.iterCatalogEntries():
			if entry.ntiid == self.course_ntiid:
				return entry

	def _create_user(self, username, password='temp001'):
		ds = mock_dataserver.current_mock_ds
		usr = User.create_user(ds, username=username, password=password)
		return usr
	
	def test_order(self):
		ims_xml = os.path.join(os.path.dirname(__file__), 'ims_enroll_drop.xml')
		ims = Enterprise.parseFile(ims_xml)
		
		members = list(ims.get_all_members())
		assert_that(members, has_length(2))
		assert_that(members[0], has_property('course_id', is_not(none())))
		assert_that(members[0], has_property('is_active', is_(False)))
		assert_that(members[1], has_property('course_id', is_not(none())))
		assert_that(members[1], has_property('is_active', is_(True)))
		
		assert_that(members[0].course_id, is_((members[1].course_id)))
		assert_that(members[0].sourcedid, is_(members[1].sourcedid))
		
		members = sorted(members, cmp=cmp_proxy)
		assert_that(members[0], has_property('is_active', is_(True)))
		assert_that(members[1], has_property('is_active', is_(False)))

	@WithMockDSTrans
	def test_create_users(self):
		ims_xml = os.path.join(os.path.dirname(__file__), 'ims_enroll.xml')
		result = create_users(ims_xml)
		assert_that(result, has_length(2))
		user = User.get_user('jobs2213')
		assert_that(user, is_not(none()))
		result = create_users(ims_xml)
		assert_that(result, has_length(0))

	@WithSharedApplicationMockDS
	@fudge.patch('nti.app.products.courseware_ims.workflow.find_ims_courses')
	def test_simple_workflow(self, mock_fic):
			
		ims_xml = os.path.join(os.path.dirname(__file__), 'ims_enroll.xml')
		ims_un_xml = os.path.join(os.path.dirname(__file__), 'ims_unenroll.xml')

		# create professor and student, in the global site because the names
		# are invalid in OU site
		with mock_dataserver.mock_db_trans(self.ds):
			self._create_user('cald3307')
			self._create_user('jobs2213')
			self._create_user('jobs2299')

		with mock_dataserver.mock_db_trans(self.ds, site_name='platform.ou.edu'):
			jobs2213 = User.get_user('jobs2213')
			jobs2299 = User.get_user('jobs2299')
			
			entry = self.catalog_entry()
			course = ICourseInstance(entry)		
			courses = {'26235.20131': course}
			mock_fic.is_callable().with_args().returns(courses)
		
			process(ims_xml)

			protected = course.SharingScopes[self._PROTECTED_SCOPE]
			public = course.SharingScopes[ES_PUBLIC]

			assert_that(jobs2213, is_in(protected))
			assert_that(jobs2213, is_in(public))

			# Instructor not in
			assert_that(jobs2299, is_not(is_in(protected)))
			assert_that(jobs2299, is_not(is_in(public)))
			instructor_enrollments = ICourseEnrollments(course).get_enrollment_for_principal(jobs2299)
			assert_that( instructor_enrollments, none())

			assert_that( ICourseEnrollments(course).get_enrollment_for_principal(jobs2213),
						 has_property('Scope', self._PROTECTED_SCOPE_NAME) )

			process(ims_un_xml)

			assert_that(jobs2213, is_not(is_in(protected)))

			# But he's still 'open-enrolled'
			assert_that(jobs2213, is_in(public))
			assert_that( ICourseEnrollments(course).get_enrollment_for_principal(jobs2213),
						 has_property('Scope', ES_PUBLIC) )
