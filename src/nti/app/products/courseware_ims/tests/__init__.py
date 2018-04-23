#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from nti.ims.lti.consumer import ConfiguredTool
from nti.ims.lti.consumer import PersistentToolConfig

from nti.testing.layers import ZopeComponentLayer
from nti.testing.layers import ConfiguringLayerMixin

import zope.testing.cleanup

TOOL_CONFIG = {
    'key': u'Test Key',
    'secret': u'Test Secret',
    'title': u'Test',
    'description': u'A test tool',
    'launch_url': u'http://test.com',
    'secure_launch_url': u'https://test.com'
}


def create_configured_tool():
    tool = ConfiguredTool()
    tool.consumer_key = TOOL_CONFIG['key']
    tool.secret = TOOL_CONFIG['secret']
    config = PersistentToolConfig(**TOOL_CONFIG)
    tool.config = config
    return tool


class SharedConfiguringTestLayer(ZopeComponentLayer,
                                 ConfiguringLayerMixin):

    set_up_packages = ('nti.contenttypes.presentation',
                       'nti.app.products.courseware_ims',
                       'nti.ims',
                       'nti.app.products.ims',)

    @classmethod
    def setUp(cls):
        cls.setUpPackages()

    @classmethod
    def tearDown(cls):
        cls.tearDownPackages()
        zope.testing.cleanup.cleanUp()

    @classmethod
    def testSetUp(cls):
        pass

    @classmethod
    def testTearDown(cls):
        pass
