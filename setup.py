#!/usr/bin/env python3
from distutils.core import setup
from setuptools import find_packages
version = '1.0.1'

setup(
    name='IntegraPy',
    version=version,
    description=u"Satel's Integra secrity hub interface",
    author='Marcin Korzonek & Michał Węgrzynek & al.',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    license='GNU General Public License',
    install_requires=[
        'bitarray'
    ]
)
