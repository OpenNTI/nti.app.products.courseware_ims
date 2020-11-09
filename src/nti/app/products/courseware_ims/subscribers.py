#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from pyramid.threadlocal import get_current_request

from six.moves.urllib.parse import urljoin

from zc.displayname.interfaces import IDisplayNameGenerator

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

from zope.component.hooks import getSite

from zope.lifecycleevent.interfaces import IObjectAddedEvent

from nti.app.authentication import get_remote_user

from nti.app.products.courseware_ims import _create_link
from nti.app.products.courseware_ims import raise_error

from nti.app.products.courseware_ims.interfaces import IExternalToolAsset
from nti.app.products.courseware_ims.interfaces import ILTILaunchParamBuilder
from nti.app.products.courseware_ims.interfaces import ILTIOutcomesResultSourcedIDUtility

from nti.app.products.courseware_ims.license_utils import can_add_lti_asset

from nti.app.products.ims import LTI
from nti.app.products.ims import VIEW_LTI_OUTCOMES

from nti.common.nameparser import human_name

from nti.contenttypes.courses.interfaces import ICourseInstance
from nti.contenttypes.courses.interfaces import ICourseCatalogEntry
from nti.contenttypes.courses.interfaces import ICourseContentLibraryProvider

from nti.contenttypes.courses.utils import is_course_instructor

from nti.coremetadata.interfaces import IUser

from nti.dataserver.authorization import is_content_admin
from nti.dataserver.authorization import is_admin_or_site_admin

from nti.dataserver.interfaces import IDataserver
from nti.dataserver.interfaces import ILinkExternalHrefOnly

from nti.dataserver.users.interfaces import IFriendlyNamed

from nti.externalization.oids import toExternalOID

from nti.ims.lti.consumer import ConfiguredTool

from nti.ims.lti.interfaces import IConfiguredTool

from nti.links.externalization import render_link

from nti.links.links import Link

from nti.mailer.interfaces import IEmailAddressable

from nti.traversal.traversal import find_interface

NTI = u"NextThought"
NTI_EMAIL = u"support@nextthought.com"
NTI_CONTEXT_TYPE = u"CourseSection"

logger = __import__('logging').getLogger(__name__)


def url_for_outcomes_postback(request=None):
    if request is None:
        request = get_current_request()
    ds_folder = component.getUtility(IDataserver).dataserver_folder
    link = Link(ds_folder,
                elements=(LTI,
                          '@@' + VIEW_LTI_OUTCOMES,))
    interface.alsoProvides(link, ILinkExternalHrefOnly)
    url = render_link(link)
    return request.relative_url(url)


def build_lti_result_sourcedid(user, course, asset):
    """
    Build a result sourcedid of the intids of the `<user>:<course>:<asset>`.
    """


class LTIParams(object):

    def __init__(self, request, context):
        self.request = request
        self.context = context


class LTIUserMixin(object):

    def _get_remote_user(self):
        try:
            return self._user
        except AttributeError:  # Expected behavior if not in a test
            return get_remote_user(request=self.request)


@interface.implementer(ILTILaunchParamBuilder)
class LTIResourceParams(LTIParams):

    def build_params(self, params, **unused_kwargs):
        asset = self.context
        asset_oid = toExternalOID(asset)
        params['resource_link_id'] = asset_oid
        params['resource_link_title'] = asset.title
        params['resource_link_description'] = asset.description


@interface.implementer(ILTILaunchParamBuilder)
class LTIOutcomesParams(LTIParams, LTIUserMixin):

    def build_params(self, params, **unused_kwargs):
        asset = self.context
        outcomes_url = url_for_outcomes_postback(self.request)
        params['lis_outcome_service_url'] = outcomes_url
        user = self._get_remote_user()
        course = find_interface(self.context, ICourseInstance)
        outcomes_utility = component.getUtility(ILTIOutcomesResultSourcedIDUtility)
        result_sourcedid = outcomes_utility.build_sourcedid(user, course, asset)
        params['lis_result_sourcedid'] = result_sourcedid


@interface.implementer(ILTILaunchParamBuilder)
class LTIUserParams(LTIParams, LTIUserMixin):

    def build_params(self, params, **unused_kwargs):
        user_obj = self._get_remote_user()
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


@interface.implementer(ILTILaunchParamBuilder)
class LTIRoleParams(LTIParams, LTIUserMixin):

    def build_params(self, params, **unused_kwargs):
        user_obj = self._get_remote_user()
        course = find_interface(self.context, ICourseInstance)
        if is_admin_or_site_admin(user_obj):
            params['roles'] = u'Administrator'
        elif is_course_instructor(course, user_obj):
            params['roles'] = u'Instructor'
        elif is_content_admin(user_obj):
            params['roles'] = u'ContentDeveloper'
        else:
            params['roles'] = u'Learner'


@interface.implementer(ILTILaunchParamBuilder)
class LTIInstanceParams(LTIParams):

    @Lazy
    def _brand_name(self):
        return component.getMultiAdapter((getSite(), self.request),
                                         IDisplayNameGenerator)()

    def build_params(self, params, **unused_kwargs):
        params['tool_consumer_instance_guid'] = self.request.domain
        params['tool_consumer_instance_name'] = self._brand_name
        params['tool_consumer_instance_url'] = self.request.host_url
        params['tool_consumer_info_product_family_code'] = NTI
        params['tool_consumer_instance_contact_email'] = NTI_EMAIL


@interface.implementer(ILTILaunchParamBuilder)
class LTIContextParams(LTIParams):

    def build_params(self, params, **unused_kwargs):
        course = ICourseInstance(self.context)
        catalog_entry = ICourseCatalogEntry(course)
        params['context_type'] = NTI_CONTEXT_TYPE
        params['context_id'] = toExternalOID(course)
        params['context_title'] = catalog_entry.title
        params['context_label'] = catalog_entry.ProviderUniqueID


@interface.implementer(ILTILaunchParamBuilder)
class LTIPresentationParams(LTIParams):

    def build_params(self, params, **unused_kwargs):
        params['launch_presentation_locale'] = self.request.locale_name
        params['launch_presentation_return_url'] = self.request.current_route_url()
        # Get the tool if we are an asset, otherwise the context is tool
        tool = IConfiguredTool(self.context)
        params['launch_presentation_document_target'] = self.request.params.get('target', 'iframe')
        params['launch_presentation_width'] = tool.selection_width if tool.selection_width is not None else self.request.params.get('width')
        params['launch_presentation_height'] = tool.selection_height if tool.selection_height is not None else self.request.params.get('height')


@interface.implementer(ILTILaunchParamBuilder)
class LTIExternalToolLinkSelectionParams(LTIParams):

    def build_params(self, params, **unused_kwargs):
        link = _create_link(self.context,
                            method='GET',
                            elements=(('@@external_tool_link_selection_response',)))
        response_url = urljoin(self.request.application_url,
                               link)
        params['launch_presentation_return_url'] = response_url

        # ext_content_* params are part of the edu apps lti specification
        # https://www.eduappcenter.com/docs/extensions/content
        params['ext_content_return_types'] = 'lti_launch_url'
        params['ext_content_return_url'] = response_url
        params['ext_content_intended_use'] = 'embed'
        params['selection_directive'] = 'select_link'


@component.adapter(IUser, ICourseInstance)
@interface.implementer(ICourseContentLibraryProvider)
class _CourseContentLibraryProvider(object):
    """
    Return the mimetypes of objects of course content that could be
    added to this course by this user.
    """

    def __init__(self, user, course):
        self.user = user
        self.course = course

    def get_item_mime_types(self):
        """
        Returns the collection of mimetypes that may be available (either
        they exist or can exist) in this course.
        """
        result = []
        if can_add_lti_asset():
            result = (ConfiguredTool.mime_type,)
        return result


@component.adapter(IExternalToolAsset, IObjectAddedEvent)
def _on_lti_asset_added(unused_asset, unused_event):
    if not can_add_lti_asset():
        raise_error(
            {
                'message': _(u"Cannot add LTI object to outline."),
                'code': 'LicenseLTIAssetRestrictedError',
            })
