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

from zope.event import notify

from zope.intid.interfaces import IIntIds

from nti.app.products.courseware_ims.interfaces import ILTIOutcomesResultSourcedIDUtility

from nti.app.products.ims.interfaces import InvalidLTISourcedIdException

from nti.ims.lti.interfaces import ITool
from nti.ims.lti.interfaces import IConfiguredTool
from nti.ims.lti.interfaces import IOutcomeService
from nti.ims.lti.interfaces import IResultSourcedId

from nti.contenttypes.completion.interfaces import UserProgressRemovedEvent
from nti.contenttypes.completion.interfaces import UserProgressUpdatedEvent

logger = __import__('logging').getLogger(__name__)


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
    An IOutcomeService that can manage outcome state for this user, course, asset/tool.
    """

    def __init__(self, user, course, asset):
        self.user = user
        self.course = course
        self.asset = asset

    def _notify(self, factory):
        event = factory(user=self.user, item=self.asset, context=self.course)
        notify(event)

    def set_score(self):
        # TODO: implement
        self._notify(UserProgressUpdatedEvent)

    def get_score(self):
        # TODO: implement
        pass

    def remove_score(self):
        # TODO: implement
        self._notify(UserProgressRemovedEvent)
