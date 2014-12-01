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

from nti.dataserver.interfaces import IUser

from nti.ims.feed.interfaces import IPerson

from nti.schema.field import Object

from nti.utils.property import alias

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
	
	def find(person):
		"""
		return the :class:`IUser` associated with the person
		"""

class IIMSUserCreationExternaValues(interface.Interface):
	"""
	Utility to add external fields when a user is being created
	"""
	
	def values(person):
		"""
		return a map with user key,value pairs to initialize a user
		"""
		