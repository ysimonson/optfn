#!/usr/bin/env python

from distutils.core import setup

with open('README.txt') as doc:
  long_description = doc.read()

setup(name='optfunc',
      version='1.0',
      description='Generate commandline flags from function arguments.',
      author='Simon Willison',
      author_email='simon@lanyrd.com',
      url='https://github.com/simonw/optfunc',
      license='BSD',
      classifiers=['Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Programming Language :: Python :: 2 :: Only',
                   'Environment :: Console',
                   'Development Status :: 5 - Production/Stable'],
      long_description=long_description,
      py_modules=['optfunc'])