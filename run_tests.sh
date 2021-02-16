#!/bin/sh

echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo "Running tests in python 3"
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo "Running tests in python 3"
python3 -m unittest discover -p "test_*.py" sql30/tests/ -v
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo "Running tests in python 2 "
python2 -m unittest discover -p "test_*.py" sql30/tests/ -v
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
