#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from zope.annotation.interfaces import IAnnotations

from nti.app.products.courseware_ims.lti import LTI_EXTERNAL_TOOL_ASSET_MIMETYPE
        
from nti.contenttypes.courses.interfaces import ICourseInstance

from nti.dataserver.interfaces import ILinkExternalHrefOnly

from nti.links import Link
from nti.links import render_link

#: Annotation key to store the IMS course SourcedID
COURSE_SOURCEDID_KEY = 'nti.app.products.courseware_ims.COURSE_SOURCEDID_KEY'

#: LTI Configured Tools workspace
LTI_CONFIGURED_TOOLS = 'lti-configured-tools'

#: Launch an external tool asset rel
EXTERNAL_TOOL_ASSET_LAUNCH = 'Launch'

#: Traversable path to External Tool Assets
LTI_EXTERNAL_TOOL_ASSETS = 'LTIExternalToolAssets'

#: IMS Course import/export filenames
IMS_CONFIGURED_TOOLS_FILE_NAME = u'ims_configured_tools.json'

logger = __import__('logging').getLogger(__name__)


def get_course_sourcedid(context):
    course = ICourseInstance(context, None)
    annotations = IAnnotations(course, {})
    return annotations.get(COURSE_SOURCEDID_KEY)


def set_course_sourcedid(context, sourceid=None):
    course = ICourseInstance(context, None)
    annotations = IAnnotations(course, {})
    result = annotations[COURSE_SOURCEDID_KEY] = sourceid
    return result


def _create_link(context, **kwargs):
    link = Link(context,
                **kwargs)
    interface.alsoProvides(link, ILinkExternalHrefOnly)
    return render_link(link)


def _register():
    try:
        from nti.solr.presentation import ASSETS_CATALOG
        from nti.solr.utils import mimeTypeRegistry
        mimeTypeRegistry.register(LTI_EXTERNAL_TOOL_ASSET_MIMETYPE, ASSETS_CATALOG)
    except ImportError:
        logger.warning("Solr registry is not available")

_register()
del _register
