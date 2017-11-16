#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from zope import component
from zope import interface

from zope.cachedescriptors.property import readproperty

from nti.app.products.courseware_ims.interfaces import IExternalToolAsset
from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.contenttypes.presentation.mixins import PersistentPresentationAsset

from nti.externalization.datastructures import InterfaceObjectIO

from nti.externalization.interfaces import IInternalObjectUpdater

from nti.ims.lti.consumer import ConfiguredToolContainer

from nti.ntiids.interfaces import INTIIDResolver

from nti.property.property import alias

from nti.schema.fieldproperty import createDirectFieldProperties

logger = __import__('logging').getLogger(__name__)


@interface.implementer(ICourseConfiguredToolContainer)
class CourseConfiguredToolContainer(ConfiguredToolContainer):
    pass


@interface.implementer(IExternalToolAsset)
class LTIExternalToolAsset(PersistentPresentationAsset):
    createDirectFieldProperties(IExternalToolAsset)

    mimeType = mime_type = 'application/vnd.nextthought.externaltoolasset'

    __external_class_name__ = "ExternalToolAsset"

    target = None

    Creator = alias('creator')
    desc = alias('description')
    configured_tool = alias('ConfiguredTool')

    nttype = u'NTIExternalToolAsset'

    __name__ = alias('ntiid')

    def __init__(self, *args, **kwargs):
        super(LTIExternalToolAsset, self).__init__(*args, **kwargs)
        # SchemaConfigured initializes these to None if a value isn't given
        # and breaks readproperty so they need to be explicitly removed
        # if they were not intentionally set to None
        for attr in ('title', 'description'):
            if attr not in kwargs and getattr(self, attr, self) is None:
                delattr(self, attr)

    @readproperty
    def ntiid(self):
        self.ntiid = self.generate_ntiid(self.nttype)
        return self.ntiid

    @readproperty
    def launch_url(self):
        return self.configured_tool.launch_url

    @readproperty
    def config(self):
        return self.configured_tool.config

    @readproperty
    def title(self):
        # This must be unicode to work with SchemaConfigured
        return six.text_type(self.config.title)

    @readproperty
    def description(self):
        # This must be unicode to work with SchemaConfigured
        return six.text_type(self.config.description)


@interface.implementer(IInternalObjectUpdater)
class ExternalToolAssetUpdater(InterfaceObjectIO):

    _ext_iface_upper_bound = IExternalToolAsset

    __external_oids__ = ('ConfiguredTool',)


@interface.implementer(INTIIDResolver)
class NTIIDReferenceResolver(object):

    _ext_iface = IExternalToolAsset

    def resolve(self, key):
        result = component.queryUtility(self._ext_iface, name=key)
        return result
