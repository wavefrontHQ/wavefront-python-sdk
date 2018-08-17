# coding: utf-8

"""
    Wavefront Python SDK
    <p>This is a Wavefront Python SDK</p>  # noqa: E501
"""

from setuptools import setup, find_packages  # noqa: H301

NAME = "wavefront_python_sdk"
VERSION = "0.1.0"
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = ['requests >= 2.18.4']

setup(
    name=NAME,
    version=VERSION,
    description="Wavefront Python SDK",
    author_email="songhao@vmware.com",
    url="https://github.com/wavefrontHQ/wavefront-python-sdk/tree/master/wavefront-python-sdk",
    keywords=["Wavefront SDK", "Wavefront"],
    install_requires=REQUIRES,
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
    long_description="""\
    """
)
