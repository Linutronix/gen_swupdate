# Copyright (c) 2017-2020 Linutronix GmbH
#
# SPDX-License-Identifier: MIT

from setuptools import setup

with open('README.rst') as f:
    readme = f.read()

setup(
    name='gen_swupdate',
    version='0.4',
    description="SWUpdate SWU file generator",
    long_description=readme,
    author="Linutronix GmbH",
    author_email="info@linutronix.de",
    license="MIT",
    py_modules=['gen_swupdate'],
    install_requires=['libconf'],
    entry_points={'console_scripts': ['gen_swupdate = gen_swupdate:main']},
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ]
)
