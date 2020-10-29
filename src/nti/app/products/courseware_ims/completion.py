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

from nti.app.products.courseware_ims.outcomes import get_user_outcome_result

from nti.contenttypes.completion.completion import CompletedItem

from nti.contenttypes.completion.interfaces import IProgress
from nti.contenttypes.completion.interfaces import IUserProgressUpdatedEvent
from nti.contenttypes.completion.interfaces import ICompletableItemCompletionPolicy

from nti.contenttypes.completion.policies import AbstractCompletableItemCompletionPolicy

from nti.contenttypes.completion.progress import Progress

from nti.contenttypes.completion.utils import update_completion

from nti.contenttypes.courses.interfaces import ICourseInstance

from nti.dataserver.interfaces import IUser

from nti.externalization.persistence import NoPickle

from nti.ims.lti.interfaces import ILTIUserLaunchStats

logger = __import__('logging').getLogger(__name__)


def _get_launch_stats(user, course, asset):
    return component.queryMultiAdapter((user, course, asset),
                                       ILTIUserLaunchStats)


@component.adapter(IUser, IExternalToolAsset, ICourseInstance)
@interface.implementer(IProgress)
def lti_external_tool_asset_progress(user, asset, course):
    """
    Build :class:`IProgress` based on two different heuristics, either
    one based on if the tool has outcomes or one based on whether the
    tool has ever been launched.
    """
    ntiid = getattr(asset, 'ntiid', None)
    if ntiid is None:
        return

    progress = Progress(NTIID=ntiid,
                        AbsoluteProgress=0,
                        MaxPossibleProgress=1,
                        HasProgress=False,
                        Item=asset,
                        User=user,
                        CompletionContext=course)
    if getattr(asset, 'has_outcomes', False):
        outcome_result = get_user_outcome_result(user, course, asset)
        if outcome_result is not None:
            progress.AbsoluteProgress = outcome_result.score
            progress.HasProgress = True
            progress.LastModified = outcome_result.ResultDate
    else:
        lti_launch_stats = _get_launch_stats(user, course, asset)
        if      lti_launch_stats is not None \
            and lti_launch_stats.LaunchCount:
            # Progress is 1 (max) if the asset has ever been launched
            progress.LastModified = lti_launch_stats.LastLaunchDate
            progress.AbsoluteProgress = 1
            progress.HasProgress = True
    return progress


@NoPickle
@component.adapter(IExternalToolAsset, ICourseInstance)
@interface.implementer(ICompletableItemCompletionPolicy)
class ExternalToolAssetCompletionPolicy(AbstractCompletableItemCompletionPolicy):

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
