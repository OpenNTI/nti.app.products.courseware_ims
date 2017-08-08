#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


from zope import interface

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.ims.lti.consumer import ConfiguredToolContainer


@interface.implementer(ICourseConfiguredToolContainer)
class CourseConfiguredToolContainer(ConfiguredToolContainer):
    pass




