#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from zope import component

from zope.intid.interfaces import IIntIdRemovedEvent

from zope.lifecycleevent import IObjectModifiedEvent

from zc.intid.interfaces import IAfterIdAddedEvent


from nti.app.products.courseware_ims.interfaces import IExternalToolAsset

from nti.contenttypes.presentation.interfaces import IPresentationAssetMovedEvent

from nti.solr.common import queue_add
from nti.solr.common import queue_modified
from nti.solr.common import queue_remove
from nti.solr.common import single_index_job
from nti.solr.common import single_unindex_job

from nti.solr.interfaces import IIndexObjectEvent
from nti.solr.interfaces import IUnindexObjectEvent

from nti.solr.presentation import ASSETS_QUEUE




__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


@component.adapter(IExternalToolAsset, IAfterIdAddedEvent)
def _asset_added(obj, _=None):
    queue_add(ASSETS_QUEUE, single_index_job, obj)


@component.adapter(IExternalToolAsset, IObjectModifiedEvent)
def _asset_modified(obj, _):
    queue_modified(ASSETS_QUEUE, single_index_job, obj)


@component.adapter(IExternalToolAsset, IIntIdRemovedEvent)
def _asset_removed(obj, _):
    queue_remove(ASSETS_QUEUE, single_unindex_job, obj=obj)


@component.adapter(IExternalToolAsset, IPresentationAssetMovedEvent)
def _asset_moved(obj, _):
    queue_modified(ASSETS_QUEUE, single_index_job, obj=obj)


@component.adapter(IExternalToolAsset, IIndexObjectEvent)
def _index_asset(obj, _):
    _asset_added(obj, None)


@component.adapter(IExternalToolAsset, IUnindexObjectEvent)
def _unindex_asset(obj, _):
    _asset_removed(obj, None)