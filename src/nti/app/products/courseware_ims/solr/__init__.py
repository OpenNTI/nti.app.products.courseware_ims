#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from nti.solr.presentation import ASSETS_CATALOG

from nti.solr.utils import mimeTypeRegistry


def _register():

    from nti.app.products.courseware_ims.lti import LTI_EXTERNAL_TOOL_ASSET_MIMETYPE
    mimeTypeRegistry.register(LTI_EXTERNAL_TOOL_ASSET_MIMETYPE, ASSETS_CATALOG)


_register()
del _register