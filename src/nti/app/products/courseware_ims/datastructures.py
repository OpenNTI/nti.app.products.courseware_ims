#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

from nti.contentfile.datastructures import BaseFactory
from nti.ims.lti.consumer import ConfiguredTool

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


def ConfiguredToolFactory(ext_obj):
    return BaseFactory(ext_obj, ConfiguredTool, ConfiguredTool)
