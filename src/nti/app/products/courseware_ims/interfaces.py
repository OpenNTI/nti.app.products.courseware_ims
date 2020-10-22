#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=inherit-non-class,expression-not-assigned

from zope import interface

from zope.lifecycleevent import ObjectCreatedEvent

from zope.lifecycleevent.interfaces import IObjectCreatedEvent

from zope.schema import ValidationError

from nti.app.products.courseware.interfaces import IEnrollmentOption

from nti.contenttypes.completion.interfaces import ICompletableItem

from nti.contenttypes.courses.interfaces import ICourseInstance

from nti.contenttypes.presentation.interfaces import href_schema_field
from nti.contenttypes.presentation.interfaces import byline_schema_field

from nti.contenttypes.presentation.interfaces import IUserCreatedAsset
from nti.contenttypes.presentation.interfaces import IGroupOverViewable
from nti.contenttypes.presentation.interfaces import INTIIDIdentifiable
from nti.contenttypes.presentation.interfaces import IAssetTitleDescribed
from nti.contenttypes.presentation.interfaces import ICoursePresentationAsset

from nti.dataserver.interfaces import IUser

from nti.ims.lti.interfaces import IConfiguredTool
from nti.ims.lti.interfaces import IConfiguredToolContainer

from nti.ims.sis.interfaces import IPerson

from nti.property.property import alias

from nti.schema.field import Bool
from nti.schema.field import Text
from nti.schema.field import Object
from nti.schema.field import HTTPURL
from nti.schema.field import DateTime
from nti.schema.field import DecodingValidTextLine as ValidTextLine


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
                         IGroupOverViewable,
                         INTIIDIdentifiable,
                         IAssetTitleDescribed,
                         ICompletableItem):
    """
    The NTI representation of an LTI defined Tool
    """

    ConfiguredTool = Object(IConfiguredTool, required=True)

    byline = byline_schema_field(required=False)

    title = ValidTextLine(title=u"Title of an external tool", required=False)

    description = Text(title=u"Description of an external tool",
                       required=False)

    icon = href_schema_field(title=u"External tool asset icon href",
                             required=False)

    launch_url = HTTPURL(title=u"Launch url of an external tool",
                         required=False)

    has_outcomes = Bool(title=u"External tool returns outcomes",
                        default=False,
                        required=False)


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


class ILTIOutcomesResultSourcedIDUtility(interface.Interface):
    """
    Utility that can build a sourcedid paramter and decode a sourcedid parameter.
    """

    def build_sourcedid(user, course, asset):
        pass

    def decode_sourcedid(sourcedid):
        """
        Returns a tuple of (user, course, asset), some of which may be None.
        """


class IInvalidLTISourcedIdException(interface.Interface):
    """
    marker interface for enrollment exception"
    """


@interface.implementer(IInvalidLTISourcedIdException)
class InvalidLTISourcedIdException(ValidationError):
    __doc__ = _(u'Invalid outcomes result sourcedid.')
    i18n_message = __doc__


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

    asset = Object(IExternalToolAsset,
                   title=u'The asset that was launched.',
                   required=True)

    timestamp = DateTime(title=u'The time at which the LTI asset was launched.',
                         required=True)


@interface.implementer(ILTILaunchEvent)
class LTILaunchEvent(object):

    def __init__(self, user, course, asset, timestamp):
        self.user = user
        self.course = course
        self.asset = asset
        self.timestamp = timestamp


class IExternalToolLinkSelectionResponse(interface.Interface):
    """
    Marker interface for External Tool Link Selection responses
    """


class ISiteLicenseLTIPolicy(interface.Interface):
    """
    The policy determining LTI usage based on the current site license.
    """

    def can_add_lti_tools():
        """
        Returns a bool whether or not an LTI tool can be added.
        """

    def can_add_lti_asset():
        """
        Returns a bool whether or not an LTI asset can be added
        to a course outline.
        """
