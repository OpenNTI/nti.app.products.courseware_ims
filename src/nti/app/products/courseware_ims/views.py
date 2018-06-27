#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import six

from datetime import datetime

from requests.structures import CaseInsensitiveDict

from zope import component
from zope import interface

from zope.component import subscribers

from zope.event import notify

from zope.security.management import endInteraction
from zope.security.management import restoreInteraction

from lti import LaunchParams
from lti import ToolConsumer

from pyramid import httpexceptions as hexc

from pyramid.view import view_config
from pyramid.view import view_defaults

from nti.app.base.abstract_views import get_all_sources
from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.contenttypes.presentation.views.asset_views import CourseOverviewGroupInsertView

from nti.app.externalization.error import raise_json_error

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.app.products.courseware_ims import _create_link

from nti.app.products.courseware_ims.lti import LTIExternalToolAsset

from nti.app.products.courseware_ims.interfaces import LTILaunchEvent
from nti.app.products.courseware_ims.interfaces import ILTIAssetMetadata
from nti.app.products.courseware_ims.interfaces import IExternalToolAsset
from nti.app.products.courseware_ims.interfaces import ILTILaunchParamBuilder
from nti.app.products.courseware_ims.interfaces import IExternalToolLinkSelectionResponse

from nti.app.products.courseware_ims.workflow import process
from nti.app.products.courseware_ims.workflow import create_users
from nti.app.products.courseware_ims.workflow import find_ims_courses

from nti.app.products.ims.interfaces import ILTIRequest

from nti.app.products.ims.views import IMSPathAdapter

from nti.common.string import is_true

from nti.contenttypes.courses.interfaces import ICourseCatalog
from nti.contenttypes.courses.interfaces import ICourseInstance
from nti.contenttypes.courses.interfaces import ICourseCatalogEntry

from nti.contenttypes.courses.utils import get_course_vendor_info

from nti.contenttypes.presentation.interfaces import INTICourseOverviewGroup

from nti.dataserver import authorization as nauth

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

from nti.ims.lti.interfaces import IConfiguredTool

from nti.ntiids.oids import to_external_ntiid_oid

from nti.traversal.traversal import find_interface

ITEMS = StandardExternalFields.ITEMS
NTIID = StandardExternalFields.NTIID
TOTAL = StandardExternalFields.TOTAL
ITEM_COUNT = StandardExternalFields.ITEM_COUNT

logger = __import__('logging').getLogger(__name__)


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
             renderer='templates/create_external_tool.pt',
             name='create_external_tool',
             request_method='GET',
             context=INTICourseOverviewGroup,
             permission=nauth.ACT_CREATE)
class CreateExternalToolAssetView(AbstractAuthenticatedView):

    def __call__(self):
        course = ICourseInstance(self.context)
        tools_link = _create_link(course,
                                  method="GET",
                                  elements=("lti_configured_tools",))
        post_link = _create_link(self.context,
                                 method="POST",
                                 elements=("contents",))

        return {'tool_url': tools_link,
                'MimeType': LTIExternalToolAsset.mimeType,
                'post_url': post_link}


@view_defaults(route_name='objects.generic.traversal',
               renderer='templates/launch_external_tool.pt',
               request_method='GET')
class ExternalToolAssetView(AbstractAuthenticatedView):

    @view_config(context=IExternalToolAsset,
                 name='launch',
                 permission=nauth.ACT_READ)
    def launch(self):
        metadata = ILTIAssetMetadata(self.context)
        course = find_interface(self.context, ICourseInstance)
        event = LTILaunchEvent(self.remoteUser,
                               course,
                               metadata,
                               datetime.utcnow())
        notify(event)
        return self._do_request(self.context.ConfiguredTool, self.context.launch_url)

    @view_config(context=IConfiguredTool,
                 name='external_tool_link_selection',
                 permission=nauth.ACT_CONTENT_EDIT)
    def external_tool_link_selection(self):
        overview_group = self.request.params['overview_group']
        return self._do_request(self.context, self.context.launch_url, overview_group=overview_group)

    @view_config(context=IConfiguredTool,
                 name='deep_linking',
                 permission=nauth.ACT_CONTENT_EDIT)
    def deep_linking(self):
        return self._do_request(self.context, self.context.launch_url)

    def _do_request(self, tool=None, launch_url=None, **kwargs):
        interface.alsoProvides(self.request, ILTIRequest)
        launch_params = LaunchParams(lti_version='LTI-1p0')
        # Add instance specific launch params
        for subscriber in subscribers((self.request, self.context), ILTILaunchParamBuilder):
            subscriber.build_params(launch_params, **kwargs)

        tool_consumer = ToolConsumer(tool.consumer_key,
                                     tool.secret,
                                     params=launch_params,
                                     launch_url=launch_url)

        tool_consumer.set_config(tool.config)

        # Auto launch is always set to true, but is there for future development if needed
        return {'consumer': tool_consumer,
                'auto_launch': 1}


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             request_method='GET',
             context=INTICourseOverviewGroup,
             name='external_tool_link_selection_response',
             permission=nauth.ACT_CONTENT_EDIT)
class ExternalToolLinkSelectionResponseView(CourseOverviewGroupInsertView):

    def readInput(self, value=None):
        return_type = self.request.params['return_type']
        # In the cases where the return type is undefined we default to an lti_launch
        result = component.queryAdapter(self.request, IExternalToolLinkSelectionResponse, return_type)
        return result

    def _do_call(self):
        self.request.environ['nti.request_had_transaction_side_effects'] = True
        return super(ExternalToolLinkSelectionResponseView, self)._do_call()
