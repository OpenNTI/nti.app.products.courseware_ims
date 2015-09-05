#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from nti.app.products.courseware.enrollment import EnrollmentOption

from nti.common.persistence import NoPickle
from nti.common.representation import WithRepr

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IInternalObjectExternalizer

from nti.schema.schema import EqHash

from .interfaces import IIMSEnrollmentOption

CLASS = StandardExternalFields.CLASS
MIMETYPE = StandardExternalFields.MIMETYPE

@WithRepr
@NoPickle
@EqHash('SourcedID',)
@interface.implementer(IIMSEnrollmentOption, IInternalObjectExternalizer)
class IMSEnrollmentOption(EnrollmentOption):

	__external_class_name__ = "IMSEnrollment"
	mime_type = mimeType = 'application/vnd.nextthought.courseware.imsenrollmentoption'

	SourcedID = FP(IIMSEnrollmentOption['SourcedID'])

	def toExternalObject(self, *args, **kwargs):
		result = LocatedExternalDict()
		result[MIMETYPE] = self.mimeType
		result[CLASS] = self.__external_class_name__
		result['SourcedID'] = result['sourcedid'] = self.SourcedID
		return result
