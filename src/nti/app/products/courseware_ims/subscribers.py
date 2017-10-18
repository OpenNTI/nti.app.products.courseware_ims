#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface, component

from nti.app.products.courseware_ims.interfaces import ILTILaunchParamBuilder

from nti.appserver.policies.site_policies import guess_site_display_name

from nti.contenttypes.courses.interfaces import ICourseCatalog
from nti.contenttypes.courses.interfaces import ICourseInstance

from nti.dataserver.users import User

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
        params['resource_link_title'] = asset.ConfiguredTool.config.title
        params['resource_link_description'] = asset.ConfiguredTool.config.description


@interface.implementer(ILTILaunchParamBuilder)
class LTIUserParams(LTIParams):

    def build_params(self, params):
        user_obj = User.get_user(self.request.authenticated_userid)
        params['user_id'] = toExternalOID(user_obj)
        params['roles'] = [role.__name__ for role in user_obj.dynamic_memberships]
        # TODO find user attributes on user_obj for lis_person_* params


@interface.implementer(ILTILaunchParamBuilder)
class LTIInstanceParams(LTIParams):

    def build_params(self, params):
        params['tool_consumer_instance_guid'] = self.request.domain
        params['tool_consumer_instance_name'] = guess_site_display_name(self.request)
        params['tool_consumer_instance_url'] = self.request.host_url
        params['tool_consumer_info_product_family_code'] = "NextThought"


@interface.implementer(ILTILaunchParamBuilder)
class LTIContextParams(LTIParams):

    def build_params(self, params):
        course = ICourseInstance(self.context)
        catalog = component.getUtility(ICourseCatalog)
        catalog_entry = None
        for entry in catalog.iterCatalogEntries():
            if entry.__parent__ is course:
                catalog_entry = entry
                break
        params['context_type'] = "CourseSection"
        params['context_id'] = toExternalOID(course)
        if catalog_entry:
            params['context_title'] = catalog_entry.title
            params['context_label'] = catalog_entry.ProviderUniqueID


@interface.implementer(ILTILaunchParamBuilder)
class LTIPresentationParams(LTIParams):

    def build_params(self, params):
        params['launch_presentation_locale'] = self.request.locale_name
        params['launch_presentation_document_target'] = "window"
        params['launch_presentation_return_url'] = self.request.current_route_url()
