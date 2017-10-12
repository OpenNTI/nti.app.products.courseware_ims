#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from zope.lifecycleevent import ObjectCreatedEvent

from zope.lifecycleevent.interfaces import IObjectCreatedEvent

from nti.app.products.courseware.interfaces import IEnrollmentOption

from nti.contenttypes.presentation.interfaces import IUserCreatedAsset
from nti.contenttypes.presentation.interfaces import IGroupOverViewable
from nti.contenttypes.presentation.interfaces import ICoursePresentationAsset

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


class IExternalToolAsset(ICoursePresentationAsset,
                         IUserCreatedAsset,
                         IGroupOverViewable):
    """
    The NTI representation of an LTI defined Tool
    """

    ConfiguredTool = Object(IConfiguredTool, required=True)


class ILTILaunchParamBuilder(interface.Interface):
    """
    Subscriber interface that adds launch time params to the LTI LaunchParams
    These parameters are defined in section 3 of the IMS LTI implementation guide
    https://www.imsglobal.org/specs/ltiv1p0/implementation-guide
    """

    def build_params(params):
        """
        Mutates an instance of LaunchParams with context specific values
        """
