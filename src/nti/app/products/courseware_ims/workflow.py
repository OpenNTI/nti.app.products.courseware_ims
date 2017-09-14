#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from collections import defaultdict

from requests.structures import CaseInsensitiveDict

from zope import component
from zope import lifecycleevent

from zope.event import notify

from zope.security.interfaces import IPrincipal

from nti.app.products.courseware_ims import get_course_sourcedid
from nti.app.products.courseware_ims import set_course_sourcedid

from nti.app.products.courseware_ims.interfaces import IIMSUserFinder
from nti.app.products.courseware_ims.interfaces import IIMSCourseCatalog
from nti.app.products.courseware_ims.interfaces import IMSUserCreatedEvent
from nti.app.products.courseware_ims.interfaces import IIMSUserCreationMetadata

from nti.contenttypes.courses.interfaces import ES_PUBLIC
from nti.contenttypes.courses.interfaces import ES_CREDIT_DEGREE

from nti.contenttypes.courses.interfaces import ICourseInstance
from nti.contenttypes.courses.interfaces import ICourseSubInstance
from nti.contenttypes.courses.interfaces import ICourseEnrollments
from nti.contenttypes.courses.interfaces import ICourseCatalogEntry
from nti.contenttypes.courses.interfaces import IDenyOpenEnrollment
from nti.contenttypes.courses.interfaces import ICourseEnrollmentManager
from nti.contenttypes.courses.interfaces import INonPublicCourseInstance

from nti.contenttypes.courses.utils import get_parent_course
from nti.contenttypes.courses.utils import drop_any_other_enrollments
from nti.contenttypes.courses.utils import is_there_an_open_enrollment

from nti.dataserver.users.users import User

from nti.externalization.interfaces import LocatedExternalDict

from nti.ims.sis.enterprise import Enterprise
from nti.ims.sis.interfaces import IEnterprise
from nti.ims.sis.interfaces import ACTIVE_STATUS
from nti.ims.sis.interfaces import INACTIVE_STATUS

from nti.ims.sis.person import Person


def create_proxy_person(member):
    result = Person(sourcedid=member.sourcedid,
                    userid=member.userid,
                    name=None,
                    email=None,
                    userrole=member.roletype)
    return result


def get_person_userid(person):
    if person.userid:
        result = person.userid
    else:
        result = person.sourcedid.id
    return result.lower() if result else None


def get_person_email(person):
    username = get_person_userid(person)
    if person.email:
        result = person.email
    else:
        result = username + u'@example.com'
        logger.warn('%s does not have an email. Defaulting to %s',
                    username, result)

    result = result.lower()
    if result.endswith('@nextthought.com'):
        result = result[:-15] + u'example.com'
    return result


def find_user(person):
    finder = component.queryUtility(IIMSUserFinder)
    if finder is not None:
        result = finder.find(person)
    else:
        username = person.sourcedid.id.lower()
        result = User.get_user(username)
    return result


def get_username(person):
    finder = component.queryUtility(IIMSUserFinder)
    if finder is not None:
        result = finder.username(person)
    else:
        result = person.sourcedid.id.lower()
        if result.endswith('@nextthought.com'):
            result = result[:-16]
    return result


def create_user(username, email, realname=None, meta=None):
    args = {u'username': username}
    ext_value = {u'email': email}
    if realname:
        ext_value['realname'] = realname
    args['external_value'] = ext_value

    meta_data = {u'check_verify_email': False}
    meta_data.update(meta or {})
    args[u'meta_data'] = meta_data
    user = User.create_user(**args)
    return user


def get_or_create_person_user(person):
    created = False
    user = find_user(person)
    userid = get_username(person)
    email = get_person_email(person)
    user = User.get_user(userid) if user is None else user
    if user is None:
        mutil = component.queryUtility(IIMSUserCreationMetadata)
        meta = mutil.data(person) if mutil is not None else None
        realname = person.name if person.name else None
        user = create_user(userid, email, realname, meta)
        notify(IMSUserCreatedEvent(user, person))
        created = True
    return user, created


def create_users(source):
    result = {}
    if IEnterprise.providedBy(source):
        ims = source
    else:
        ims = Enterprise.parseFile(source)

    for person in ims.get_persons():
        userid = get_username(person)
        person_userid = get_person_userid(person)
        _, created = get_or_create_person_user(person)
        if created:
            result[userid] = person_userid
    return result


def find_ims_courses():
    catalog = component.queryUtility(IIMSCourseCatalog)
    result = catalog.courses() if catalog is not None else {}
    return result


def has_assigments_submitted(course, user):
    try:
        from nti.app.assessment.common import has_assigments_submitted
        result = has_assigments_submitted(course, user)
    except ImportError:
        result = False
    return result


def drop_enrollments(context, user):
    result = []
    dropped_courses = drop_any_other_enrollments(context, user)
    for course in dropped_courses:
        entry = ICourseCatalogEntry(course)
        if has_assigments_submitted(course, user):
            logger.warn("User %s has submitted to course '%s'", user,
                        entry.ProviderUniqueID)
        result.append(entry)
    return result


def update_member_enrollment_status(course_instance, person, role,
                                    enrrollment_info=None,
                                    move_info=None,
                                    drop_info=None):

    user = find_user(person)
    if user is None:
        logger.warn("User %s was not found", person)
        return

    username = user.username
    person_userid = get_person_userid(person)

    move_info = {} if move_info is None else move_info
    drop_info = {} if drop_info is None else drop_info
    enrrollment_info = {} if enrrollment_info is None else enrrollment_info

    enrollments = ICourseEnrollments(course_instance)
    enrollment_manager = ICourseEnrollmentManager(course_instance)
    enrollment = enrollments.get_enrollment_for_principal(user)

    instance_entry = ICourseCatalogEntry(course_instance)

    if role.status == ACTIVE_STATUS:
        # check any other enrollment
        for entry in drop_enrollments(course_instance, user):
            drop_info.setdefault(entry.ProviderUniqueID, {})
            drop_info[entry.ProviderUniqueID][username] = person_userid

        add_mod = True
        # The user should be enrolled for degree-seeking credit.
        if enrollment is None:
            # Never before been enrolled
            logger.info('User %s enrolled in %s',
                        user, instance_entry.ProviderUniqueID)
            enrollment = enrollment_manager.enroll(user,
                                                   scope=ES_CREDIT_DEGREE)
        elif enrollment.Scope != ES_CREDIT_DEGREE:
            logger.info('User %s upgraded to ForCredit in %s',
                        user, instance_entry.ProviderUniqueID)
            enrollment.Scope = ES_CREDIT_DEGREE
            lifecycleevent.modified(enrollment)
        else:
            add_mod = False

        # record enrollment
        if add_mod:
            enrrollment_info.setdefault(instance_entry.ProviderUniqueID, {})
            enrrollment_info[instance_entry.ProviderUniqueID][username] = person_userid
    elif role.status == INACTIVE_STATUS:
        # if enrolled but the course is not public then drop it
        if enrollment is not None:
            if INonPublicCourseInstance.providedBy(course_instance) \
                    or ICourseSubInstance.providedBy(course_instance):
                logger.info('User %s dropping course %s',
                            user, instance_entry.ProviderUniqueID)
                enrollment_manager.drop(user)
                enrollment = None

                # record drop
                drop_info.setdefault(instance_entry.ProviderUniqueID, {})
                drop_info[instance_entry.ProviderUniqueID][username] = person_userid

            elif enrollment.Scope != ES_PUBLIC:
                logger.info('User %s moving to PUBLIC version of %s',
                            user, instance_entry.ProviderUniqueID)
                # The user should not be enrolled for degree-seeking credit,
                # but if they were already enrolled they should remain
                # as publically enrolled
                enrollment.Scope = ES_PUBLIC
                lifecycleevent.modified(enrollment)

                # record move
                move_info.setdefault(instance_entry.ProviderUniqueID, {})
                move_info[instance_entry.ProviderUniqueID][username] = person_userid

        # set in an open enrollment
        if      enrollment is not None \
            and enrollment.Scope != ES_PUBLIC \
            and not is_there_an_open_enrollment(course_instance, user):
            open_course = course_instance

            # if section and non public get main course
            if      ICourseSubInstance.providedBy(course_instance) \
                and INonPublicCourseInstance.providedBy(course_instance):
                open_course = get_parent_course(course_instance)

            # do open enrollment
            if      not INonPublicCourseInstance.providedBy(open_course) \
                and not IDenyOpenEnrollment.providedBy(open_course):
                enrollments = ICourseEnrollments(open_course)
                enrollment = enrollments.get_enrollment_for_principal(user)
                if enrollment is None:
                    enrollment_manager = ICourseEnrollmentManager(open_course)
                    enrollment = enrollment_manager.enroll(
                        user, scope=ES_PUBLIC)

                    # log public enrollment
                    entry = ICourseCatalogEntry(open_course)
                    logger.info('User %s enolled to PUBLIC version of %s',
                                user, entry.ProviderUniqueID)

                    # record
                    enrrollment_info.setdefault(entry.ProviderUniqueID, {})
                    enrrollment_info[entry.ProviderUniqueID][username] = person_userid
            else:
                logger.warn('User %s was not enolled to any PUBLIC version of course',
                            user)
    else:
        raise NotImplementedError("Unknown status", role.status)

    # return enrollment
    return enrollment


def cmp_proxy(x, y):
    x_sort_status = 1 if x.is_active else 0
    y_sort_status = 1 if y.is_active else 0
    result = cmp(x_sort_status, y_sort_status)
    if result == 0:
        result = cmp((x.course_id, x.sourcedid), (y.course_id, y.sourcedid))
    return result


def get_person(ims, member):
    person = ims.get_person(member.id)
    if person is None:
        logger.warn("Person definition for %s was not found", member.id)
        person = create_proxy_person(member)
    return person


def get_course(member, ims_courses, warns=()):
    course_id = member.course_id.id
    context = ims_courses.get(course_id)
    course_instance = ICourseInstance(context, None)
    if course_instance is None:
        if course_id not in warns:
            warns.add(course_id)
            logger.warn("Course definition for %s was not found",
                        course_id)
    return course_instance


def skip_record(member, cache):
    status = member.role.status
    if status == INACTIVE_STATUS:  # drop
        # check for an enrollment op in the same course, since the enrollment
        # process drops any other enrollment in the course
        key = "%s,%s,%s" % (member.course_id.id,
                            member.sourcedid.id, ACTIVE_STATUS)
        return key in cache
    return False


def drop_missing_credit_students(course, enrollments=()):
    result = set()
    # transform list of enrollments
    master = set()
    for record in enrollments or ():
        principal = IPrincipal(record, None)
        if principal is not None:  # bad enrollment
            master.add(principal.id.lower())
    # drop enrollments for credit students not in master
    course_enrollments = ICourseEnrollments(course)
    enrollment_manager = ICourseEnrollmentManager(course)
    for record in list(course_enrollments.iter_enrollments()):
        drop = False
        principal = IPrincipal(record, None)
        if principal is None:  # bad enrollment
            drop = True
        elif    not principal.id.lower() in master \
            and record.Scope == ES_CREDIT_DEGREE:
            drop = True
        if drop:
            enrollment_manager.drop(principal)
            result.add(principal)
    # return drop principals
    result.discard(None)
    return result


def process(ims_file, create_persons=False, drop_missing=False):
    """
    Process an IMS file feed
    :param: ims_file: File feed
    :param: bool create_persons: Create the users in the feed flag
    :param: bool drop_missing: Drop missing credit students
    """
    # check for the old calling convention
    assert isinstance(create_persons, bool)
    ims = Enterprise.parseFile(ims_file)
    ims_courses = find_ims_courses()

    # create users
    created_users = create_users(ims) if create_persons else ()

    warns = set()
    moves = LocatedExternalDict()
    drops = LocatedExternalDict()
    errollment = LocatedExternalDict()

    # simple closure to populate cache
    cache = CaseInsensitiveDict()

    def populate(member):
        key = "%s,%s,%s" % (member.course_id.id,
                            member.sourcedid.id,
                            member.role.status)
        cache[key] = member
        return member

    enrollments = defaultdict(list)
    # sort members (drops come first)
    members = sorted(ims.get_all_members(populate), cmp=cmp_proxy)
    for member in members:

        # instructors should be auto-created.
        if member.is_instructor:
            continue

        person = get_person(ims, member)
        course_instance = get_course(member, ims_courses, warns)
        if course_instance is None:
            continue

        if skip_record(member, cache):
            continue

        sourcedid = member.course_id
        sid = get_course_sourcedid(course_instance)
        if sid != sourcedid:
            set_course_sourcedid(course_instance, sourcedid)

        enrollment = update_member_enrollment_status(course_instance,
                                                     person, member.role,
                                                     errollment, moves, drops)
        if enrollment is not None:
            enrollments[course_instance].append(enrollment)

    if drop_missing:
        for course, values in enrollments.items():
            principals = drop_missing_credit_students(course, values)
            entry = ICourseCatalogEntry(course)
            drops.setdefault(entry.ProviderUniqueID, {})
            for principal in principals or ():
                principal = IPrincipal(principal)
                drops[entry.ProviderUniqueID][principal.id] = principal.id

    result = LocatedExternalDict()
    result['Drops'] = drops
    result['Moves'] = moves
    result['Enrollment'] = errollment
    result['CreatedUsers'] = created_users
    return result
