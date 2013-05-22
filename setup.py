#!/usr/bin/env python

from distutils.core import setup

with open('README.md') as doc:
  long_description = doc.read()

setup(name='optfunc-ysimonson',
      version='0.1',
      description='Generate commandline flags from function arguments.',
      author='Simon Willison',
      author_email='simon@lanyrd.com',
      url='https://github.com/ysimonson/optfunc',
      license='BSD',
      classifiers=['Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Programming Language :: Python :: 2 :: Only',
                   'Environment :: Console',
                   'Development Status :: 5 - Production/Stable'],
      long_description=long_description,
      py_modules=['optfunc'])