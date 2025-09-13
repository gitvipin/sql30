#!/usr/bin/env python
# Copyright (c) 2020 Vipin Sharma. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
"""
This module serves SQLITE database data as JSON through HTTP server.
"""
import json
import os
import platform
import signal
import sys

from sys import argv
from http.server import BaseHTTPRequestHandler

IS_PYTHON2 = not platform.python_version().startswith('3')

try:
    _ = ModuleNotFoundError
except Exception:   # Python 3.6 and before.
    class ModuleNotFoundError(Exception):
        pass

try:
    from http.server import ThreadingHTTPServer
except (ModuleNotFoundError, ImportError):
    # python 3.6 and before.
    import socketserver
    from http.server import HTTPServer
    class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
        pass

from sql30 import db

DBPATH = None


class SQL30Handler(BaseHTTPRequestHandler):
    """HTTP request handler for serving SQLite database contents as JSON.
    
    This handler processes HTTP requests to serve database table contents
    in JSON format. It expects requests to follow the pattern /tables/<table_name>
    to retrieve data from specific tables.
    
    Attributes:
        Inherits from BaseHTTPRequestHandler.
    """

    def get_content_type(self):
        """Get the content type for HTTP responses.
        
        Returns:
            str: The MIME type for JSON responses.
        """
        return 'application/json'

    def _set_headers(self):
        """Set HTTP response headers.
        
        Sets the content type and CORS headers for the response.
        """
        self.send_header('Content-type', self.get_content_type())
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def do_HEAD(self):
        """Handle HTTP HEAD requests.
        
        Responds to HEAD requests by setting appropriate headers
        without sending response body.
        """
        self._set_headers()

    def do_GET(self):
        """Handle HTTP GET requests.
        
        Processes GET requests to serve database contents:
        - Root path ('/') returns welcome message
        - Paths containing '/tables/' serve table data
        - Invalid paths return error messages
        
        Returns:
            JSON response with either welcome message, table data, or error.
        """
        if not self.path or self.path == '/':
            response, error = json.dumps(self.welcome()), None
        elif '/tables' not in self.path:
            response, error = "/tables/ is missing from path", True
        else:
            response, error = self._get_records()

        self.send_response(200 if not error else 400)
        self._set_headers()
        response = bytes(response, 'utf-8') if not IS_PYTHON2 else response
        self.wfile.write(response)

    def welcome(self):
        """Generate welcome message for root path requests.
        
        Returns:
            dict: Welcome message with status code.
        """
        return {'message': 'Welcome to SQL30', 'staus': 200}

    def _get_records(self):
        """Retrieve records from the specified database table.
        
        Parses the request path to extract table name and retrieves
        all records from that table including headers.
        
        Returns:
            tuple: (formatted_data, error_flag) where error_flag is None
                   for success or error message string for failure.
        """
        class DummyDB(db.Model):
            pass

        with DummyDB(db_name=DBPATH) as dummydb:
            try:
                dummydb.fetch_schema()
                path = self.path.split('/')
                try:
                    tidx = path.index('tables')
                except Exception:
                    return "Invalid path", True
                dummydb.table = path[tidx+1]
                records = dummydb.read(include_header=True)
                return self.format_output(records), None
            except Exception as err:
                return str(err), str(err)

    def format_output(self, data):
        """Format data as JSON string.
        
        Args:
            data: Data to be formatted as JSON.
            
        Returns:
            str: JSON-formatted string representation of the data.
        """
        return json.dumps(data)

class SQL30HandlerHTML(SQL30Handler):
    """HTTP request handler for serving SQLite database contents as HTML.
    
    This handler extends SQL30Handler to serve database table contents
    in HTML format instead of JSON. It generates HTML tables for better
    browser visualization of the data.
    
    Attributes:
        Inherits from SQL30Handler.
    """

    def welcome(self):
        """Generate HTML welcome page for root path requests.
        
        Returns:
            str: HTML content for the welcome page.
        """
        return '''
        <!DOCTYPE html>
        <html>
            <body>
            <h1>Welcome to SQL30</h1>
            </body>
        </html>
        '''
    def get_content_type(self):
        """Get the content type for HTML responses.
        
        Returns:
            str: The MIME type for HTML responses with UTF-8 encoding.
        """
        return 'text/html; charset=UTF-8'

    def format_output(self, records):
        """Format database records as HTML table.
        
        Reads the HTML template file and inserts database records as
        an HTML table. The first row (header) is formatted with <th> tags,
        subsequent rows use <td> tags.
        
        Args:
            records (list): List of database records, first item should be headers.
            
        Returns:
            str: Complete HTML page with embedded table data.
            
        Raises:
            FileNotFoundError: If the HTML template file is not found.
        """
        fpath = os.path.dirname(os.path.abspath(__file__))
        fpath = os.path.join(fpath, 'templates/index.html')
        html_content = None
        with open(fpath, 'r') as fp:
            html_content = fp.readlines()
            idx = [i for i, x in enumerate(html_content) if 'INSERT_DATA_HERE' in x][0]
            first, last = html_content[:idx], html_content[idx+1:]
            data = []
            for idx, line in enumerate(records):
                smarker, emarker = ('<td>', '</td>') if idx else ('<th>', '</th>')
                data.append('<tr>\n')
                for elem in line:
                    data.append('\t%s%s%s\n' % (smarker, elem, emarker))
                data.append('</tr>\n')
        return ''.join(first + data + last)

def start_server(db_path, server=ThreadingHTTPServer, handler=SQL30Handler,
                 port=8008, json_output=True):
    """Start HTTP server to serve SQLite database contents.
    
    Creates and starts an HTTP server that serves database table contents
    either as JSON or HTML responses. The server runs indefinitely until
    interrupted with SIGINT (Ctrl+C).
    
    Args:
        db_path (str): Path to the SQLite database file to serve.
        server (class, optional): HTTP server class to use. Defaults to
            ThreadingHTTPServer for concurrent request handling.
        handler (class, optional): Request handler class. Defaults to
            SQL30Handler. Will be overridden based on json_output parameter.
        port (int, optional): Port number to listen on. Defaults to 8008.
        json_output (bool, optional): If True, serve JSON responses using
            SQL30Handler. If False, serve HTML responses using SQL30HandlerHTML.
            Defaults to True.
    
    Example:
        # Start server serving JSON responses on port 8080
        start_server('./my_database.db', port=8080)
        
        # Start server serving HTML responses
        start_server('./my_database.db', json_output=False)
    
    Note:
        The server will run indefinitely until interrupted. Use Ctrl+C
        to stop the server gracefully.
    """
    global DBPATH
    DBPATH = db_path

    server_address = ('', port)
    handler = SQL30Handler if json_output else SQL30HandlerHTML
    server = server(server_address, handler)

    def signal_handler(sig, frame):
        """Handle SIGINT signal for graceful server shutdown."""
        print('Closing server..')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    print('Starting httpd on port %d...' % port)
    server.serve_forever()

if __name__ == "__main__":
    if len(argv) >= 2:
        start_server(argv[1], port=int(argv[2]))
    else:
        start_server(None)
