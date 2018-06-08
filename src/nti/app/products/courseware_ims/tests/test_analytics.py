#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import datetime
from hamcrest import is_, assert_that
from nti.analytics.lti import _lti_asset_launched
from nti.analytics_database.tests import AnalyticsDatabaseTest
from nti.app.contenttypes.presentation import VIEW_CONTENTS
from nti.app.products.courseware.tests import InstructedCourseApplicationTestLayer
from nti.app.products.courseware_ims.adapters import TOOLS_ANNOTATION_KEY
from nti.app.products.courseware_ims.interfaces import LTILaunchEvent, ILTIAssetMetadata
from nti.app.products.courseware_ims.lti import LTIAssetMetadata, LTIExternalToolAsset
from nti.app.products.courseware_ims.tests import create_configured_tool
from nti.app.products.courseware_ims.tests.test_views import TOOL_DATA
from nti.app.testing.application_webtest import ApplicationLayerTest
from nti.app.testing.decorators import WithSharedApplicationMockDS
from nti.contenttypes.courses.courses import ContentCourseInstance
from nti.dataserver.tests import mock_dataserver
from nti.dataserver.users import User
from nti.ims.lti.consumer import ConfiguredTool

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


class TestLTIAnalytics(ApplicationLayerTest, AnalyticsDatabaseTest):

    layer = InstructedCourseApplicationTestLayer

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_asset_analytics(self):

        from IPython.core.debugger import Tracer;Tracer()()

        tool = create_configured_tool()
        asset = LTIExternalToolAsset(ConfiguredTool=tool)
        metadata = ILTIAssetMetadata(asset)

        with mock_dataserver.mock_db_trans(self.ds):
            ds = mock_dataserver.current_mock_ds
            user = User.create_user(ds, username=u'foonextthought1',
                                    password=u'TestPass')
            event = LTILaunchEvent(user=user,
                                   course=ContentCourseInstance(),
                                   metadata=metadata,
                                   timestamp=datetime.datetime.now())

            _lti_asset_launched(event)
