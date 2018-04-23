#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

import unittest

from nti.app.products.courseware_ims.interfaces import IExternalToolAsset

from nti.app.products.courseware_ims.lti import LTIExternalToolAsset

from nti.app.products.courseware_ims.tests import create_configured_tool
from nti.app.products.courseware_ims.tests import SharedConfiguringTestLayer

from nti.contenttypes.presentation.group import NTICourseOverViewGroup

from nti.contenttypes.presentation.lesson import NTILessonOverView


class TestExternalToolAsset(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def test_external_tool_asset(self):
        tool = create_configured_tool()
        asset = LTIExternalToolAsset(ConfiguredTool=tool)
        assert_that(asset.launch_url, is_(tool.launch_url))

        assert_that(asset, verifiably_provides(IExternalToolAsset))
        assert_that(asset, validly_provides(IExternalToolAsset))

        course = NTICourseOverViewGroup()
        assert_that(course.items, is_(None))
        course.append(asset)
        assert_that(course, has_length(1))

        assert_that(course.items, has_length(1))

        lesson = NTILessonOverView()

        assert_that(lesson.items, is_(None))
        lesson.append(course)
        assert_that(lesson.items, has_length(1))

        course = lesson.pop(0)
        assert_that(lesson.items, has_length(0))

        asset = course.pop(0)
        assert_that(course.items, has_length(0))

        assert_that(asset, verifiably_provides(IExternalToolAsset))
        assert_that(asset, validly_provides(IExternalToolAsset))
