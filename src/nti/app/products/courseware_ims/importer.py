#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os

from zope import interface

from nti.app.products.courseware_ims import IMS_CONFIGURED_TOOLS_FILE_NAME

from nti.app.products.courseware_ims.interfaces import ICourseConfiguredToolContainer

from nti.cabinet.filer import transfer_to_native_file

from nti.contentlibrary.interfaces import IFilesystemBucket

from nti.contenttypes.courses.importer import BaseSectionImporter

from nti.contenttypes.courses.interfaces import ICourseInstance

from nti.externalization.internalization import update_from_external_object


@interface.implementer(ICourseConfiguredToolContainer)
class IMSCourseSectionImporter(BaseSectionImporter):
    """
    Store the configured tools for this course
    """

    def process(self, context, filer, writeout=True):
        course = ICourseInstance(context)
        for key, iface in ((IMS_CONFIGURED_TOOLS_FILE_NAME, ICourseConfiguredToolContainer)):
            path = self.course_bucket_path(course) + key
            source = self.safe_get(filer, path)
            if source is not None:
                ims_impl = iface(course)
                ext_obj = self.load(source)
                update_from_external_object(ims_impl,
                                            ext_obj,
                                            notify=False)
                # save source
                if writeout and IFilesystemBucket.providedBy(course.root):
                    path = self.course_bucket_path(course) + key
                    source = self.safe_get(filer, path) # reload
                    if source is not None:
                        self.makedirs(course.root.absolute_path)
                        new_path = os.path.join(course.root.absolute_path,
                                                key)
                        transfer_to_native_file(source, new_path)