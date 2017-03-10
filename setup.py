# -*- coding: utf-8 -*-
#
# This file is part of django-xmpp-http-upload
# (https://github.com/mathiasertl/django-xmpp-http-upload).
#
# django-xmpp-http-upload is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# django-xmpp-http-upload is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# django-xmpp-http-upload.  If not, see <http://www.gnu.org/licenses/>.

import os
import subprocess
import sys

from distutils.cmd import Command
from setuptools import find_packages
from setuptools import setup

_rootdir = os.path.dirname(os.path.realpath(__file__))
version = '0.5.0'
requires = [
    'Django>=1.8',
    'djangorestframework>=3.5',
]


class BaseCommand(Command):
    user_options = [
        ('suite=', None, 'Testsuite to run', )
    ]

    def initialize_options(self):
        self.suite = ''

    def finalize_options(self):
        pass

    def run_tests(self):
        work_dir = os.path.join(_rootdir, 'demo')
        os.chdir(work_dir)
        sys.path.insert(0, work_dir)
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "demo.test_settings")

        import django
        django.setup()

        suite = 'xmpp_http_upload'
        if self.suite:
            if self.suite.startswith('xmpp_http_upload'):
                suite = self.suite
            else:
                suite += '.tests.%s' % self.suite

        from django.core.management import call_command
        call_command('test', suite)


class TestCommand(BaseCommand):
    description = 'Run the test-suite for django-xmpp-http-upload'

    def run(self):
        self.run_tests()


class CoverageCommand(BaseCommand):
    description = 'Generate test-coverage for django-ca.'

    def run(self):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "demo.test_settings")

        work_dir = os.path.join(_rootdir, 'demo')
        report_dir = os.path.join(_rootdir, 'build', 'coverage')
        os.chdir(work_dir)

        import coverage

        cov = coverage.Coverage(cover_pylib=False, branch=True,
                                source=['xmpp_http_upload'],
                                omit=['*migrations/*', '*/tests/tests*', ]
                                )
        cov.start()

        self.run_tests()

        cov.stop()
        cov.save()

        cov.html_report(directory=report_dir)


class QualityCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        proj = 'xmpp_http_upload'
        print('isort --check-only --diff -rc %s setup.py' % proj)
        status = subprocess.call(['isort', '--check-only', '--diff', '-rc', proj, 'setup.py'])
        if status != 0:
            sys.exit(status)

        print('flake8 %s fabfile.py setup.py' % proj)
        status = subprocess.call(['flake8', proj, 'setup.py'])
        if status != 0:
            sys.exit(status)

        work_dir = os.path.join(_rootdir, proj)

        os.chdir(work_dir)
        sys.path.insert(0, work_dir)

        import django

        # This does not import settings.py but instead loads our own settings
        from django.conf import settings
        settings.configure(DEBUG=True)
        django.setup()

        from django.core.management import call_command
        print('python ca/manage.py check')
        call_command('check')


setup(
    name='django-xmpp-http-upload',
    version=version,
    description='Provides XEP-0363: HTTP File Upload',
    author='Mathias Ertl',
    author_email='mati@jabber.at',
    url='https://github.com/mathiasertl/django-xmpp-http-upload',
    install_requires=requires,
    license="GNU General Public License (GPL) v3",
    packages=find_packages(),
    cmdclass={
        'coverage': CoverageCommand,
        'test': TestCommand,
        'code_quality': QualityCommand,
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Communications :: File Sharing",
    ],
    long_description="""A Django app providing the http-based functionality for
`XEP-0363: HTTP File Upload <http://www.xmpp.org/extensions/xep-0363.html>`_."""
)
