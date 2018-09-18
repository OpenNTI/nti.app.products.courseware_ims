#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import csv
import sys
import argparse

import simplejson as json

import six

from nti.app.products.courseware_ims import workflow

from nti.dataserver.utils import run_with_dataserver

from nti.dataserver.utils.base_script import set_site
from nti.dataserver.utils.base_script import create_context

logger = __import__('logging').getLogger(__name__)


def _tx_string(s):
    if s and isinstance(s, six.text_type):
        s = s.encode('utf-8')
    return s


def _process_args(ims_file, create_persons, site=None, output=None,
                  as_csv=False, drop_missing=False, verbose=False):
    set_site(site)
    response = workflow.process(ims_file, create_persons, drop_missing)
    if output and response:
        with open(output, "wb") as fp:
            if not as_csv:
                json.dump(response, fp, indent=4, encoding="utf-8")
            else:
                header = ['Course', 'Operation', 'Username', 'PersonID']
                csv_writer = csv.writer(fp)
                csv_writer.writerow(header)

                def _write_operation(m, operation):
                    for course in sorted(m.keys()):
                        users = m[course]
                        for username in sorted(users.keys()):
                            personid = users[username]
                            data = [course, operation, username, personid]
                            csv_writer.writerow([_tx_string(x) for x in data])
                _write_operation(response.get('Drops', {}), 'Drop')
                _write_operation(response.get('Moves', {}), 'Moves')
                _write_operation(response.get('Enrollment', {}), 'Enroll')
        if verbose:
            print("Output response saved at", output)


def main():
    arg_parser = argparse.ArgumentParser(description="Course enrollment")
    arg_parser.add_argument('-v', '--verbose', help="Be verbose", action='store_true',
                            dest='verbose')

    arg_parser.add_argument('-c', '--create', help="Create users", action='store_true',
                            dest='create_persons', default=False)

    arg_parser.add_argument('-d', '--drop', help="Drop missing", action='store_true',
                            dest='drop_missing')

    arg_parser.add_argument('-i', '--ims', help="IMS file location",
                            dest='ims_file')

    arg_parser.add_argument('-s', '--site', dest='site', help="Request site")

    arg_parser.add_argument('-o', '--output', dest='output',
                            help="Output response path")

    arg_parser.add_argument('--csv', dest='csv', action='store_true',
                            help="CSV output response")

    args = arg_parser.parse_args()

    verbose = args.verbose
    drop_missing = args.drop_missing

    ims_file = args.ims_file
    ims_file = os.path.expanduser(ims_file) if ims_file else None
    if not ims_file or not os.path.exists(ims_file):
        print('IMS file cannot be found', ims_file, file=sys.stderr)
        sys.exit(2)

    site = args.site
    if not site and verbose:
        print('WARN: NO site specified')

    create_persons = args.create_persons
    if create_persons and not site and verbose:
        print('WARN: Creating users with no site specified')

    as_csv = args.csv
    output = args.output
    output = os.path.expanduser(output) if output else None
    if output and os.path.exists(output) and os.path.isdir(output):
        ext = 'json' if not as_csv else 'csv'
        name = os.path.splitext(os.path.basename(ims_file))[0]
        output = os.path.join(output, '%s.%s' % (name, ext))

    env_dir = os.getenv('DATASERVER_DIR')
    conf_packages = ('nti.appserver',)
    context = create_context(env_dir, with_library=True)

    run_with_dataserver(environment_dir=env_dir,
                        verbose=verbose,
                        context=context,
                        minimal_ds=True,
                        xmlconfig_packages=conf_packages,
                        function=lambda: _process_args(site=site,
                                                       as_csv=as_csv,
                                                       output=output,
                                                       verbose=verbose,
                                                       ims_file=ims_file,
                                                       drop_missing=drop_missing,
                                                       create_persons=create_persons))


if __name__ == '__main__':
    main()
