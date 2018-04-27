#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from nti.app.products.ims import MessageFactory

from zope.annotation.interfaces import IAnnotations

from nti.contenttypes.courses.interfaces import ICourseInstance

#: Annotation key to store the IMS course SourcedID
COURSE_SOURCEDID_KEY = 'nti.app.products.courseware_ims.COURSE_SOURCEDID_KEY'

#: LTI Configured Tools workspace
LTI_CONFIGURED_TOOLS = 'lti-configured-tools'

#: Launch an external tool asset rel
EXTERNAL_TOOL_ASSET_LAUNCH = 'Launch'

#: IMS Course import/export filenames
IMS_CONFIGURED_TOOLS_FILE_NAME = u'ims_configured_tools.json'


def get_course_sourcedid(context):
    course = ICourseInstance(context, None)
    annotations = IAnnotations(course, {})
    return annotations.get(COURSE_SOURCEDID_KEY)


def set_course_sourcedid(context, sourceid=None):
    course = ICourseInstance(context, None)
    annotations = IAnnotations(course, {})
    result = annotations[COURSE_SOURCEDID_KEY] = sourceid
    return result
