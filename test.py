# This file is part of django-xmpp-http-upload (https://github.com/mathiasertl/django-xmpp-http-upload).
#
# django-xmpp-http-upload is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# django-xmpp-http-upload is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along with django-xmpp-http-upload. If
# not, see <http://www.gnu.org/licenses/>.

import argparse
import os
import subprocess
import sys

import coverage

import django
from django.core.management import call_command

_rootdir = os.path.dirname(os.path.realpath(__file__))
_suite_default = ['xmpp_http_upload']

parser = argparse.ArgumentParser(description="Run the test-suite.")
subparsers = parser.add_subparsers(help='commands', dest='command')
test_parser = subparsers.add_parser('test', help='Run the test suite.')
test_parser.add_argument('--no-coverage', dest='coverage', default=True, action='store_false',
                         help="Don't test code coverage.")
test_parser.add_argument('test_label', nargs='*', default=_suite_default,
                         help="Module paths to test (default: %s)." % ', '.join(_suite_default))
subparsers.add_parser('code-quality', help='Test code quality using flake8 and isort.')

args = parser.parse_args()


def run_tests(test_labels):
    work_dir = os.path.join(_rootdir, 'demo')
    os.chdir(work_dir)
    sys.path.insert(0, work_dir)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "demo.test_settings")

    django.setup()
    call_command('test', *test_labels)


if args.command == 'test':
    report_dir = os.path.join(_rootdir, 'build', 'coverage')

    if args.coverage:
        cov = coverage.Coverage(cover_pylib=False, branch=True,
                                source=['xmpp_http_upload'],
                                omit=['*migrations/*', '*/tests/tests*', ]
                                )
        cov.start()

    run_tests(args.test_label)

    if args.coverage:
        cov.stop()
        cov.save()
        cov.html_report(directory=report_dir)
elif args.command == 'code-quality':
    files = ['xmpp_http_upload', 'setup.py', 'test.py']

    isort = ['isort', '--check-only', '--diff', '-rc'] + files
    print(' '.join(isort))
    subprocess.run(isort, check=True)

    flake8 = ['flake8'] + files
    print(' '.join(flake8))
    subprocess.run(flake8, check=True)

    check = ['python', '-Wd', 'demo/manage.py', 'check']
    print(' '.join(check))
    subprocess.run(check, check=True)
