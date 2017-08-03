#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division

from nti.ims.lti.interfaces import IConfiguredTool
from zope.formlib import form
from zope.publisher.browser import TestRequest

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import six

from requests.structures import CaseInsensitiveDict

from zope import component

from zope.security.management import endInteraction
from zope.security.management import restoreInteraction

from pyramid import httpexceptions as hexc

from pyramid.view import view_config
from pyramid.view import view_defaults

from nti.app.base.abstract_views import get_all_sources
from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.error import raise_json_error

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.products.courseware_ims.workflow import process
from nti.app.products.courseware_ims.workflow import create_users
from nti.app.products.courseware_ims.workflow import find_ims_courses

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.app.products.ims.views import ConfiguredToolCreateView
from nti.app.products.ims.views import ConfiguredToolDeleteView
from nti.app.products.ims.views import ConfiguredToolEditView
from nti.app.products.ims.views import ConfiguredToolsGetView
from nti.app.products.ims.views import IMSPathAdapter

from nti.common.string import is_true

from nti.contenttypes.courses.interfaces import ICourseCatalog
from nti.contenttypes.courses.interfaces import ICourseInstance
from nti.contenttypes.courses.interfaces import ICourseCatalogEntry

from nti.contenttypes.courses.utils import get_course_vendor_info

from nti.dataserver import authorization as nauth

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

from nti.externalization.oids import to_external_ntiid_oid

ITEMS = StandardExternalFields.ITEMS
NTIID = StandardExternalFields.NTIID
TOTAL = StandardExternalFields.TOTAL
ITEM_COUNT = StandardExternalFields.ITEM_COUNT


def get_source(values, request):
    sources = get_all_sources(request)
    if sources:
        ims_file = next(iter(sources.values()))
        ims_file.seek(0)
    else:
        ims_file = values.get('ims_file') or values.get('ims')
        if isinstance(ims_file, six.string_types):
            ims_file = os.path.expanduser(ims_file)
            if not os.path.exists(ims_file):
                message = u'%s file not found.' % ims_file
                raise_json_error(request,
                                 hexc.HTTPUnprocessableEntity,
                                 {
                                     'message': message
                                 },
                                 None)
    if not ims_file:
        message = u'No feed source provided.'
        raise_json_error(request,
                         hexc.HTTPUnprocessableEntity,
                         {
                             'message': message
                         },
                         None)
    return ims_file


@view_config(name='enrollment')
@view_config(name='nti_enrollment')
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               context=IMSPathAdapter,
               permission=nauth.ACT_NTI_ADMIN)
class IMSEnrollmentView(AbstractAuthenticatedView,
                        ModeledContentUploadRequestUtilsMixin):

    def readInput(self, value=None):
        if self.request.body:
            values = super(IMSEnrollmentView, self).readInput(value)
        else:
            values = self.request.params
        values = CaseInsensitiveDict(values)
        return values

    def __call__(self):
        values = self.readInput()
        ims_file = get_source(values, self.request)
        # parse options
        create_persons = values.get('create_users') \
                      or values.get('create_persons')
        create_persons = is_true(create_persons)
        send_email = values.get('email') \
                  or values.get('sendEmail') \
                  or values.get('send_email')
        send_email = is_true(send_email)
        drop_missing = is_true(values.get('drop_missing'))
        if not send_email:
            endInteraction()
        try:
            result = process(ims_file, create_persons, drop_missing)
        finally:
            if not send_email:
                restoreInteraction()
        return result


@view_config(name='create_users')
@view_config(name='nti_create_users')
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               context=IMSPathAdapter,
               permission=nauth.ACT_NTI_ADMIN)
class IMSCreateUsersView(AbstractAuthenticatedView,
                         ModeledContentUploadRequestUtilsMixin):

    def readInput(self, value=None):
        if self.request.body:
            values = super(IMSCreateUsersView, self).readInput(value)
        else:
            values = self.request.params
        values = CaseInsensitiveDict(values)
        return values

    def __call__(self):
        values = self.readInput()
        ims_file = get_source(values, self.request)
        endInteraction()
        try:
            created = create_users(ims_file)
        finally:
            restoreInteraction()
        result = LocatedExternalDict()
        result[ITEMS] = created
        result[TOTAL] = result[ITEM_COUNT] = len(created)
        return result


@view_config(name='courses')
@view_config(name='nti_courses')
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               context=IMSPathAdapter,
               permission=nauth.ACT_NTI_ADMIN)
class IMSCoursesView(AbstractAuthenticatedView):

    def _get_entry_key(self, entry):
        parents = []
        o = entry.__parent__
        while o is not None and not ICourseCatalog.providedBy(o):
            parents.append(o.__name__)
            o = getattr(o, '__parent__', None)
        parents.reverse()
        if None in parents:
            result = entry.ProviderUniqueID
        else:
            result = '/'.join(parents)
            if not result:
                result = entry.ProviderUniqueID
        return result

    def _get_entries(self, courses=()):
        entries = {}
        for context in courses or ():
            course_instance = ICourseInstance(context)
            course_entry = ICourseCatalogEntry(context)
            info = get_course_vendor_info(course_instance, False) or {}
            entry = entries[self._get_entry_key(course_entry)] = {
                'VendorInfo': info
            }
            entry['NTIIDs'] = {
                'CourseCatalogEntry': course_entry.ntiid,
                'CourseInstance': to_external_ntiid_oid(course_instance)
            }
            bundle = getattr(course_instance, 'ContentPackageBundle', None)
            if bundle is not None:
                bundle_info = entry['ContentPackageBundle'] = {}
                bundle_info[NTIID] = getattr(bundle, 'ntiid', None)
                bundle_info['ContentPackages'] = [
                    x.ntiid for x in bundle.ContentPackages or ()
                ]
        return entries

    def __call__(self):
        request = self.request
        params = CaseInsensitiveDict(request.params)
        all_courses = is_true(params.get('all'))
        result = LocatedExternalDict()
        if not all_courses:
            course_map = find_ims_courses()
            entries = self._get_entries(course_map.values())
        else:
            catalog = component.getUtility(ICourseCatalog)
            entries = self._get_entries(catalog.iterCatalogEntries())
        result[ITEMS] = entries
        result[TOTAL] = result[ITEM_COUNT] = len(entries)
        return result


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             request_method='POST',
             context=ICourseInstance,
             name='create_lti_tool',
             permission=nauth.ROLE_CONTENT_ADMIN)
class CourseConfiguredToolCreateView(ConfiguredToolCreateView):

    def get_tools(self):
        tools = ICourseConfiguredToolContainer(self.context)
        return tools


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             request_method='PUT',
             context=ICourseInstance,
             name='edit_lti_tool',
             permission=nauth.ROLE_CONTENT_ADMIN)
class CourseConfiguredToolEditView(ConfiguredToolEditView):

    def get_tools(self):
        tools = ICourseConfiguredToolContainer(self.context)
        return tools


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             request_method='POST',
             context=ICourseInstance,
             permission=nauth.ROLE_CONTENT_ADMIN)
class CourseConfiguredToolDeleteView(ConfiguredToolDeleteView):

    def get_tools(self):
        tools = ICourseConfiguredToolContainer(self.context)
        return tools
