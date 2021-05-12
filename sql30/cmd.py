#!/usr/bin/env python
# Copyright (c) 2020 Vipin Sharma. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
'''
A simple REST interface for reading SQLite Database.
'''

import argparse
import os
import signal
import sys

from sql30 import db
from sql30 import api


class DummyDB(db.Model):
    pass



def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-d', '--database', help="Name of database.", required=True)
    parser.add_argument(
        '-e', '--export', action='store_true',
        help="Export database as SQL schema.")
    parser.add_argument(
        '-l', '--location', action="store",
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

    _ = bool(args.verbose)

    if args.location:
        db_path = os.path.join(args.location, args.database)
    else:
        db_path = args.database

    db = DummyDB(db_name=db_path)
    db.fetch_schema()

    if args.export:
        db.export(dbfile=args.output)

    if args.server:
        assert int(args.port), "None or invalid port"
        server = api.start_server(db_path=db_path, port=int(args.port))


if __name__ == '__main__':
    main()
