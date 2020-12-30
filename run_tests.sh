#!/bin/sh

echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo "Running tests in python 3"
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo "Running tests in python 3"
python3 -m unittest discover -p "*.py" sql30/tests/ -v
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo "Running tests in python 2- DIABLED"
# python2 -m unittest discover -p "*.py" sql30/tests/ -v
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
