# This file is part of django-xmpp-http-upload (https://github.com/mathiasertl/django-xmpp-http-upload).
#
# django-xmpp-http-upload is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# django-xmpp-http-upload is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU General Public License along with django-xmpp-http-upload. If
# not, see <http://www.gnu.org/licenses/>.

from setuptools import find_packages
from setuptools import setup

version = '1.0.0'
requires = [
    'Django>=2.2',
    'djangorestframework>=3.9',
]

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
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Communications :: File Sharing",
    ],
    long_description="""A Django app providing the http-based functionality for
`XEP-0363: HTTP File Upload <http://www.xmpp.org/extensions/xep-0363.html>`_."""
)
