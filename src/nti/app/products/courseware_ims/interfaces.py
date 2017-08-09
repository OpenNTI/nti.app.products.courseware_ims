#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.container.constraints import contains

from zope.lifecycleevent import ObjectCreatedEvent

from zope.lifecycleevent.interfaces import IObjectCreatedEvent

from nti.app.products.courseware.interfaces import IEnrollmentOption

from nti.contenttypes.presentation.interfaces import ICoursePresentationAsset
from nti.contenttypes.presentation.interfaces import IPresentationAssetContainer

from nti.dataserver.interfaces import IUser

from nti.ims.lti.interfaces import IConfiguredTool
from nti.ims.lti.interfaces import IConfiguredToolContainer

from nti.ims.sis.interfaces import IPerson

from nti.property.property import alias

from nti.schema.field import Object
from nti.schema.field import ValidTextLine


class IIMSCourseCatalog(interface.Interface):

    def courses():
        """
        return a map of IMS course id vs :class:`nti.contenttypes.courses.interfaces.ICourseInstance`
        objects
        """


class IIMSUserCreatedEvent(IObjectCreatedEvent):
    user = Object(IUser, title=u"user created")
    person = Object(IPerson, title=u"IMS person", required=False)


@interface.implementer(IIMSUserCreatedEvent)
class IMSUserCreatedEvent(ObjectCreatedEvent):

    user = alias("object")

    def __init__(self, user, person=None):
        super(IMSUserCreatedEvent, self).__init__(user)
        self.person = person


class IIMSUserFinder(interface.Interface):

    def username(person):
        """
        return the username for this person
        """

    def find(person):
        """
        return the :class:`IUser` associated with the person
        """


class IIMSUserCreationMetadata(interface.Interface):
    """
    Utility to set metadata during user creation
    """

    def data(person):
        """
        return a map with metadata
        """


class IIMSEnrollmentOption(IEnrollmentOption):
    SourcedID = ValidTextLine(title=u"Sourced ID", required=True)


class ICourseConfiguredToolContainer(IConfiguredToolContainer):
    """
    A course instance wrapper of an LTI Configured Tool Container
    """
    pass


class ILTIExternalTool(ICoursePresentationAsset):
    """
    An NTI representation of an LTI defined Tool
    """

    configured_tool = Object(IConfiguredTool,
                             required=True)


class ILTIExternalToolContainer(IPresentationAssetContainer):

    contains(ILTIExternalTool)
