#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope.event import notify

from zope import lifecycleevent

from nti.app.assessment.common import has_assigments_submitted

from nti.app.products.courseware.utils import drop_any_other_enrollments
from nti.app.products.courseware.utils import is_there_an_open_enrollment

from nti.contenttypes.courses.interfaces import ES_PUBLIC
from nti.contenttypes.courses.interfaces import ES_CREDIT_DEGREE

from nti.contenttypes.courses.interfaces import ICourseInstance
from nti.contenttypes.courses.interfaces import ICourseSubInstance
from nti.contenttypes.courses.interfaces import ICourseEnrollments
from nti.contenttypes.courses.interfaces import ICourseCatalogEntry
from nti.contenttypes.courses.interfaces import IDenyOpenEnrollment
from nti.contenttypes.courses.interfaces import ICourseEnrollmentManager
from nti.contenttypes.courses.interfaces import INonPublicCourseInstance

from nti.dataserver import users

from nti.externalization.interfaces import LocatedExternalDict

from nti.ims.feed.enterprise import Enterprise
from nti.ims.feed.interfaces import IEnterprise
from nti.ims.feed.interfaces import ACTIVE_STATUS
from nti.ims.feed.interfaces import INACTIVE_STATUS

from .interfaces import IIMSUserFinder
from .interfaces import IIMSCourseCatalog
from .interfaces import IMSUserCreatedEvent
from .interfaces import IIMSUserCreationExternaValues

def get_person_email(person):
	username = person.userid
	if person.email:
		result = person.email
	else:
		result = username + '@example.com'
		logger.warn('%s does not have an email. Defaulting to %s', username, result)

	result = result.lower()
	if result.endswith('@nextthought.com'):
		result = result[:-15] + 'example.com'
	return result

def find_user(person):
	finder = component.queryUtility(IIMSUserFinder)
	if finder is not None:
		result = finder.find(person)
	else:
		username = person.userid.lower()
		result = users.User.get_user(username)
	return result

def create_users(source):
	result = {}
	ims = source if IEnterprise.providedBy(source) \
		  else Enterprise.parseFile(source)

	for person in ims.get_persons():
		if person.sourcedid and person.sourcedid.id:
			sourcedid = userid = person.sourcedid.id.lower()
		else:
			sourcedid = userid = person.userid.lower()
		if userid.endswith('@nextthought.com'):
			userid = userid[:-16]

		user = find_user(person)
		email = get_person_email(person)
		user = users.User.get_user(userid) if user is None else user
		if user is None:
			args = {'username': userid}
			ext_value = {'email': email}
			if person.name:
				ext_value['realname'] = person.name
			args['external_value'] = ext_value
			
			external = component.queryUtility(IIMSUserCreationExternaValues)
			if external is not None:
				values = external.values(person)
				ext_value.update(values or {})
				
			user = users.User.create_user(**args)
			notify(IMSUserCreatedEvent(user, person))
			result[userid] = sourcedid
	return result

def find_ims_courses():
	catalog = component.queryUtility(IIMSCourseCatalog)
	result  = catalog.courses() if catalog is not None else {}
	return result

def _drop_enrollments(context, user):
	result = []
	dropped_courses = drop_any_other_enrollments(context, user)
	for course in dropped_courses:
		entry = ICourseCatalogEntry(course)
		if has_assigments_submitted(course, user):
			logger.warn("User %s has submitted to course '%s'", user, 
						entry.ProviderUniqueID)
		result.append(entry)
	return result

def update_member_enrollment_status(course_instance, person, role,
									enrrollment_info=None, move_info=None, 
									drop_info=None):
	userid = person.userid
	soonerID = person.sourcedid.id
	user = users.User.get_user(soonerID) or users.User.get_user(userid)
	if user is None:
		logger.warn("User (%s,%s) was not found", userid, soonerID)
		return

	move_info = {} if move_info is None else move_info
	drop_info = {} if drop_info is None else drop_info
	enrrollment_info = {} if enrrollment_info is None else enrrollment_info
	
	enrollments = ICourseEnrollments(course_instance)
	enrollment_manager = ICourseEnrollmentManager(course_instance)
	enrollment = enrollments.get_enrollment_for_principal(user)
	
	instance_entry = ICourseCatalogEntry(course_instance)

	if role.status == ACTIVE_STATUS:
		
		# check any other enrollment
		for entry in _drop_enrollments(course_instance, user):
			drop_info.setdefault(entry.ProviderUniqueID, {})
			drop_info[entry.ProviderUniqueID][userid] = soonerID
		
		add_mod = True
		# The user should be enrolled for degree-seeking credit.
		if enrollment is None:
			# Never before been enrolled
			logger.info('User %s enrolled in %s', user, instance_entry.ProviderUniqueID)
			enrollment_manager.enroll(user, scope=ES_CREDIT_DEGREE)
		elif enrollment.Scope != ES_CREDIT_DEGREE:
			logger.info('User %s upgraded to ForCredit in %s',
						user, instance_entry.ProviderUniqueID)
			enrollment.Scope = ES_CREDIT_DEGREE
			lifecycleevent.modified(enrollment)
		else:
			add_mod = False
			
		# record enrollment
		if add_mod:
			enrrollment_info.setdefault(instance_entry.ProviderUniqueID, {})
			enrrollment_info[instance_entry.ProviderUniqueID][userid] = soonerID
	elif role.status == INACTIVE_STATUS:
		# if enrolled but the course is not public then drop it
		if enrollment is not None:

			if INonPublicCourseInstance.providedBy(course_instance):
				logger.info('User %s dropping course %s',
							user, instance_entry.ProviderUniqueID)
				enrollment_manager.drop(user)
				
				# record drop
				drop_info.setdefault(instance_entry.ProviderUniqueID, {})
				drop_info[instance_entry.ProviderUniqueID][userid] = soonerID
				
			elif enrollment.Scope != ES_PUBLIC:
				logger.info('User %s moving to PUBLIC version of %s',
							user, instance_entry.ProviderUniqueID)
				# The user should not be enrolled for degree-seeking credit,
				# but if they were already enrolled they should remain
				# as publically enrolled
				enrollment.Scope = ES_PUBLIC
				lifecycleevent.modified(enrollment)
				
				# record move
				move_info.setdefault(instance_entry.ProviderUniqueID, {})
				move_info[instance_entry.ProviderUniqueID][userid] = soonerID

		# set in an open enrollment
		if 	enrollment is not None and enrollment.Scope != ES_PUBLIC and \
			not is_there_an_open_enrollment(course_instance, user):
			open_course = course_instance
			
			# if section and non public get main course
			if 	ICourseSubInstance.providedBy(course_instance) and \
				INonPublicCourseInstance.providedBy(course_instance):
				open_course = course_instance.__parent__.__parent__
				
			# do open enrollment
			if	not INonPublicCourseInstance.providedBy(open_course) and \
				not IDenyOpenEnrollment.providedBy(open_course):
				enrollments = ICourseEnrollments(open_course)
				enrollment = enrollments.get_enrollment_for_principal(user)
				if enrollment is None:
					enrollment_manager = ICourseEnrollmentManager(open_course)
					enrollment_manager.enroll(user, scope=ES_PUBLIC)
					
					# log public enrollment
					entry = ICourseCatalogEntry(open_course)
					logger.info('User %s enolled to PUBLIC version of %s',
								user, entry.ProviderUniqueID)
					
					# record
					enrrollment_info.setdefault(entry.ProviderUniqueID, {})
					enrrollment_info[entry.ProviderUniqueID][userid] = soonerID
	else:
		raise NotImplementedError("Unknown status", role.status)

def cmp_proxy(x, y):
	result = cmp((x.course_id, x.sourcedid), (y.course_id, y.sourcedid))
	if result == 0:
		x_sort_status = 0 if x.is_active else 1
		y_sort_status = 0 if y.is_active else 1
		result = cmp(x_sort_status, y_sort_status)
	return result

def process(ims_file, create_persons=False):

	# check for the old calling convention
	assert isinstance(create_persons, bool)
	ims = Enterprise.parseFile(ims_file)
	ims_courses = find_ims_courses()

	created_users = create_users(ims) if create_persons else ()

	warns = set()
	moves = LocatedExternalDict()
	drops = LocatedExternalDict()
	errollment = LocatedExternalDict()
	# sort members (drops come first)
	members = sorted(ims.get_all_members(), cmp=cmp_proxy)
	for member in members:
		person = ims.get_person(member.id)
		if person is None:
			logger.warn("Person definition for %s was not found", member.id)
			continue

		# Instructors should be auto-created.
		if member.is_instructor:
			continue

		course_id = member.course_id.id
		context = ims_courses.get(member.course_id.id)
		course_instance = ICourseInstance(context, None) 
		if course_instance is None:
			if course_id not in warns:
				warns.add(course_id)
				logger.warn("Course definition for %s was not found", course_id)
			continue

		update_member_enrollment_status(course_instance, person, member.role,
										errollment, moves, drops)

	result = LocatedExternalDict()
	result['Drops'] = drops
	result['Moves'] = moves
	result['Enrollment'] = errollment
	result['CreatedUsers'] = created_users
	return result
