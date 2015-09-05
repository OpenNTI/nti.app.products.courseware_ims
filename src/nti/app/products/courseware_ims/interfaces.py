#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import interface

from zope.lifecycleevent import ObjectCreatedEvent
from zope.lifecycleevent.interfaces import IObjectCreatedEvent

from nti.app.products.courseware.interfaces import IEnrollmentOption

from nti.common.property import alias

from nti.dataserver.interfaces import IUser

from nti.ims.sis.interfaces import IPerson

from nti.schema.field import Object
from nti.schema.field import ValidTextLine

class IIMSCourseCatalog(interface.Interface):

	def courses():
		"""
		return a map of IMS course id vs :class:`nti.contenttypes.courses.interfaces.ICourseInstance`
		objects
		"""

class IIMSUserCreatedEvent(IObjectCreatedEvent):
	user = Object(IUser, title="user created")
	person = Object(IPerson, title="IMS person", required=False)

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
	SourcedID = ValidTextLine(title="Sourced ID", required=True)
