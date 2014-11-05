#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import six

from zope import component
from zope.security.management import endInteraction
from zope.security.management import restoreInteraction

from pyramid.view import view_config
from pyramid import httpexceptions as hexc

from nti.app.base.abstract_views import AbstractAuthenticatedView
from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.products.ims.views import IMSPathAdapter

from nti.contenttypes.courses.interfaces import ICourseCatalog
from nti.contenttypes.courses.interfaces import ICourseInstance
from nti.contenttypes.courses.interfaces import ICourseCatalogEntry
from nti.contenttypes.courses.interfaces import ICourseInstanceVendorInfo

from nti.dataserver import authorization as nauth

from nti.externalization.interfaces import LocatedExternalDict

from nti.utils.maps import CaseInsensitiveDict

from .workflow import process
from .workflow import create_users
from .workflow import find_ims_courses

def is_true(t):
	result = bool(t and str(t).lower() in ('1', 'y', 'yes', 't', 'true'))
	return result

def get_source(values, keys, name):
	# check map
	source = None
	for key in keys:
		source = values.get(key)
		if source is not None:
			break
	# validate
	if isinstance(source, six.string_types):
		source = os.path.expanduser(source)
		if not os.path.exists(source):
			raise hexc.HTTPUnprocessableEntity(detail='%s file not found' % name)
	elif source is not None:
		source = source.file
		source.seek(0)
	else:
		raise hexc.HTTPUnprocessableEntity(detail='No %s source provided' % name)
	return source

@view_config(route_name='objects.generic.traversal',
			 renderer='rest',
			 name='enrollment',
			 permission=nauth.ACT_MODERATE,
			 context=IMSPathAdapter)
class IMSEnrollmentView(AbstractAuthenticatedView, 
						ModeledContentUploadRequestUtilsMixin):
	
	def __call__(self):
		request = self.request
		if request.POST:
			values = CaseInsensitiveDict(request.POST)
		else:
			values = self.readInput()
			values = CaseInsensitiveDict(values)
		ims_file = get_source(values, ('ims_file', 'ims'), 'IMS')
		create_persons = values.get('create_users') or values.get('create_persons')
		create_persons = is_true(create_persons)
	
		# Make sure we don't send enrollment email, etc, during this process
		# by not having any interaction.
		# This is somewhat difficult to test the side-effects of, sadly.
		endInteraction()
		try:
			result = process(ims_file, create_persons)
		finally:
			restoreInteraction()
		return result

@view_config(route_name='objects.generic.traversal',
			 renderer='rest',
			 name='create_users',
			 permission=nauth.ACT_MODERATE,
			 context=IMSPathAdapter)
class IMSCreateUsersView(AbstractAuthenticatedView,
						 ModeledContentUploadRequestUtilsMixin):

	def __call__(self):
		request = self.request
		if request.POST:
			values = CaseInsensitiveDict(request.POST)
		else:
			values = self.readInput()
			values = CaseInsensitiveDict(values)
		ims_file = get_source(values, ('ims_file', 'ims'), 'IMS')
		endInteraction()
		try:
			created = create_users(ims_file)
		finally:
			restoreInteraction()
		
		result = LocatedExternalDict()
		result['Items'] = created
		result['Total'] = len(created)
		return result

@view_config(route_name='objects.generic.traversal',
			 renderer='rest',
			 name='courses',
			 permission=nauth.ACT_MODERATE,
			 context=IMSPathAdapter)
class IMSCoursesView(AbstractAuthenticatedView):

	def _get_entries(self, courses=()):
		entries = {}
		for context in courses or ():
			course_instance = ICourseInstance(context)
			course_entry = ICourseCatalogEntry(context)
			vendor_info = ICourseInstanceVendorInfo(course_instance, {})
			entry = entries[course_entry.ProviderUniqueID] = {'VendorInfo': vendor_info}
			bundle = getattr(course_instance, 'ContentPackageBundle', None)
			entry['ContentPackageBundle'] = getattr(bundle, 'ntiid', None)
			entry['CatalogEntryNTIID'] = getattr(course_entry, 'ntiid', None)
		return entries
	
	def __call__(self):
		request = self.request
		params = CaseInsensitiveDict(request.params)
		all_courses= params.get('all') or params.get('allCourses') or params.get('all_courses')
		all_courses = is_true(all_courses)
	
		result = LocatedExternalDict()
		if not all_courses:
			course_map = find_ims_courses()
			entries = self._get_entries(course_map.values())
		else:
			catalog = component.getUtility(ICourseCatalog)
			entries = self._get_entries(catalog.iterCatalogEntries())
		
		result['Items'] = entries
		result['Total'] = len(entries)
		return result
