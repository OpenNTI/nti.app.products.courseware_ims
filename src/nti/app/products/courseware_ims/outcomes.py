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

from nti.app.products.courseware_ims.interfaces import InvalidLTISourcedIdException

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
        parts = sourcedid.split(':')
        intids = component.getUtility(IIntIds)
        __traceback_info__ = parts
        if len(parts) != 3:
            raise InvalidLTISourcedIdException()
        user = intids.queryObject(int(parts[0]))
        course = intids.queryObject(int(parts[1]))
        asset = intids.queryObject(int(parts[2]))
        return (user, course, asset)
