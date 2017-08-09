#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.cachedescriptors.property import readproperty

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.ims.lti.consumer import ConfiguredToolContainer


@interface.implementer(ICourseConfiguredToolContainer)
class CourseConfiguredToolContainer(ConfiguredToolContainer):
    pass


class LTIExternalToolAsset(object):

    @property
    def configured_tool(self):
        return self.configured_tool

    @configured_tool.setter
    def configured_tool(self, tool):
        self.configured_tool = tool

    @readproperty
    def launch_url(self):
        return self.configured_tool.launch_url
