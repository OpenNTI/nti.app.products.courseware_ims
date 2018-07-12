#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from hamcrest import assert_that
from hamcrest import is_
from hamcrest import none

from datetime import datetime

from zope.event import notify

from nti.app.products.courseware.tests import InstructedCourseApplicationTestLayer

from nti.app.products.courseware_ims.interfaces import LTILaunchEvent

from nti.app.products.courseware_ims.lti import LTIExternalToolAsset

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.contenttypes.completion.interfaces import UserProgressUpdatedEvent

from nti.contenttypes.completion.utils import get_completed_item

from nti.contenttypes.courses.courses import CourseInstance

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.dataserver.users import User

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


class TestCompletion(ApplicationLayerTest):
    layer = InstructedCourseApplicationTestLayer

    @WithMockDSTrans
    def test_asset_completion(self):

        asset = LTIExternalToolAsset()
        asset.ntiid = u'tag:nextthought.com,2011:test'
        user = User.create_user(username='test_user', dataserver=self.ds)
        course = CourseInstance()
        connection = mock_dataserver.current_transaction
        connection.add(course)

        progress_event = UserProgressUpdatedEvent(obj=asset,
                                                  user=user,
                                                  context=course)

        notify(progress_event)
        completed_item = get_completed_item(user, course, asset)
        assert_that(completed_item, none())

        timestamp = datetime.now()
        launch_event = LTILaunchEvent(user=user,
                                      course=course,
                                      asset=asset,
                                      timestamp=timestamp)
        notify(launch_event)
        notify(progress_event)
        completed_item = get_completed_item(user, course, asset)
        assert_that(completed_item.ItemNTIID, is_(asset.ntiid))
        assert_that(completed_item.CompletedDate.year, is_(timestamp.year))
