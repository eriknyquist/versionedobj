import unittest
import os
from setuptools import setup
from distutils.core import Command

from versionedobj import __version__

HERE = os.path.abspath(os.path.dirname(__file__))
README = os.path.join(HERE, "README.rst")

class RunVersionedObjTests(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        suite = unittest.TestLoader().discover("tests")
        t = unittest.TextTestRunner(verbosity = 2)
        t.run(suite)

with open(README, 'r') as f:
    long_description = f.read()

setup(
    name='versionedobj',
    version=__version__,
    description=('Easy object serialization & versioning framework'),
    long_description=long_description,
    url='http://github.com/eriknyquist/versionedobj',
    author='Erik Nyquist',
    author_email='eknyquist@gmail.com',
    license='Apache 2.0',
    packages=['versionedobj'],
    cmdclass={'test': RunVersionedObjTests},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.7",
    keywords=[
        "serialization",
        "json",
        "api",
        "marshal",
        "marshalling",
        "deserialization",
        "validation",
        "schema"
    ],
    classifiers=[
        "Classifier: Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    project_urls={
        "Documentation": "https://eriknyquist.github.io/versionedobj",
        "Issues": "https://github.com/eriknyquist/versionedobj/issues",
        "Contributions": "https://eriknyquist.github.io/versionedobj/#contributions"
    }
)
