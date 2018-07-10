#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from persistent import Persistent

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

from nti.ntiids.oids import to_external_ntiid_oid

from nti.property.property import alias

from nti.schema.fieldproperty import createDirectFieldProperties
from zope.container.contained import Contained

from nti.wref import IWeakRef

logger = __import__('logging').getLogger(__name__)

PARSE_VALS = ('title', 'description', 'launch_url')

LTI_ASSET_METADATA_KEY = 'nti.app.products.courseware_ims.lti.metadata'

LTI_EXTERNAL_TOOL_ASSET_MIMETYPE = 'application/vnd.nextthought.ltiexternaltoolasset'


@interface.implementer(ICourseConfiguredToolContainer)
class CourseConfiguredToolContainer(ConfiguredToolContainer):
    pass


@interface.implementer(IExternalToolAsset)
class LTIExternalToolAsset(PersistentPresentationAsset):
    createDirectFieldProperties(IExternalToolAsset)

    mimeType = mime_type = LTI_EXTERNAL_TOOL_ASSET_MIMETYPE

    __external_class_name__ = "ExternalToolAsset"

    target = None

    Creator = alias('creator')
    desc = alias('description')

    nttype = u'NTIExternalToolAsset'

    __name__ = alias('ntiid')

    def __init__(self, *args, **kwargs):
        super(LTIExternalToolAsset, self).__init__(*args, **kwargs)
        # SchemaConfigured initializes these to None if a value isn't given
        # and breaks readproperty so they need to be explicitly removed
        # if they were not intentionally set to None
        for attr in PARSE_VALS:
            if attr not in kwargs and getattr(self, attr, self) is None:
                delattr(self, attr)

    @readproperty
    def ntiid(self):
        self.ntiid = self.generate_ntiid(self.nttype)
        return self.ntiid

    @readproperty
    def launch_url(self):
        return self.ConfiguredTool.launch_url

    @readproperty
    def title(self):
        # This must be unicode to work with SchemaConfigured
        return six.text_type(self.ConfiguredTool.title)

    @readproperty
    def description(self):
        # This must be unicode to work with SchemaConfigured
        return six.text_type(self.ConfiguredTool.description)

    @property
    def ConfiguredTool(self):
        result = None
        if getattr(self, '_ConfiguredTool', None) is not None:
            result = self._ConfiguredTool()
        return result

    @ConfiguredTool.setter
    def ConfiguredTool(self, value):
        self._ConfiguredTool = IWeakRef(value)


@interface.implementer(IInternalObjectUpdater)
class ExternalToolAssetUpdater(InterfaceObjectIO):

    _ext_iface_upper_bound = IExternalToolAsset

    __external_oids__ = ('ConfiguredTool',)

    def updateFromExternalObject(self, parsed, *args, **kwargs):
        # This checks to see if title and/or description have no value. If they do not, we delete
        # them so that this information is instead gleaned off the ConfiguredTool
        for attr in PARSE_VALS:
            if attr in parsed and not parsed[attr]:
                del parsed[attr]
        super(ExternalToolAssetUpdater, self).updateFromExternalObject(parsed, *args, **kwargs)


@interface.implementer(INTIIDResolver)
class NTIIDReferenceResolver(object):

    _ext_iface = IExternalToolAsset

    def resolve(self, key):
        result = component.queryUtility(self._ext_iface, name=key)
        return result


# This used to be stored as a persistent annotation so we leave it around for now
# so the bad data can be unpickled if needed
class LTIAssetMetadata(Persistent, Contained):
    """
    A metadata object for an LTI asset
    """

    @property
    def ntiid(self):
        return to_external_ntiid_oid(self)
