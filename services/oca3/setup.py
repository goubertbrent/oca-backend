# coding: utf-8

import sys
from setuptools import setup, find_packages

NAME = "oca"
VERSION = "1.0.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = [
    "connexion>=2.0.2",
    "swagger-ui-bundle>=0.0.2",
    "python_dateutil>=2.6.0"
]

setup(
    name=NAME,
    version=VERSION,
    description="Our City App",
    author_email="",
    url="",
    keywords=["OpenAPI", "Our City App"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['openapi/openapi.yaml']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['oca=oca.__main__:main']},
    long_description="""\
    Our City App internal apis
    """
)

