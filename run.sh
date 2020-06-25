#!/bin/sh

# Simple script that helps in pushing the package on pypi

# Remove existing build
rm -rf dist build

# Build packages
python3 setup.py sdist bdist_wheel

# Upload packages.
python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
python3 -m twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

git clean -fX
git checkout .


