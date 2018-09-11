#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from six.moves.urllib.parse import urljoin

from zope import interface, component

from nti.app.authentication import get_remote_user

from nti.app.products.courseware_ims import _create_link

from nti.app.products.courseware_ims.interfaces import IExternalToolAsset
from nti.app.products.courseware_ims.interfaces import ILTILaunchParamBuilder

from nti.app.products.ims import SUPPORTED_LTI_EXTENSIONS
from nti.app.products.ims.interfaces import ILTIRequest

from nti.appserver.policies.site_policies import guess_site_display_name

from nti.common.nameparser import human_name

from nti.contenttypes.courses.interfaces import ICourseCatalogEntry
from nti.contenttypes.courses.interfaces import ICourseInstance

from nti.contenttypes.courses.utils import is_course_instructor

from nti.dataserver.authorization import is_admin_or_site_admin
from nti.dataserver.authorization import is_content_admin

from nti.dataserver.users.interfaces import IFriendlyNamed

from nti.externalization.oids import toExternalOID

from nti.ims.lti.interfaces import IConfiguredTool
from nti.ims.lti.interfaces import IDeepLinking
from nti.ims.lti.interfaces import IExternalToolLinkSelection

from nti.mailer.interfaces import IEmailAddressable

from nti.traversal.traversal import find_interface

NTI = u"NextThought"
NTI_EMAIL = u"support@nextthought.com"
NTI_CONTEXT_TYPE = u"CourseSection"

logger = __import__('logging').getLogger(__name__)


class LTIParams(object):

    def __init__(self, request, context):
        self.request = request
        self.context = context


@component.adapter(ILTIRequest, interface.Interface)
@interface.implementer(ILTILaunchParamBuilder)
class LTIUserParams(LTIParams):

    def build_params(self, params):
        user_obj = get_remote_user(request=self.request)
        params['user_id'] = toExternalOID(user_obj)

        named_user = IFriendlyNamed(user_obj)
        if named_user.realname:
            name = human_name(named_user.realname)
            params['lis_person_name_full'] = name.full_name
            if name.first:
                params['lis_person_name_given'] = name.first
            if name.last:
                params['lis_person_name_family'] = name.last

        user_email = IEmailAddressable(user_obj)
        params['lis_person_contact_email_primary'] = user_email.email


@component.adapter(ILTIRequest, interface.Interface)
@interface.implementer(ILTILaunchParamBuilder)
class LTIRoleParams(LTIParams):

    def build_params(self, params):
        user_obj = get_remote_user(request=self.request)
        course = find_interface(self.context, ICourseInstance)
        ext_roles = [u'urn:lti:sysrole:ims/lis/User']
        roles = []
        if is_admin_or_site_admin(user_obj):
            roles.append(u'Administrator')
            ext_roles += [u'urn:lti:sysrole:ims/lis/Administrator',
                          u'urn:lti:instrole:ims/lis/Administrator',
                          u'urn:lti:role:ims/lis/Administrator']
        if is_course_instructor(course, user_obj):
            roles.append(u'Instructor')
            ext_roles += [u'urn:lti:instrole:ims/lis/Instructor',
                          u'urn:lti:role:ims/lis/Instructor']
        else:
            params['roles'] = u'Learner'
        if is_content_admin(user_obj):
            roles.append(u'ContentDeveloper')
            ext_roles += [u'urn:lti:role:ims/lis/ContentDeveloper']

        params['roles'] = u''.join(roles)
        params['ext_roles'] = u''.join(ext_roles)


@component.adapter(ILTIRequest, interface.Interface)
@interface.implementer(ILTILaunchParamBuilder)
class LTIInstanceParams(LTIParams):

    def build_params(self, params):
        params['tool_consumer_instance_guid'] = self.request.domain
        params['tool_consumer_instance_name'] = guess_site_display_name(self.request)
        params['tool_consumer_instance_url'] = self.request.host_url
        params['tool_consumer_info_product_family_code'] = NTI
        params['tool_consumer_instance_contact_email'] = NTI_EMAIL


@component.adapter(ILTIRequest, interface.Interface)
@interface.implementer(ILTILaunchParamBuilder)
class LTIContextParams(LTIParams):

    def build_params(self, params):
        course = find_interface(self.context, ICourseInstance)
        catalog_entry = ICourseCatalogEntry(course)
        params['context_type'] = NTI_CONTEXT_TYPE
        params['context_id'] = toExternalOID(course)
        params['context_title'] = catalog_entry.title
        params['context_label'] = catalog_entry.ProviderUniqueID


@component.adapter(ILTIRequest, interface.Interface)
@interface.implementer(ILTILaunchParamBuilder)
class LTIPresentationParams(LTIParams):

    def build_params(self, params):
        params['launch_presentation_locale'] = self.request.locale_name
        params['launch_presentation_return_url'] = self.request.current_route_url()
        params['launch_presentation_document_target'] = self.request.params.get('target', 'iframe')
        params['launch_presentation_width'] = self.request.params.get('width')
        params['launch_presentation_height'] = self.request.params.get('height')


@component.adapter(ILTIRequest, IExternalToolAsset)
@interface.implementer(ILTILaunchParamBuilder)
class LTIResourceParams(LTIParams):

    def build_params(self, params):
        asset = self.context
        asset_oid = toExternalOID(asset)
        params['resource_link_id'] = asset_oid
        params['resource_link_title'] = asset.title
        params['resource_link_description'] = asset.description


@component.adapter(ILTIRequest, IExternalToolLinkSelection)
@interface.implementer(ILTILaunchParamBuilder)
class LTIExternalToolLinkSelectionParams(LTIParams):

    def build_params(self, params):
        link = _create_link(self.context,
                            method='GET',
                            elements=('@@external_tool_link_selection_response',))
        response_url = urljoin(self.request.application_url,
                               link)
        params['launch_presentation_return_url'] = response_url

        # ext_content_* params are part of the edu apps lti specification
        # https://www.eduappcenter.com/docs/extensions/content
        params['ext_content_return_types'] = 'lti_launch_url'
        params['ext_content_return_url'] = response_url
        params['ext_content_intended_use'] = 'embed'
        params['selection_directive'] = 'select_link'


@component.adapter(ILTIRequest, IDeepLinking)
@interface.implementer(ILTILaunchParamBuilder)
class LTIDeepLinkingParams(LTIParams):

    def build_params(self, params):
        link = _create_link(self.context,
                            method='GET',
                            elements=('@@deep_linking_response',))
        response_url = urljoin(self.request.application_url,
                               link)
        params['content_item_return_url'] = response_url
        params['accept_presentation_document_targets'] = 'frame,iframe'
        # XXX: There are various other types we could potentially support here
        params['accept_media_types'] = 'application/vnd.ims.lti.v1.ltilink'
        params['lti_message_type'] = 'ContentItemSelectionRequest'
        params['accept_multiple'] = 'false'
        params['accept_unsigned'] = 'true'
        params['auto_create'] = 'false'
