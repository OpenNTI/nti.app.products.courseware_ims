#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.lifecycleevent import ObjectCreatedEvent

from zope.lifecycleevent.interfaces import IObjectCreatedEvent

from nti.app.products.courseware.interfaces import IEnrollmentOption

from nti.contenttypes.presentation.interfaces import ICoursePresentationAsset
from nti.contenttypes.presentation.interfaces import IGroupOverViewable
from nti.contenttypes.presentation.interfaces import IUserCreatedAsset

from nti.dataserver.interfaces import IUser

from nti.ims.lti.interfaces import IConfiguredToolContainer, IConfiguredTool

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


class IExternalToolAsset(ICoursePresentationAsset, IUserCreatedAsset, IGroupOverViewable):
    """
    The NTI representation of an LTI defined Tool
    """

    ConfiguredTool = Object(IConfiguredTool,
                            required=True)


class ILTIResourceLaunchParamBuilder(interface.Interface):
    """
    Subscriber interface that adds launch time params to the ToolConsumer resource launch params
    Specifically:
    - resource_link_id
    - resource_link_title
    - resource_link_description
    """

    def build_params(consumer):
        """
        Mutates an instance of ToolConsumer launch params with context specific values
        """


class ILTIUserProfileLaunchParamBuilder(interface.Interface):
    """
    Subscriber interface that adds launch time params to the ToolConsumer user related launch params
    Specifically:
    - user_id
    - roles
    - lis_person_name_given
    - lis_person_name_family
    - lis_person_name_full
    """

    def build_params(consumer):
        """
        Mutates an instance of ToolConsumer launch params with context specific values
        """


class ILTIContextLaunchParamBuilder(interface.Interface):
    """
    Subscriber interface that adds launch time params to the ToolConsumer context launch params
    Specifically:
    - context_id
    - context_type
    - context_title
    - context_label
    """

    def build_params(consumer):
        """
        Mutates an instance of ToolConsumer launch params with context specific values
        """


class ILTIToolConsumerInfoLaunchParamBuilder(interface.Interface):
    """
    Subscriber interface that adds launch time params to the ToolConsumer consumer details launch params
    Specifically:
    - tool_consumer_instance_guid
    - tool_consumer_instance_name
    - tool_consumer_instance_url
    """

    def build_params(consumer):
        """
        Mutates an instance of ToolConsumer launch params with context specific values
        """


class ILTIPresentationLaunchParamBuilder(interface.Interface):
    """
    Subscriber interface that adds launch time params to the ToolConsumer presentation launch params
    Specifically:
    - launch_presentation_locale
    - launch_presentation_document_target
    - launch_presentation_width
    - launch_presentation_height
    - launch_presentation_return_url
    """

    def build_params(consumer):
        """
        Mutates an instance of ToolConsumer launch params with context specific values
        """


class ILTICustomLaunchParamBuilder(interface.Interface):
    """
    Subscriber interface that adds launch time params to the ToolConsumer custom launch params
    Any values added here are prefixed by custom e.g. custom_launch_param
    """

    def build_params(consumer):
        """
        Mutates an instance of ToolConsumer launch params with context specific values
        """