#!/usr/bin/env python
# Copyright (c) 2020 Vipin Sharma. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
"""Command-line interface for SQL30 database operations.

This module provides a command-line interface for SQL30 operations including:
- Starting HTTP servers to serve database contents as JSON or HTML
- Exporting database schemas to SQL files
- Database browsing and inspection

Following examples consider test_reviews.db as SQLITE
database file. -d option takes qualified path to DB file.

A sample file can be generated using the command:
    python3 -msql30.tests.sanity -x

USAGE:

    # Run HTTP Server serving data as JSON response
    python -msql30.cmd -s -p 8008 -d ./test_reviews.db

    # Run HTTP Server serving data as HTML response
    python -msql30.cmd -s -p 8008 -x -d ./test_reviews.db
    
    # Export database schema to SQL file
    python -msql30.cmd -e -d ./test_reviews.db -o backup.sql

Command Line Arguments:
    -d, --database: Name of database file (required)
    -e, --export: Export database as SQL schema
    -j, --json: Start server for JSON response
    -l, --location: Location of DB file
    -o, --output: Output schema file name (default: db.schema)
    -p, --port: Port to connect (default: 5649)
    -s, --server: Start HTTP Server for read-only requests
    -v, --verbose: Verbose mode
    -x, --html: Start server for HTML response
"""

import argparse
import os
import signal
import sys

from sql30 import db
from sql30 import api


class DummyDB(db.Model):
    """Dummy database model for command-line operations.
    
    This is a minimal database model class used by the command-line interface
    to perform operations on existing SQLite databases without requiring
    a predefined schema. It inherits from db.Model and uses the database
    schema discovery functionality to work with any SQLite database.
    
    Attributes:
        Inherits all attributes from db.Model.
    """
    pass


def main():
    """Main entry point for the SQL30 command-line interface.
    
    Parses command-line arguments and executes the requested operations:
    - Database schema export to SQL files
    - HTTP server startup for database browsing
    
    The function handles argument parsing, database path resolution,
    and delegates to appropriate functions based on the provided options.
    
    Raises:
        SystemExit: If required arguments are missing or invalid.
        AssertionError: If port number is invalid.
        FileNotFoundError: If database file is not found.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-d', '--database', help="Name of database.", required=True)
    parser.add_argument(
        '-e', '--export', action='store_true',
        help="Export database as SQL schema.")
    parser.add_argument(
        '-j', '--json', action="store_true",
        help="Start server for JSON response.")
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
    parser.add_argument(
        '-x', '--html', action="store_true",
        help="Start server for HTML response.")

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
        json_output = False if args.html else True
        assert int(args.port), "None or invalid port"
        server = api.start_server(db_path=db_path, port=int(args.port),
                                  json_output=json_output)


if __name__ == '__main__':
    main()
