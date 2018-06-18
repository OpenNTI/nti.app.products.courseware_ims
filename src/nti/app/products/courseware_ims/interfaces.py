#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import


from zope import interface

from zope.annotation import IAttributeAnnotatable

from zope.lifecycleevent import ObjectCreatedEvent

from zope.lifecycleevent.interfaces import IObjectCreatedEvent

from nti.app.products.courseware.interfaces import IEnrollmentOption

from nti.contenttypes.courses.interfaces import ICourseInstance

from nti.contenttypes.presentation.interfaces import href_schema_field
from nti.contenttypes.presentation.interfaces import IUserCreatedAsset
from nti.contenttypes.presentation.interfaces import IGroupOverViewable
from nti.contenttypes.presentation.interfaces import ICoursePresentationAsset

from nti.coremetadata.interfaces import IContained

from nti.dataserver.interfaces import IUser

from nti.ims.lti.interfaces import IConfiguredTool
from nti.ims.lti.interfaces import IConfiguredToolContainer

from nti.ims.sis.interfaces import IPerson

from nti.property.property import alias

from nti.schema.field import DateTime
from nti.schema.field import HTTPURL
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

    title = ValidTextLine(title=u"Title of an external tool", required=False)

    description = ValidTextLine(title=u"Description of an external tool", required=False)

    icon = href_schema_field(title=u"External tool asset icon href", required=False)

    launch_url = HTTPURL(title=u"Launch url of an external tool", required=False)


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


class ILTIAssetMetadata(IContained, IAttributeAnnotatable):
    """
    Metadata for an LTI asset.
    """

    asset_id = ValidTextLine(title=u'The LTI asset id.',
                             required=False)


class ILTILaunchEvent(interface.Interface):
    """
    An event that is sent when an LTI asset is launched
    """

    user = Object(IUser,
                  title=u'The user who launched the LTI asset.',
                  required=True)

    course = Object(ICourseInstance,
                    title=u'The course in which the LTI asset was launched.',
                    required=True)

    metadata = Object(ILTIAssetMetadata,
                      title=u'The metadata object of the LTI asset that was launched.',
                      required=True)

    timestamp = DateTime(title=u'The time at which the LTI asset was launched.',
                         required=True)


@interface.implementer(ILTILaunchEvent)
class LTILaunchEvent(object):

    def __init__(self, user, course, metadata, timestamp):
        self.user = user
        self.course = course
        self.metadata = metadata
        self.timestamp = timestamp


class IExternalToolLinkSelectionResponse(interface.Interface):
    """
    Marker interface for External Tool Link Selection responses
    """
