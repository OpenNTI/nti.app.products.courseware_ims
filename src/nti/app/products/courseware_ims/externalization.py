#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from nti.ntiids.oids import to_external_ntiid_oid
from zope import component
from zope import interface

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.externalization.externalization import to_standard_external_dictionary, toExternalObject, to_external_object

from nti.externalization.interfaces import IExternalObject
from nti.externalization.interfaces import StandardExternalFields

ITEMS = StandardExternalFields.ITEMS

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


@component.adapter(ICourseConfiguredToolContainer)
@interface.implementer(IExternalObject)
class _CourseConfiguredToolContainerExternalObject(object):

    def __init__(self, container):
        self.container = container

    def toExternalObject(self, **kwargs):
        result = to_standard_external_dictionary(self.container, **kwargs)
        result[ITEMS] = {
            key: to_external_object(val, name='exporter') for key, val in self.container.items()
        }
        return result
