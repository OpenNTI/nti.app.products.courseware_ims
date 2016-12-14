#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import zope.i18nmessageid
MessageFactory = zope.i18nmessageid.MessageFactory("nti.app.products.ims")

from zope.annotation.interfaces import IAnnotations

from nti.contenttypes.courses.interfaces import ICourseInstance

#: Annotation key to store the IMS course SourcedID
COURSE_SOURCEDID_KEY = 'nti.app.products.courseware_ims.COURSE_SOURCEDID_KEY'

def get_course_sourcedid(context):
	course = ICourseInstance(context, None)
	annotations = IAnnotations(course, {})
	return annotations.get(COURSE_SOURCEDID_KEY)

def set_course_sourcedid(context, sourceid=None):
	course = ICourseInstance(context, None)
	annotations = IAnnotations(course, {})
	result = annotations[COURSE_SOURCEDID_KEY] = sourceid
	return result
