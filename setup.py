#!/usr/bin/env python

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sql30",
    version="0.0.1",
    author="Vipin Sharma",
    author_email="sh.vipin@gmail.com",
    description="A ZERO '0' weight ORM for sqlite3 database.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gitvipin/sql30",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD-2 License",
        "Operating System :: OS Independent",
    ],
)
