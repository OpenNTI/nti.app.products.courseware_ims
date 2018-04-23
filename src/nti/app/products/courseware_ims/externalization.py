#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from zope import component
from zope import interface

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.externalization.externalization import to_standard_external_dictionary

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
        result['tools'] = [tool for tool in self.container]
        return result
