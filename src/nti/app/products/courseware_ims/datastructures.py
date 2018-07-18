#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from nti.contentfile.datastructures import BaseFactory

from nti.ims.lti.consumer import ConfiguredTool

logger = __import__('logging').getLogger(__name__)


def ConfiguredToolFactory(ext_obj):
    return BaseFactory(ext_obj, ConfiguredTool, ConfiguredTool)
