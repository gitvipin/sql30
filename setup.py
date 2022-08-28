#!/usr/bin/env python

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

version = {}
with open("sql30/__init__.py") as fp:
    exec(fp.read(), version)


setuptools.setup(
    name="sql30",
    version=version['__version__'],
    author="Vipin Sharma",
    author_email="sh.vipin@gmail.com",
    description="A zero, 0, weight ORM for sqlite3 database.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gitvipin/sql30",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    package_data={
        'sql30.templates': ['*']
        }
)
