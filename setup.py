#-*- coding: utf-8 -*-
import os
import codecs
from distutils.core import setup
from setuptools import find_packages, findall

version = __import__('yasgg').get_version()
read = lambda filepath: codecs.open(filepath, 'r', 'utf-8').read()

print findall('yasgg/themes/')

setup(
    name='YASGG',
    version=version,
    url='https://github.com/nomnomnom/yasgg',
    author='nomnomnom',
    author_email='nomnomnom@secure-mail.cc',
    description=('YASGG is a static gallery generator with optional encryption support written in python.'),
    long_description=read(os.path.join(os.path.dirname(__file__), 'README.md')),
    license='Beer',
    packages=find_packages(),
    include_package_data=True,
    scripts=['yasgg/bin/yasggctl'],
)
