#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

from nti.dataserver.users import User

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.app.products.courseware_ims.interfaces import ILTILaunchParamBuilder

from nti.externalization.oids import toExternalOID


@interface.implementer(ILTILaunchParamBuilder)
class LTIResourceParams(object):

    def __init__(self, request):
        self.request = request

    def build_params(self, params):
        # This is makes some assumptions about the request that may not be ideal
        asset = self.request.context
        asset_oid = toExternalOID(asset)
        params['resource_link_id'] = asset_oid
        params['resource_link_title'] = asset.ConfiguredTool.config.title
        params['resource_link_description'] = asset.ConfiguredTool.config.title


@interface.implementer(ILTILaunchParamBuilder)
class LTIUserParams(object):

    def __init__(self, request):
        self.request = request

    def build_params(self, params):
        user_obj = User.get_user(self.request.authenticated_userid)
        params['user_id'] = toExternalOID(user_obj)
        roles = []
        for role in user_obj.dynamic_memberships:
            roles.append(role.__name__)
        params['roles'] = roles
