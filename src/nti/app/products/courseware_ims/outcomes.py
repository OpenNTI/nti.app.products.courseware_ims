#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from datetime import datetime

from ZODB.interfaces import IConnection

from zope import component
from zope import interface

from zope.annotation import factory as an_factory

from zope.event import notify

from zope.intid.interfaces import IIntIds

from nti.app.products.courseware_ims.interfaces import ILTIOutcomesResultSourcedIDUtility

from nti.app.products.ims.interfaces import IOutcomeResultContainer
from nti.app.products.ims.interfaces import IUserOutcomeResultContainer
from nti.app.products.ims.interfaces import InvalidLTISourcedIdException

from nti.app.products.ims.outcomes import UserOutcomeResult
from nti.app.products.ims.outcomes import OutcomeResultContainer
from nti.app.products.ims.outcomes import UserOutcomeResultContainer

from nti.ims.lti.interfaces import ITool
from nti.ims.lti.interfaces import IConfiguredTool
from nti.ims.lti.interfaces import IOutcomeService
from nti.ims.lti.interfaces import IResultSourcedId

from nti.contenttypes.completion.interfaces import UserProgressRemovedEvent
from nti.contenttypes.completion.interfaces import UserProgressUpdatedEvent

from nti.contenttypes.courses.interfaces import ICourseInstance

logger = __import__('logging').getLogger(__name__)


OUTCOME_RESULT_CONTAINER_ANNOTATION_KEY = 'nti.contenttypes.completion.interfaces.ICompletedItemContainer'


def get_user_outcome_result(user, course, asset):
    """
    Return the IUserOutcomeResult for the given user, course, asset.
    """
    course_container = IOutcomeResultContainer(course)
    username = user.username
    item_ntiid = asset.ntiid
    if username in course_container:
        user_container = course_container[username]
        if item_ntiid in user_container:
            return user_container[item_ntiid]


@interface.implementer(ILTIOutcomesResultSourcedIDUtility)
class LTIOutcomesResultSourcedIDUtility(object):

    def build_sourcedid(self, user, course, asset):
        intids = component.getUtility(IIntIds)
        user_id = intids.getId(user)
        course_id = intids.getId(course)
        asset_id = intids.getId(asset)
        return '%s:%s:%s' % (user_id, course_id, asset_id)

    def decode_sourcedid(self, sourcedid):
        """
        Returns a tuple of (user, course, asset), some of which may be None.
        """
        parts = sourcedid.split(':')
        intids = component.getUtility(IIntIds)
        __traceback_info__ = parts
        if len(parts) != 3:
            raise InvalidLTISourcedIdException()
        user = intids.queryObject(int(parts[0]))
        course = intids.queryObject(int(parts[1]))
        asset = intids.queryObject(int(parts[2]))
        return (user, course, asset)


@component.adapter(IResultSourcedId)
@interface.implementer(ITool)
def _get_tool_from_sourcedid(sourcedid):
    sourcedid_util = component.getUtility(ILTIOutcomesResultSourcedIDUtility)
    unused_user, unused_course, asset = sourcedid_util.decode_sourcedid(sourcedid.lis_result_sourcedid)
    tool = IConfiguredTool(asset, None)
    return tool


@component.adapter(IResultSourcedId)
@interface.implementer(IOutcomeService)
def _course_outcome_service_from_sourcedid(sourcedid):
    sourcedid_util = component.getUtility(ILTIOutcomesResultSourcedIDUtility)
    user, course, asset = sourcedid_util.decode_sourcedid(sourcedid.lis_result_sourcedid)
    if      user is not None \
        and course is not None \
        and asset is not None:
        return CourseOutcomeService(user, course, asset)


@interface.implementer(IOutcomeService)
class CourseOutcomeService(object):
    """
    An IOutcomeService that can manage outcome state for this user, course, asset.
    """

    def __init__(self, user, course, asset):
        self.user = user
        self.course = course
        self.asset = asset

    def _notify(self, factory):
        event = factory(user=self.user, item=self.asset, context=self.course)
        notify(event)

    def set_score(self, score):
        course_container = IOutcomeResultContainer(self.course)
        username = self.user.username
        item_ntiid = self.asset.ntiid
        try:
            user_container = course_container[username]
        except KeyError:
            user_container = UserCourseOutcomeResultContainer()
            course_container[username] = user_container
        try:
            result = user_container[item_ntiid]
            result.score = score
            result.ResultDate = datetime.utcnow()
        except KeyError:
            result = UserOutcomeResult(score=score,
                                       ItemNTIID=item_ntiid,
                                       ResultDate=datetime.utcnow())
            user_container[item_ntiid] = result
        logger.info("Storing LTI score (%s)", result)
        self._notify(UserProgressUpdatedEvent)
        return result

    def get_score(self):
        outcome_result = get_user_outcome_result(self.user,
                                                 self.course,
                                                 self.asset)
        if outcome_result:
            return outcome_result.score

    def remove_score(self):
        course_container = IOutcomeResultContainer(self.course)
        username = self.user.username
        item_ntiid = self.asset.ntiid
        if self.user.username in course_container:
            user_container = course_container[username]
            if item_ntiid in user_container:
                result = user_container.pop(item_ntiid)
                logger.info("Removed LTI score (%s)", result)
                self._notify(UserProgressRemovedEvent)


@interface.implementer(IUserOutcomeResultContainer)
class UserCourseOutcomeResultContainer(UserOutcomeResultContainer):
    """
    Stores mappings of asset_ntiid -> IUserOutcomeResult
    """


@component.adapter(ICourseInstance)
@interface.implementer(IOutcomeResultContainer)
class CourseOutcomeResultContainer(OutcomeResultContainer):
    """
    Stores mappings of username -> IUserOutcomeResultContainer for a user.
    """


_CourseOutcomeResultContainerFactory = an_factory(CourseOutcomeResultContainer,
                                                  OUTCOME_RESULT_CONTAINER_ANNOTATION_KEY)


def _create_annotation(obj, factory):
    result = factory(obj)
    if IConnection(result, None) is None:
        try:
            # pylint: disable=too-many-function-args
            IConnection(obj).add(result)
        except (TypeError, AttributeError):  # pragma: no cover
            pass
    return result


def CourseOutcomeResultContainerFactory(obj):
    return _create_annotation(obj, _CourseOutcomeResultContainerFactory)

