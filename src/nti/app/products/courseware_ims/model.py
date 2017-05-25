#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from nti.app.products.courseware.enrollment import EnrollmentOption

from nti.app.products.courseware_ims.interfaces import IIMSEnrollmentOption

from nti.externalization.representation import WithRepr

from nti.schema.eqhash import EqHash


@WithRepr
@EqHash('SourcedID',)
@interface.implementer(IIMSEnrollmentOption)
class IMSEnrollmentOption(EnrollmentOption):

    __external_class_name__ = "IMSEnrollment"
    mime_type = mimeType = 'application/vnd.nextthought.courseware.imsenrollmentoption'

    SourcedID = FP(IIMSEnrollmentOption['SourcedID'])
