#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division


__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os

import simplejson

from six.moves import cStringIO

from zope import interface

from nti.app.products.courseware_ims import IMS_CONFIGURED_TOOLS_FILE_NAME

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.app.products.courseware_ims.lti import LTI_EXTERNAL_TOOL_ASSET_MIMETYPE

from nti.cabinet.filer import transfer_to_native_file

from nti.contentlibrary.interfaces import IFilesystemBucket

from nti.contenttypes.courses.importer import BaseSectionImporter

from nti.contenttypes.courses.interfaces import ICourseInstance

from nti.contenttypes.presentation.group import NTICourseOverViewGroup

from nti.externalization.interfaces import StandardExternalFields

from nti.externalization.internalization import update_from_external_object

from nti.ntiids.oids import to_external_ntiid_oid


ITEMS = StandardExternalFields.ITEMS
GROUP_MIMETYPE = NTICourseOverViewGroup.mimeType
MIMETYPE = StandardExternalFields.MIMETYPE

__LESSONS__ = 'Lessons'


def _dump(ext_obj):
    source = cStringIO()
    simplejson.dump(ext_obj,
                    source,
                    indent='\t',
                    sort_keys=True)
    source.seek(0)
    return source


@interface.implementer(ICourseConfiguredToolContainer)
class IMSCourseSectionImporter(BaseSectionImporter):
    """
    We import all Configured Tools from the ims json file and add them
    back into the CourseConfiguredToolContainer. We then post process the lesson
    overview json to look for any External Tool Assets. Assets' Configured Tools
    json representation is then updated to the oid of these newly created
    Configured Tools by looking up the tool in the container using its id
    """

    def _update_assets_in_overview_group(self, items, course):
        modified = False
        for item in items:
            if item.get(MIMETYPE) == LTI_EXTERNAL_TOOL_ASSET_MIMETYPE:
                tool_id_container = item[u'ConfiguredTool'][u'ID']
                tool_container = ICourseConfiguredToolContainer(course)
                tool = tool_container.get(tool_id_container)
                item[u'ConfiguredTool'] = to_external_ntiid_oid(tool)
                modified = True
        return modified

    def _post_process(self, context, filer, course):
        course_path = self.course_bucket_path(course)
        lesson_bucket = os.path.join(course_path, __LESSONS__)
        # check there is a 'Lessons' folder
        if filer.is_bucket(lesson_bucket):
            lessons = filer.get(lesson_bucket)
            for lesson in lessons.enumerateChildren():
                source = self.safe_get(filer, lesson)
                if source is not None:
                    modified = False
                    ext_obj = self.load(source)
                    for item in ext_obj.get(ITEMS, []):
                        if item.get(MIMETYPE) == GROUP_MIMETYPE:
                            modified = self._update_assets_in_overview_group(item[ITEMS], course)
                    if modified:
                        source = _dump(ext_obj)
                        name = lessons.getChildNamed(lesson).name
                        filer.save(name, source,
                                   overwrite=True,
                                   bucket=lesson_bucket,
                                   contentType="application/x-json")

    def process(self, context, filer, writeout=True):
        course = ICourseInstance(context)
        for key, iface in ((IMS_CONFIGURED_TOOLS_FILE_NAME, ICourseConfiguredToolContainer),):
            path = self.course_bucket_path(course) + key
            source = self.safe_get(filer, path)
            if source is not None:
                ims_impl = iface(course)
                ext_obj = self.load(source)
                update_from_external_object(ims_impl,
                                            ext_obj,
                                            notify=False)
                self._post_process(context, filer, course)
                # save source
                if writeout and IFilesystemBucket.providedBy(course.root):
                    path = self.course_bucket_path(course) + key
                    source = self.safe_get(filer, path)  # reload
                    if source is not None:
                        self.makedirs(course.root.absolute_path)
                        new_path = os.path.join(course.root.absolute_path,
                                                key)
                        transfer_to_native_file(source, new_path)
