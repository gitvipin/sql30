#!/usr/bin/env python
# Copyright (c) 2020 Vipin Sharma. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
'''
A simple REST interface for reading SQLite Database.
'''

import argparse
import signal
import sys

from sql30 import db

DB_NAME = None

class DummyDB(db.Model):
    DB_NAME = DB_NAME

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-d', '--database', action="store_const",
        help="Name of database.")
    parser.add_argument(
        '-l', '--location', action="store_const",
        required=True,help="Location of DB file.")
    parser.add_argument(
        '-p', '--port', nargs='+',
        help="Port to connect")
    parser.add_argument(
        '-v', '--verbose', action="store_true",
        help="Verbose mode")

    args = parser.parse_args()

    verbose = bool(args.verbose)

    global DB_NAME
    DB_NAME = args.location

    def signal_handler(sig, frame):
        # TODO :
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)


if __name__ == '__main__':
    main()