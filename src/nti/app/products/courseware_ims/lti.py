#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division

from lti import ToolConsumer

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.cachedescriptors.property import readproperty

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer
from nti.app.products.courseware_ims.interfaces import IExternalToolAsset

from nti.contenttypes.presentation.mixins import PersistentPresentationAsset

from nti.contenttypes.courses.interfaces import ICourseInstance

from nti.ims.lti.consumer import ConfiguredToolContainer


@interface.implementer(ICourseConfiguredToolContainer)
class CourseConfiguredToolContainer(ConfiguredToolContainer):
    pass


@interface.implementer(IExternalToolAsset)
class LTIExternalToolAsset(PersistentPresentationAsset):

    def __init__(self, tool):
        super(LTIExternalToolAsset, self).__init__()
        self.__name__ = tool.__name__
        self.__parent__ = ICourseInstance
        self._configured_tool = tool
        self.configured_tool = None

    @property
    def configured_tool(self):
        return self._configured_tool

    @readproperty
    def launch_url(self):
        return self.configured_tool.launch_url

    @readproperty
    def config(self):
        return self.configured_tool.config
