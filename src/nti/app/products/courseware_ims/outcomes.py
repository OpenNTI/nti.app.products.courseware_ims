#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component

from zope.intid.interfaces import IIntIds

logger = __import__('logging').getLogger(__name__)


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
        parts = sourcedid.spli(':')
        intids = component.getUtility(IIntIds)
        if len(parts) != 3:
            raise InvalidLTISourcedIdException()
        user = intids.queryObject(intids[0])
        course = intids.queryObject(intids[1])
        asset = intids.queryObject(intids[2])
        return (user, course, asset)
