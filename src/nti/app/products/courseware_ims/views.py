#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import six

from requests.structures import CaseInsensitiveDict

from zope import component

from zope.security.management import endInteraction
from zope.security.management import restoreInteraction

from pyramid import httpexceptions as hexc

from pyramid.threadlocal import get_current_request

from pyramid.view import view_config
from pyramid.view import view_defaults

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.error import raise_json_error

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.products.courseware_ims.workflow import process
from nti.app.products.courseware_ims.workflow import create_users
from nti.app.products.courseware_ims.workflow import find_ims_courses

from nti.app.products.ims.views import IMSPathAdapter

from nti.common.string import is_true

from nti.contenttypes.courses.interfaces import ICourseCatalog
from nti.contenttypes.courses.interfaces import ICourseInstance
from nti.contenttypes.courses.interfaces import ICourseCatalogEntry

from nti.contenttypes.courses.utils import get_course_vendor_info

from nti.dataserver import authorization as nauth

from nti.externalization.oids import to_external_ntiid_oid
from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

ITEMS = StandardExternalFields.ITEMS
NTIID = StandardExternalFields.NTIID
TOTAL = StandardExternalFields.TOTAL
ITEM_COUNT = StandardExternalFields.ITEM_COUNT


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
            message = '%s file not found.' % name
            raise_json_error(get_current_request(),
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': message
                             },
                             None)
    elif source is not None:
        source = source.file
        source.seek(0)
    else:
        message = 'No %s source provided.' % name
        raise_json_error(get_current_request(),
                         hexc.HTTPUnprocessableEntity,
                         {
                             'message': message
                         },
                         None)
    return source


@view_config(name='enrollment')
@view_config(name='nti_enrollment')
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               name='nti_enrollment',
               context=IMSPathAdapter,
               permission=nauth.ACT_NTI_ADMIN)
class IMSEnrollmentView(AbstractAuthenticatedView,
                        ModeledContentUploadRequestUtilsMixin):

    def readInput(self, value=None):
        request = self.request
        if request.POST:
            values = CaseInsensitiveDict(request.POST)
        else:
            values = super(IMSEnrollmentView, self).readInput(value=value)
            values = CaseInsensitiveDict(values)
        return values

    def __call__(self):
        values = self.readInput()
        ims_file = get_source(values, ('ims_file', 'ims'), 'IMS')
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
