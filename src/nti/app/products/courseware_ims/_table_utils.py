#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from z3c.table import column
from z3c.table import table

from zope.publisher.interfaces.browser import IBrowserRequest

from nti.app.authentication import get_remote_user

from nti.dataserver import authorization as nauth

from nti.dataserver.authorization_acl import has_permission

from nti.externalization.oids import to_external_ntiid_oid


class LTIToolsTable(table.Table):

    batchSize = 25
    startBatchingAt = 25
    sortOn = None

    def batchRows(self):
        try:
            super(LTIToolsTable, self).batchRows()
        except IndexError:
            self.batchStart = len(self.rows) - self.getBatchSize()
            super(LTIToolsTable, self).batchRows()


class TitleColumn(column.Column):
    weight = 1
    header = u'Title'

    def renderCell(self, tool):
        return tool.__name__


class DescriptionColumn(column.Column):
    weight = 2
    header = u'Description'

    def renderCell(self, tool):
        return tool.description


class KeyColumn(column.Column):
    weight = 3
    header = u'Consumer Key'

    def renderCell(self, tool):
        return tool.consumer_key


class SecretColumn(column.Column):
    weight = 4
    header = u'Secret'

    def renderCell(self, tool):
        return tool.secret


class DeleteColumn(column.Column):
    weight = 5
    buttonTitle = 'DELETE'
    header = u'Delete'

    def _onsubmit(self, item):
        msg = "'Are you sure you want to delete the tool %s?'" % item.title
        return 'onclick="return confirm(%s)"' % msg

    def renderCell(self, item):
        user = get_remote_user(self.request)

        # if not has_permission(nauth.ACT_DELETE, item, user):
        #     return ''
        from IPython.core.debugger import Tracer;Tracer()()
        action_url = self.request.resource_url(self.context, '@@delete_lti_tool')
        return """<form action="%s" method="post">
                    <input type="hidden" name="tool_name" value=%s>
                    <button type="submit">%s</button>
				  </form>"""\
               % (action_url, item.__name__, self.buttonTitle)


def make_specific_table(tableClassName, container, request):

    the_table = tableClassName(container, IBrowserRequest(request))

    try:
        the_table.update()
    except IndexError:
        the_table.batchStart = len(the_table.rows) - the_table.getBatchSize()
        the_table.update()

    return the_table

