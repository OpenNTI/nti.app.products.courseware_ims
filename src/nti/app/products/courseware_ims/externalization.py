#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.externalization.externalization import to_external_object
from nti.externalization.externalization import to_standard_external_dictionary

from nti.externalization.interfaces import IExternalObject
from nti.externalization.interfaces import StandardExternalFields

from nti.ntiids.oids import to_external_ntiid_oid

ITEMS = StandardExternalFields.ITEMS

logger = __import__('logging').getLogger(__name__)


@component.adapter(ICourseConfiguredToolContainer)
@interface.implementer(IExternalObject)
class _CourseConfiguredToolContainerExternalObject(object):

    def __init__(self, container):
        self.container = container

    def toExternalObject(self, **kwargs):
        result = to_standard_external_dictionary(self.container, **kwargs)
        result[ITEMS] = {
            to_external_ntiid_oid(val): to_external_object(val, name='exporter', decorate=False)
            for val in self.container.values()
        }
        return result
