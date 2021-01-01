#!/usr/bin/env python
# Copyright (c) 2020 Vipin Sharma. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
"""
This module serves SQLITE database data as JSON through HTTP server.
"""
import json

from sys import argv
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

from sql30 import db

DBPATH = None


class SQL30Handler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def do_HEAD(self):
        self._set_headers()

    # GET sends back a Hello world message
    def do_GET(self):
        self._set_headers()
        if not self.path or self.path == '/':
            response = json.dumps({'hello': 'world', 'received': 'ok'})
        else:
            response = self._get_records()

        response = bytes(response, 'utf-8')
        self.wfile.write(response)

    def _get_records(self):
        class DummyDB(db.Model):
            pass

        with DummyDB(db_name=DBPATH) as dummydb:
            dummydb.fetch_schema()
            path = self.path.split('/')
            tidx = path.index('tables')
            dummydb.table = path[tidx+1]
            records = dummydb.read()
            return json.dumps(records)


def run(db_path, server=ThreadingHTTPServer, handler=SQL30Handler, port=8008):
    global DBPATH
    DBPATH = db_path

    server_address = ('', port)
    httpd = server(server_address, handler)

    print('Starting httpd on port %d...' % port)
    httpd.serve_forever()


if __name__ == "__main__":
    if len(argv) >= 2:
        run(argv[1], port=int(argv[2]))
    else:
        run(None)
