import unittest
import os
from setuptools import setup
from distutils.core import Command

from versionedconfig import __version__

HERE = os.path.abspath(os.path.dirname(__file__))
README = os.path.join(HERE, "README.rst")

classifiers = [
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Natural Language :: English',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'Intended Audience :: Education',
    'Intended Audience :: Information Technology',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 3',
]

class RunVersionedConfigTests(Command):
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
    name='versionedconfig',
    version=__version__,
    description=('Easy versioned JSON config files'),
    long_description=long_description,
    url='http://github.com/eriknyquist/versionedconfig',
    author='Erik Nyquist',
    author_email='eknyquist@gmail.com',
    license='Apache 2.0',
    packages=['versionedconfig'],
    classifiers = classifiers,
    cmdclass={'test': RunVersionedConfigTests},
    include_package_data=True,
    zip_safe=False
)
