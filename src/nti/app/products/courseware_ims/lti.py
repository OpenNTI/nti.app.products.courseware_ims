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
from nti.app.products.courseware_ims.interfaces import IExternalToolAsset

from nti.contenttypes.presentation.mixins import PersistentPresentationAsset

from nti.externalization.datastructures import InterfaceObjectIO

from nti.externalization.interfaces import IInternalObjectUpdater

from nti.ims.lti.consumer import ConfiguredToolContainer

from nti.property.property import alias


@interface.implementer(ICourseConfiguredToolContainer)
class CourseConfiguredToolContainer(ConfiguredToolContainer):
    pass


@interface.implementer(IExternalToolAsset)
class LTIExternalToolAsset(PersistentPresentationAsset):

    mimeType = mime_type = u'application/vnd.nextthought.contenttypes.presentation.lticonfiguredtool'
    __external_class_name__ = "ExternalToolAsset"

    target = None

    Creator = alias('creator')
    desc = alias('description')
    target_ntiid = alias('target')
    ntiRequirements = alias('nti_requirements')
    targetMimeType = target_mime_type = alias('type')

    nttype = u'NTIExternalToolAsset'

    __name__ = alias('ntiid')

    @readproperty
    def ntiid(self):
        self.ntiid = self.generate_ntiid(self.nttype)
        return self.ntiid

    @property
    def configured_tool(self):
        return self._configured_tool

    @readproperty
    def launch_url(self):
        return self.configured_tool.launch_url

    @readproperty
    def config(self):
        return self.configured_tool.config


@interface.implementer(IInternalObjectUpdater)
class ExternalToolAssetUpdater(InterfaceObjectIO):

    _ext_iface_upper_bound = IExternalToolAsset

    __external_oids__ = ('ConfiguredTool', )
