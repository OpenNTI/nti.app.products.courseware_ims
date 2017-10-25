#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division


__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.app.authentication import get_remote_user

from nti.app.products.courseware_ims.interfaces import ILTILaunchParamBuilder

from nti.appserver.policies.site_policies import guess_site_display_name

from nti.common.nameparser import human_name

from nti.contenttypes.courses.interfaces import ICourseCatalogEntry
from nti.contenttypes.courses.interfaces import ICourseInstance

from nti.dataserver.users.interfaces import ICompleteUserProfile

from nti.externalization.oids import toExternalOID


class LTIParams(object):

    def __init__(self, request, context):
        self.request = request
        self.context = context


@interface.implementer(ILTILaunchParamBuilder)
class LTIResourceParams(LTIParams):

    def build_params(self, params):
        asset = self.context
        asset_oid = toExternalOID(asset)
        params['resource_link_id'] = asset_oid
        params['resource_link_title'] = asset.title
        params['resource_link_description'] = asset.description


@interface.implementer(ILTILaunchParamBuilder)
class LTIUserParams(LTIParams):

    def build_params(self, params):
        user_obj = get_remote_user(request=self.request)
        params['user_id'] = toExternalOID(user_obj)
        user_obj = ICompleteUserProfile(user_obj)
        if user_obj.realname:
            name = human_name(user_obj.realname)
            params['lis_person_name_full'] = name.full_name
            if name.first:
                params['lis_person_name_given'] = name.first
            if name.last:
                params['lis_person_name_family'] = name.last
        params['lis_person_contact_email_primary'] = user_obj.email


@interface.implementer(ILTILaunchParamBuilder)
class LTIRoleParams(LTIParams):

    def build_params(self, params):
        user_obj = get_remote_user(request=self.request)
        profile = ICompleteUserProfile(user_obj)
        params['roles'] = [profile.role]  # TODO needs mapped to lis vocabulary


@interface.implementer(ILTILaunchParamBuilder)
class LTIInstanceParams(LTIParams):

    def build_params(self, params):
        params['tool_consumer_instance_guid'] = self.request.domain
        params['tool_consumer_instance_name'] = guess_site_display_name(self.request)
        params['tool_consumer_instance_url'] = self.request.host_url
        params['tool_consumer_info_product_family_code'] = "NextThought"
        params['tool_consumer_instance_contact_email'] = "support@nextthought.com"


@interface.implementer(ILTILaunchParamBuilder)
class LTIContextParams(LTIParams):

    def build_params(self, params):
        course = ICourseInstance(self.context)
        catalog_entry = ICourseCatalogEntry(course)
        params['context_type'] = "CourseSection"
        params['context_id'] = toExternalOID(course)
        params['context_title'] = catalog_entry.title
        params['context_label'] = catalog_entry.ProviderUniqueID


@interface.implementer(ILTILaunchParamBuilder)
class LTIPresentationParams(LTIParams):

    def build_params(self, params):
        params['launch_presentation_locale'] = self.request.locale_name
        params['launch_presentation_document_target'] = "window"
        params['launch_presentation_return_url'] = self.request.current_route_url()
