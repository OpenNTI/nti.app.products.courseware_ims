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

from nti.app.products.courseware_ims.interfaces import IExternalToolAsset

from nti.contenttypes.completion.completion import CompletedItem

from nti.contenttypes.completion.interfaces import IProgress
from nti.contenttypes.completion.interfaces import IUserProgressUpdatedEvent
from nti.contenttypes.completion.interfaces import ICompletableItemCompletionPolicy

from nti.contenttypes.completion.utils import update_completion

from nti.contenttypes.courses.interfaces import ICourseInstance

logger = __import__('logging').getLogger(__name__)


@component.adapter(IExternalToolAsset, ICourseInstance)
@interface.implementer(ICompletableItemCompletionPolicy)
class ExternalToolAssetCompletionPolicy(object):

    def __init__(self, asset, course):
        self.asset = asset
        self.course = course

    def is_complete(self, progress):
        result = None

        if progress is None:
            return result

        if not IProgress.providedBy(progress):
            return result

        if progress.AbsoluteProgress > 0:
            result = CompletedItem(Item=progress.Item,
                                   Principal=progress.User,
                                   CompletedDate=progress.LastModified)
        return result


@component.adapter(IExternalToolAsset, IUserProgressUpdatedEvent)
def _on_user_progress_updated(asset, event):
    user = event.user
    course = event.context
    update_completion(asset, asset.ntiid, user, course)
