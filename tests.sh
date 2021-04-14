#!/bin/sh

echo "===================================="
echo "Running tests using python 3"
echo "===================================="
python3 -m unittest discover -p "test_*.py" sql30/tests/ -v
python3 -m unittest discover -p testPath.py sql30/tests/ -v
python3 -m unittest discover -p sanity.py sql30/tests/ -v
echo "===================================="
echo ""
echo ""
echo ""
echo "===================================="
echo "Running tests in python 2 "
echo "===================================="
python2 -m unittest discover -p "test_*.py" sql30/tests/ -v
python2 -m unittest discover -p testPath.py sql30/tests/ -v
echo "===================================="
