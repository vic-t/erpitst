# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in itst/__init__.py
from itst import __version__ as version

setup(
	name='itst',
	version=version,
	description='ITST',
	author='ITST',
	author_email='vt@itst.ch',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
