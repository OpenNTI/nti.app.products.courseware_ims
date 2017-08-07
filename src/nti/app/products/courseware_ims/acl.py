#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.dataserver import authorization as nauth

from nti.dataserver.authorization_acl import ace_allowing
from nti.dataserver.authorization_acl import acl_from_aces

from nti.dataserver.interfaces import IACLProvider

CRUD = (nauth.ACT_CREATE.id,
        nauth.ACT_READ.id,
        nauth.ACT_UPDATE.id,
        nauth.ACT_DELETE.id,)


@interface.implementer(IACLProvider)
@component.adapter(ICourseConfiguredToolContainer)
class _CourseConfiguredToolContainerACLProvider(object):

    def __init__(self, context):
        self.course = context.__parent__

    @property
    def __acl__(self):
        aces = [ace_allowing(x, CRUD)
                for x in self.course.instructors]
        aces.append(ace_allowing(nauth.ROLE_CONTENT_EDITOR, CRUD))

        return acl_from_aces(aces)
