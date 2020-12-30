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


class DummyDB(db.Model):
    pass


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-d', '--database', help="Name of database.")
    parser.add_argument(
        '-e', '--export', action='store_true',
        help="Export database as SQL schema.")
    parser.add_argument(
        '-l', '--location', action="store", required=True,
        help="Location of DB file.")
    parser.add_argument(
        '-o', '--output', default='db.schema',
        help="Output schema file name")
    parser.add_argument(
        '-p', '--port', default=5649, help="Port to connect")
    parser.add_argument(
        '-s', '--server', action='store_true',
        help="Start HTTP Server to host (read only) requests.")
    parser.add_argument(
        '-v', '--verbose', action="store_true",
        help="Verbose mode")

    args = parser.parse_args()

    verbose = bool(args.verbose)

    db = DummyDB(db_name=args.location)
    db.fetch_schema()

    import pdb ; pdb.set_trace()
    if args.export:
        db.export(dbfile=args.output)

    def signal_handler(sig, frame):
        # TODO :
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)


if __name__ == '__main__':
    main()