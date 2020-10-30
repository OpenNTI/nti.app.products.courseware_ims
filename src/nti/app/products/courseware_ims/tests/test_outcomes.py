#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from hamcrest import is_
from hamcrest import none
from hamcrest import not_none
from hamcrest import assert_that
from hamcrest import contains_string

from pyramid.testing import DummyRequest

from zope import component

from zope.intid.interfaces import IIntIds

from nti.app.products.courseware.tests import InstructedCourseApplicationTestLayer

from nti.app.products.courseware_ims.interfaces import ILTIOutcomesResultSourcedIDUtility

from nti.app.products.courseware_ims.lti import LTIExternalToolAsset

from nti.app.products.ims.interfaces import ILTIRequest

from nti.app.products.ims.outcomes import ResultSourcedId

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.contenttypes.completion.interfaces import IProgress
from nti.contenttypes.completion.interfaces import ICompletionContextCompletionPolicyContainer

from nti.contenttypes.completion.policies import CompletableItemAggregateCompletionPolicy

from nti.contenttypes.completion.utils import get_completed_item

from nti.contenttypes.courses.courses import CourseInstance

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.dataserver.users import User

from nti.ims.lti.interfaces import IOutcomeRequest
from nti.ims.lti.interfaces import IOutcomeService

logger = __import__('logging').getLogger(__name__)


delete_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <imsx_POXEnvelopeRequest xmlns="http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">
        <imsx_POXHeader>
          <imsx_POXRequestHeaderInfo>
            <imsx_version>V1.0</imsx_version>
            <imsx_messageIdentifier>999999123</imsx_messageIdentifier>
          </imsx_POXRequestHeaderInfo>
        </imsx_POXHeader>
        <imsx_POXBody>
          <deleteResultRequest>
            <resultRecord>
              <sourcedGUID>
                <sourcedId>3124567</sourcedId>
              </sourcedGUID>
            </resultRecord>
          </deleteResultRequest>
        </imsx_POXBody>
        </imsx_POXEnvelopeRequest>
        """


read_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <imsx_POXEnvelopeRequest xmlns="http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">  <imsx_POXHeader>
        <imsx_POXRequestHeaderInfo>
          <imsx_version>V1.0</imsx_version>
          <imsx_messageIdentifier>999999123</imsx_messageIdentifier>
        </imsx_POXRequestHeaderInfo>
        </imsx_POXHeader>
        <imsx_POXBody>
        <readResultRequest>
          <resultRecord>
            <sourcedGUID>
              <sourcedId>3124567</sourcedId>
            </sourcedGUID>
          </resultRecord>
        </readResultRequest>
        </imsx_POXBody>
        </imsx_POXEnvelopeRequest>
        """


replace_xml_fmt = """<?xml version="1.0" encoding="UTF-8"?>
        <imsx_POXEnvelopeRequest xmlns="http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">
        <imsx_POXHeader>
          <imsx_POXRequestHeaderInfo>
            <imsx_version>V1.0</imsx_version>
            <imsx_messageIdentifier>999999123</imsx_messageIdentifier>
          </imsx_POXRequestHeaderInfo>
        </imsx_POXHeader>
        <imsx_POXBody>
          <replaceResultRequest>
            <resultRecord>
              <sourcedGUID>
                <sourcedId>3124567</sourcedId>
              </sourcedGUID>
              <result>
                <resultScore>
                  <language>en</language>
                  <textString>%s</textString>
                </resultScore>
              </result>
            </resultRecord>
          </replaceResultRequest>
        </imsx_POXBody>
        </imsx_POXEnvelopeRequest>
        """


class TestOutcomes(ApplicationLayerTest):
    layer = InstructedCourseApplicationTestLayer

    @WithMockDSTrans
    def test_asset_outcomes(self):
        """
        Validate the course outcome service all the way to progress/completion.

        Note we may get a partial score rom the TP. Therefore we do not attempt
        to say the asset is `Completed` but unsuccessfully (success=False).
        """
        intids = component.getUtility(IIntIds)
        asset = LTIExternalToolAsset()
        asset.ntiid = u'tag:nextthought.com,2011:test'
        user = User.create_user(username='test_user', dataserver=self.ds)
        course = CourseInstance()
        connection = mock_dataserver.current_transaction
        intids.register(course)
        connection.add(course)
        intids.register(asset)
        connection.add(asset)

        # Validate going from sourcedid to utility
        sourcedid_utility = component.getUtility(ILTIOutcomesResultSourcedIDUtility)
        sourcedid_str = sourcedid_utility.build_sourcedid(user, course, asset)
        sourcedid = ResultSourcedId(lis_result_sourcedid=sourcedid_str)
        assert_that(sourcedid, not_none())
        assert_that(sourcedid.lis_result_sourcedid, not_none())

        outcome_service = IOutcomeService(sourcedid, None)
        assert_that(outcome_service, not_none())
        assert_that(outcome_service.course, is_(course))
        assert_that(outcome_service.user, is_(user))
        assert_that(outcome_service.asset, is_(asset))

        # Base case, no score yet
        delete_request = DummyRequest()
        delete_request.body = delete_xml
        delete_lti_request = ILTIRequest(delete_request)
        delete_proxy = IOutcomeRequest(delete_lti_request)
        delete_proxy.lis_result_sourcedid = sourcedid_str
        response = delete_proxy()
        response.generate_response_xml()

        # Base case, no score yet
        read_request = DummyRequest()
        read_request.body = read_xml
        read_lti_request = ILTIRequest(read_request)
        read_proxy = IOutcomeRequest(read_lti_request)
        read_proxy.lis_result_sourcedid = sourcedid_str
        response = read_proxy()
        response_xml = response.generate_response_xml()
        assert_that(response_xml, contains_string('<textString>None</textString>'))

        completed_item = get_completed_item(user, course, asset)
        assert_that(completed_item, none())

        # Score of .8
        replace_request = DummyRequest()
        replace_request.body = replace_xml_fmt % '.8'
        replace_lti_request = ILTIRequest(replace_request)
        replace_proxy = IOutcomeRequest(replace_lti_request)
        replace_proxy.lis_result_sourcedid = sourcedid_str
        response = replace_proxy()
        response_xml = response.generate_response_xml()
        assert_that(response_xml, contains_string('<imsx_codeMajor>success</imsx_codeMajor>'))

        completed_item = get_completed_item(user, course, asset)
        assert_that(completed_item, none())

        # Set a asset completion policy of .7
        seventy_perc_policy = CompletableItemAggregateCompletionPolicy(percentage=.7)
        policy_container = ICompletionContextCompletionPolicyContainer(course)
        policy_container[asset.ntiid] = seventy_perc_policy

        # Still no completed item
        completed_item = get_completed_item(user, course, asset)
        assert_that(completed_item, none())

        # Update grade to .7 - with policy in place, we are now complete
        replace_request.body = replace_xml_fmt % '.7'
        replace_lti_request = ILTIRequest(replace_request)
        replace_proxy = IOutcomeRequest(replace_lti_request)
        replace_proxy.lis_result_sourcedid = sourcedid_str
        response = replace_proxy()
        response_xml = response.generate_response_xml()
        assert_that(response_xml, contains_string('<imsx_codeMajor>success</imsx_codeMajor>'))

        completed_item = get_completed_item(user, course, asset)
        assert_that(completed_item, none())

        # Now make sure our asset specifies outcomes
        asset.has_outcomes = True
        response = replace_proxy()
        response_xml = response.generate_response_xml()
        assert_that(response_xml, contains_string('<imsx_codeMajor>success</imsx_codeMajor>'))
        completed_item = get_completed_item(user, course, asset)
        assert_that(completed_item, not_none())
        assert_that(completed_item.ItemNTIID, is_(asset.ntiid))
        assert_that(completed_item.CompletedDate, not_none())
        assert_that(completed_item.Success, is_(True))

        progress = component.queryMultiAdapter((user, asset, course),
                                               IProgress)
        assert_that(progress.AbsoluteProgress, is_(.7))
        assert_that(progress.MaxPossibleProgress, is_(1))
        assert_that(progress.HasProgress, is_(True))
        assert_that(progress.NTIID, is_(asset.ntiid))

        # Read now returns .7
        response = read_proxy()
        response_xml = response.generate_response_xml()
        assert_that(response_xml, contains_string('<textString>0.7</textString>'))

        # Delete removes progress
        delete_proxy()
        completed_item = get_completed_item(user, course, asset)
        assert_that(completed_item, none())
        progress = component.queryMultiAdapter((user, asset, course),
                                               IProgress)
        assert_that(progress.AbsoluteProgress, is_(0))
        assert_that(progress.MaxPossibleProgress, is_(1))
        assert_that(progress.HasProgress, is_(False))
        assert_that(progress.NTIID, is_(asset.ntiid))

        # Now we get a score less than threshold
        replace_request = DummyRequest()
        replace_request.body = replace_xml_fmt % '.69'
        replace_lti_request = ILTIRequest(replace_request)
        replace_proxy = IOutcomeRequest(replace_lti_request)
        replace_proxy.lis_result_sourcedid = sourcedid_str
        response = replace_proxy()
        response_xml = response.generate_response_xml()
        assert_that(response_xml, contains_string('<imsx_codeMajor>success</imsx_codeMajor>'))
        completed_item = get_completed_item(user, course, asset)
        assert_that(completed_item, none())

        # Read now returns .69
        response = read_proxy()
        response_xml = response.generate_response_xml()
        assert_that(response_xml, contains_string('<textString>0.69</textString>'))

        # Invalid score changes no state
        replace_request = DummyRequest()
        replace_request.body = replace_xml_fmt % '1.001'
        replace_lti_request = ILTIRequest(replace_request)
        replace_proxy = IOutcomeRequest(replace_lti_request)
        replace_proxy.lis_result_sourcedid = sourcedid_str
        response = replace_proxy()
        response_xml = response.generate_response_xml()
        assert_that(response_xml, contains_string('<imsx_codeMajor>failure</imsx_codeMajor>'))
        completed_item = get_completed_item(user, course, asset)
        assert_that(completed_item, none())

        response = read_proxy()
        response_xml = response.generate_response_xml()
        assert_that(response_xml, contains_string('<textString>0.69</textString>'))
