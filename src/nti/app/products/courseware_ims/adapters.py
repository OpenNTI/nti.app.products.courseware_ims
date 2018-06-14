#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope.annotation import IAnnotations

from nti.app.products.courseware_ims.lti import CourseConfiguredToolContainer
from nti.app.products.courseware_ims.lti import LTI_EXTERNAL_TOOL_ASSET_MIMETYPE

from nti.contenttypes.courses.interfaces import ICourseInstance

TOOLS_ANNOTATION_KEY = 'lti_configured_tools'


def course_to_configured_tool_container(context, create=True):
    course = ICourseInstance(context)
    annotations = IAnnotations(course)
    tools = annotations.get(TOOLS_ANNOTATION_KEY)
    if create and tools is None:
        tools = CourseConfiguredToolContainer()
        tools.__parent__ = course
        tools.__name__ = TOOLS_ANNOTATION_KEY
        annotations[TOOLS_ANNOTATION_KEY] = tools
    return tools


# External Tool Link Selection adapters

def _parse_description(result):
    if result.get('text') and result.get('text') != 'undefined':
        result['description'] = result['text']
    return result


def ETLS_external_tool_asset(request):
    result = dict(request.params)
    tool_oid = request.subpath[0]
    result['ConfiguredTool'] = tool_oid
    result['launch_url'] = result['url']
    _parse_description(result)
    result['MimeType'] = LTI_EXTERNAL_TOOL_ASSET_MIMETYPE
    return result


def ETLS_external_link(request):
    result = dict(request.params)
    result['MimeType'] = "application/vnd.nextthought.relatedworkref"
    result['byline'] = request.remote_user
    result['label'] = result.get('title', "")
    _parse_description(result)
    result['href'] = result['url']
    result['targetMimeType'] = 'application/vnd.nextthought.externallink'
    return result