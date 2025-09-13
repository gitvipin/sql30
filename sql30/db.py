#!/usr/bin/env python
# Copyright (c) 2020 Vipin Sharma. All Rights Reserved.
# SPDX-License-Identifier: BSD-2 License
# The full license information can be found in LICENSE.txt
# in the root directory of this project.
"""SQL30 - A lightweight ORM for SQLite databases.

This module provides a simple Object-Relational Mapping (ORM) interface for
SQLite databases. It allows users to define database schemas using JSON
configuration and perform CRUD operations without writing SQL directly.

Key Features:
    - Zero external dependencies (pure Python)
    - JSON-based schema definition
    - Automatic table creation and management
    - Context manager support for transaction handling
    - HTTP server integration for database browsing
    - Support for database export and schema discovery

Example:
    class Reviews(db.Model):
        TABLE = 'reviews'
        PKEY = 'rid'
        DB_SCHEMA = {
            'db_name': './reviews.db',
            'tables': [{
                'name': TABLE,
                'fields': {
                    'rid': 'uuid',
                    'header': 'text',
                    'rating': 'int',
                    'desc': 'text'
                },
                'primary_key': PKEY
            }]
        }
        VALIDATE_BEFORE_WRITE = True

    # Usage
    db = Reviews()
    db.table = 'reviews'
    db.create(rid=1, header='Great product', rating=5)
    records = db.read()
"""
import logging
import os
import sqlite3


log = logging.getLogger(__name__)

PATHSEP = '/'


class Model(object):
    """Base model class for SQLite database operations.
    
    This class provides the core ORM functionality for SQLite databases.
    It handles database connections, schema management, and CRUD operations.
    
    Attributes:
        DB_SCHEMA (dict): Database schema configuration containing database
            name and table definitions.
        VALIDATE_BEFORE_WRITE (bool): Whether to validate field names before
            writing to database. Defaults to False.
        DB_FILE_LOC (str): Default location for database files.
        INIT_CONNECTION (bool): Whether to initialize connection on instantiation.
        TIMEOUT (int): Connection timeout in seconds. None uses SQLite default.
        DEFAULT_TABLE (str): Default table name for operations.
    
    Example:
        class MyModel(db.Model):
            DB_SCHEMA = {
                'db_name': './mydb.db',
                'tables': [{
                    'name': 'users',
                    'fields': {'id': 'int', 'name': 'text'},
                    'primary_key': 'id'
                }]
            }
    """

    DB_SCHEMA = {
            'db_name': 'DEFAULT_DB',
            'tables': []
            }
    VALIDATE_BEFORE_WRITE = False

    # Location where database files would be saved unless
    # 1) path is relative (i.e. has path separator in it) OR
    # 2) SQL30_DB_DIR environment variable is set.
    DB_FILE_LOC = '/opt/sql30/'

    # Initialize global connection to sqlite database.
    INIT_CONNECTION = True

    # Timeout for connection
    TIMEOUT = None  # default is 5 seconds, coming from python.

    # Default Table
    DEFAULT_TABLE = None

    def __init__(self, **kwargs):
        """Initialize the database model instance.
        
        Sets up database connection, file paths, and initializes the database
        schema. Handles environment variable overrides and path resolution.
        
        Args:
            **kwargs: Optional keyword arguments:
                db_loc (str): Custom database file location.
                db_name (str): Custom database file name.
                verbose (bool): Enable verbose logging.
                timeout (int): Connection timeout in seconds.
        
        Environment Variables:
            SQL30_DB_DIR: If set, overrides all database file locations.
            
        Example:
            # Basic initialization
            db = MyModel()
            
            # With custom database location
            db = MyModel(db_name='./custom.db', verbose=True)
            
            # With custom timeout
            db = MyModel(timeout=30)
        """
        # set default DB file location
        self._db_loc = kwargs.get('db_loc', None) or self.DB_FILE_LOC

        self._db = kwargs.get('db_name', None) or self.DB_SCHEMA['db_name']

        _db_global_path = os.environ.get('SQL30_DB_DIR', None)
        if _db_global_path:
            # If SQL30_DB_DIR is set, it supersedes all request for DB file
            # location. All DB files whether given w.r.t relative path or
            # just filename would always goto this directory.
            _, self._db = os.path.split(self._db)
            self._db = os.path.join(_db_global_path, self._db)
            if not os.path.exists(_db_global_path):
                os.makedirs(_db_global_path)
        elif PATHSEP not in self._db:
            if not os.path.exists(self.db_loc):
                os.makedirs(self.db_loc)
            self._db = os.path.join(self.db_loc, self._db)

        self.DB_SCHEMA['db_name'] = self._db    # if came from kwargs

        self.verbose = kwargs.get('verbose', False)

        # Common connection and cursor for interacting with databse.
        self._conn = None
        self._cursor = None

        # Context Manager's db connection and cursor.
        self._context_conn = None
        self._context_cursor = None

        self._timeout = kwargs.get('timeout', None)

        if self.INIT_CONNECTION:
            self.init_connection()

        self._table = None

        # Initialize Database
        self.init_db(schema=self.DB_SCHEMA)

    @property
    def table(self):
        """Get the current active table name.
        
        Returns:
            str: The currently active table name, or DEFAULT_TABLE if none set.
        """
        return self._table or self.DEFAULT_TABLE

    @property
    def timeout(self):
        """Get the database connection timeout.
        
        Returns:
            int: Connection timeout in seconds, or None for SQLite default.
        """
        return self._timeout or self.TIMEOUT

    @table.setter
    def table(self, val):
        """Set the active table for subsequent operations.
        
        Args:
            val (str): Name of the table to set as active.
        """
        self._table = val

    @property
    def db_loc(self):
        """Get the database file location directory.
        
        Returns:
            str: Directory path where database files are stored.
        """
        return self._db_loc

    @db_loc.setter
    def db_loc(self, val):
        """Set the database file location directory.
        
        Args:
            val (str): Directory path for database files.
        """
        self._db_loc = val

    @property
    def db_file(self):
        """Get the full path to the database file.
        
        Returns:
            str: Complete file path to the SQLite database file.
        """
        return self._db

    @property
    def connection(self):
        """Get the current database connection.
        
        Returns the context connection if inside a context manager,
        otherwise returns the global connection.
        
        Returns:
            sqlite3.Connection: Active database connection.
        """
        # If you are inside a context, all the operations are presumed
        # to be done on the context. Otherwise, it is global context.
        return self._context_conn or self._conn

    @property
    def cursor(self):
        """Get the current database cursor.
        
        Returns the context cursor if inside a context manager,
        otherwise returns the global cursor.
        
        Returns:
            sqlite3.Cursor: Active database cursor.
        """
        return self._context_cursor if self._context_conn else self._cursor

    def init_connection(self):
        """
        Initializes connection to database. It must be called before performing
        any CRUD operations. It is automatically called unless INIT_CONNECTION
        is set to false intentionally in which case, user must call it
        explicitly.
        """
        if not self._conn:
            self._conn = self.get_conn_handle()
            self._cursor = self._conn.cursor()

    def get_conn_handle(self):
        """
        Returns new Connection handle to Database.

        When using this ORM with other than SQLITE3 databases, for example
        PostgresSQL, users can just simply overwrite this method and can
        still using regular CRUD operations.
        """
        if not self.timeout:
            return sqlite3.connect(self._db)
        else:
            return sqlite3.connect(self._db, timeout=self.timeout)

    def commit(self):
        """Commit pending transactions to the database.
        
        Commits all pending changes to the database. This is automatically
        called when using context managers, but can be called manually
        for explicit transaction control.
        
        Example:
            db.create(rid=1, header='test')
            db.commit()  # Persist changes to disk
        """
        if self.verbose:
            log.debug("Performing COMMIT via %s", self.connection)
        self.connection.commit()

    def close(self, commit=True):
        """Close the database connection.
        
        Closes the database connection and optionally commits pending
        transactions. This method handles both global and context connections.
        
        Args:
            commit (bool): Whether to commit pending transactions before
                closing. Defaults to True.
        
        Example:
            db.create(rid=1, header='test')
            db.close()  # Commits and closes connection
            
            # Close without committing
            db.close(commit=False)
        """
        if commit:
            self.commit()
        conn = self.connection  # cache before setting to None
        if conn == self._conn:
            self._conn = None
            self._cursor = None
        if self.verbose:
            log.debug("Clossing connection %s", conn)
        conn.close()

    def __enter__(self):
        """Enter the context manager.
        
        Creates a new database connection and cursor for use within
        the context manager. Automatically commits and closes on exit.
        
        Returns:
            Model: Self instance for use in context.
            
        Raises:
            AssertionError: If already inside a context manager.
            
        Example:
            with MyModel() as db:
                db.create(rid=1, header='test')
                # Automatically committed and closed on exit
        """
        assert not self._context_conn, "nested context not allowed"
        self._context_conn = self.get_conn_handle()
        self._context_cursor = self._context_conn.cursor()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Exit the context manager.
        
        Commits all pending transactions and closes the context connection.
        This is automatically called when exiting a with statement.
        
        Args:
            exc_type: Exception type if an exception occurred.
            exc_value: Exception value if an exception occurred.
            exc_traceback: Exception traceback if an exception occurred.
        """
        if self._context_conn:
            self._context_conn.commit()
            self._context_conn.close()
            self._context_conn = None
            self._context_cursor = None

    def getContext(self):
        """
        To be used as following in legacy code.

        with self.getContext() as db:
            db.create(...)
        """
        return self

    @property
    def table_names(self):
        """ Returns list of tables in sqlite_master database. """
        records = self.read('sqlite_master', type='table', include_header=True)
        nindex = records[0].index('name')
        return [x[nindex] for x in records[1:]]

    def fetch_schema(self):
        """ Fetches DB Schema and populates table info """
        records = self.read('sqlite_master', type='table', include_header=True)
        nidx = records[0].index('name')
        sidx = records[0].index('sql')

        for table_info in records[1:]:
            tbl_name = table_info[nidx]
            tbl_sql = table_info[sidx]

            schema = {}
            schema['name'] = tbl_name
            fields = {}
            fstart = tbl_sql.index('(')
            fend = tbl_sql.index(')')
            tbl_sql = tbl_sql[fstart+1:fend].split(',')
            tbl_sql = [str(x.strip()) for x in tbl_sql]
            for line in tbl_sql:
                if 'CREATE TABLE' in line:
                    continue
                elif line == ')':
                    continue
                elif line.startswith('PRIMARY KEY'):
                    start, end = line.index('('), line.index(')')
                    schema['primary_key'] = line[start+1:end]
                else:
                    line = line.split()
                    var = line[0]
                    if line[1] in ['VARCHAR', 'text']:
                        fields[var] = 'text'
                    elif line[1] in ['INTEGER', 'int']:
                        fields[var] = 'int'

            schema['fields'] = fields
            _table = [x for x in self.DB_SCHEMA['tables'] if x['name'] == tbl_name]
            assert len(_table) <= 1
            if _table:
                _table[0].update(schema)
            else:
                self.DB_SCHEMA['tables'].append(schema)

    def export(self, dbfile='db.scehma', schema_only=False):
        """
        Exports whole database in a file with SQL statements. This
        file can then be taken anywhere and database can be reconstructed
        by following command :
            $ sqlite3 my_backup.db < db.schema

        Parameters
        -----------
        dbfile : str
            Path and filename to be dumped. Defaults to db.schema
        schema_only : bool
            Dumps only schema and not the data when set to True ; default False.
        """

        with open(dbfile, 'w+') as fp:
            for line in self.connection.iterdump():
                if schema_only and line.startswith('INSERT INTO'):
                    continue
                fp.write('%s\n' % line)

    def init_db(self, schema):
        """Initialize database using the provided schema.
        
        Creates all tables specified in the schema configuration.
        This method is automatically called during model initialization.
        
        Args:
            schema (dict): Database schema configuration containing:
                - 'tables': List of table definitions
                
        Schema Format:
            {
                'tables': [
                    {
                        'name': 'table_name',
                        'fields': {'col1': 'type1', 'col2': 'type2'},
                        'primary_key': 'col1'  # optional
                    }
                ]
            }
        
        Example:
            schema = {
                'tables': [{
                    'name': 'users',
                    'fields': {'id': 'int', 'name': 'text'},
                    'primary_key': 'id'
                }]
            }
            db.init_db(schema)
        """
        for table in schema['tables']:
            self.create_table(schema=table)

    def table_exists(self, tbl_name):
        """Check if a table exists in the database.
        
        Args:
            tbl_name (str): Name of the table to check.
            
        Returns:
            bool: True if table exists, False otherwise.
            
        Example:
            if db.table_exists('users'):
                print('Users table exists')
        """
        return True if self.read('sqlite_master',
                                 type='table',
                                 name=tbl_name) else False

    def _add_col_order(self, tbl_schema):
        """Add column order information to table schema.
        
        Ensures that the table schema includes a 'col_order' field that
        preserves the order of columns as defined in the schema.
        
        Args:
            tbl_schema (dict): Table schema dictionary to modify.
        """
        if 'col_order' in tbl_schema:
            return
        tbl_schema['col_order'] = [k for k, _ in tbl_schema['fields'].items()]

    def _get_col_order(self, tbl, schema=None):
        """Get columns in the order they were created.
        
        Args:
            tbl (str): Table name.
            schema (dict, optional): Table schema. If not provided, will be fetched.
            
        Returns:
            list: List of column names in creation order.
        """
        tbl_schema = schema or self._get_schema(tbl)
        return tbl_schema['col_order']

    def create_table(self, schema):
        """
        Creates Table into the database represented by database here using
        the schema. Schema is represented in JSON and must have two fields
        'table' and 'fields'
        {
            'name': 'stocks',
            'fields': {
                'date' : 'text',
                'trans': 'text'
                }
        }
        """
        tbl_name = schema['name']
        pkey = schema.get('primary_key', None)
        self._add_col_order(schema)

        if self.table_exists(tbl_name):
            if self.verbose:
                log.debug("Table %s exists, skipped from creation", tbl_name)
            return

        cols = []

        _fields = schema['fields']
        for cname in self._get_col_order(tbl_name, schema):
            ctype = _fields[cname]
            _col = '%s %s' % (cname, ctype)
            if cname == pkey:
                _col += ' PRIMARY KEY'
            cols.append(_col)
        cols = '(%s)' % ','.join(cols)

        cmnd = '''CREATE TABLE %s %s''' % (tbl_name, cols)
        log.info("Creating Table as : %s", cmnd)
        self.cursor.execute(cmnd)

    def _get_schema(self, tbl_name):
        """Get the schema definition for a specific table.
        
        Args:
            tbl_name (str): Name of the table.
            
        Returns:
            dict: Table schema dictionary, or None if table not found.
        """
        tbl_schema = [x for x in self.DB_SCHEMA['tables'] if
                      x['name'] == tbl_name]
        return tbl_schema[0] if tbl_schema else None

    def _get_fields(self, tbl_name):
        """Get the list of field names for a table.
        
        Args:
            tbl_name (str): Name of the table.
            
        Returns:
            list: List of field names in creation order.
        """
        return self._get_col_order(tbl_name)

    def __form_constraints(self, _separator='and', kwargs=None):
        def is_range(x): return isinstance(x, tuple) or isinstance(x, list)
        constraints = []
        for key, val in kwargs.items():
            if is_range(val):
                cparam = '%s BETWEEN %s AND %s' % (key, val[0], val[1])
            else:
                cparam = '%s=:%s' % (key, key)
            constraints.append(cparam)
        return (' %s ' % _separator).join(constraints)

    def _form_constraints(self, _separator='and', kwargs=None):
        if not kwargs:
            return ''
        return 'WHERE ' + self.__form_constraints(_separator=_separator, kwargs=kwargs)

    def _validate_bfr_write(self, tbl, kwargs):
        if not self.VALIDATE_BEFORE_WRITE:
            return

        _fields = self._get_fields(tbl)
        unknown = []
        for x in kwargs.keys():
            if x not in _fields:
                unknown.append(x)
        if unknown:
            raise AssertionError("Unknown columns :%r" % unknown)

    # CRUD operation methods' definition.

    def create(self, tbl=None, **kwargs):
        """Create a new record in the specified table.
        
        Inserts a new record into the database table with the provided
        field values. All fields defined in the table schema must be provided.
        
        Args:
            tbl (str, optional): Table name. Uses self.table if not provided.
            **kwargs: Column name-value pairs for the new record.
            
        Raises:
            AssertionError: If table is not set or validation fails.
            sqlite3.IntegrityError: If primary key constraint is violated.
            
        Example:
            # Create a new review record
            db.create(rid=1, header='Great product', rating=5, desc='Love it!')
            
            # Create in specific table
            db.create('reviews', rid=2, header='Good', rating=4)
        """
        tbl = tbl or self.table
        assert tbl, "No table set for operation"
        self._validate_bfr_write(tbl, kwargs)

        values = [kwargs.get(field, '') for field in self._get_fields(tbl)]

        cmnd = 'INSERT INTO %s VALUES (%s)' % (tbl, ','.join(['?'] * len(values)))
        self.cursor.execute(cmnd, values)

    def read(self, tbl=None, include_header=False, **kwargs):
        """Read records from the specified table with optional filtering.
        
        Retrieves records from the database table with optional WHERE clause
        constraints, LIMIT, and OFFSET for pagination.
        
        Args:
            tbl (str, optional): Table name. Uses self.table if not provided.
            include_header (bool): Whether to include column headers in result.
                Defaults to False.
            **kwargs: Filter conditions as column=value pairs. Special keys:
                - LIMIT (int): Maximum number of records to return
                - OFFSET (int): Number of records to skip
                - Range filters: Use tuple/list for BETWEEN queries
                
        Returns:
            list: List of tuples representing database records. If include_header
                is True, first element is a list of column names.
                
        Example:
            # Read all records
            records = db.read()
            
            # Read with filtering
            records = db.read(rid=1, rating=5)
            
            # Read with pagination
            records = db.read(LIMIT=10, OFFSET=20)
            
            # Read with range filter
            records = db.read(rating=(3, 5))  # rating BETWEEN 3 AND 5
            
            # Read with headers
            records = db.read(include_header=True)
        """
        tbl = tbl or self.table
        assert tbl, "No table set for operation"

        _limit = kwargs.pop('LIMIT', None)
        _offset = kwargs.pop('OFFSET', None)
        constraints = self._form_constraints(kwargs=kwargs)
        query = 'SELECT * FROM %s %s' % (tbl, constraints)

        if _limit is not None:
            query += ' LIMIT %s ' % _limit
        if _offset is not None:
            query += ' OFFSET %s ' % _offset

        self.cursor.execute(query, kwargs)
        result = self.cursor.fetchall()  # TODO : Can be inefficient at scale.
        if include_header:
            header = [d[0] for d in self.cursor.description]
            result.insert(0, header)

        return result

    def update(self, tbl=None, condition={}, **kwargs):
        """Update records in the specified table.
        
        Updates existing records in the database table based on the provided
        condition. The condition parameter is required to prevent accidental
        updates of all records.
        
        Args:
            tbl (str, optional): Table name. Uses self.table if not provided.
            condition (dict): WHERE clause conditions as column=value pairs.
                This parameter is required and cannot be empty.
            **kwargs: Column=value pairs for the fields to update.
            
        Raises:
            #TODO : Validate second part of docstring below.
            AssertionError: If table is not set or condition is empty.
            
        Example:
            # Update a specific record
            db.update(condition={'rid': 1}, header='Updated title', rating=4)
            
            # Update multiple records matching condition
            db.update(condition={'rating': 1}, rating=2)  # Change all 1-star to 2-star
            
            # Update in specific table
            db.update('reviews', condition={'rid': 2}, header='New title')
        """
        tbl = tbl or self.table
        assert tbl, "No table set for operation"
        msg = "With no/empty condition, WHERE clause cannot be set for UPDATE"
        assert condition, msg
        values = self.__form_constraints(_separator=',', kwargs=kwargs)
        cond = self._form_constraints(kwargs=condition)
        query = 'UPDATE %s SET %s %s' % (tbl, values, cond)
        kwargs.update(condition)
        self.cursor.execute(query, kwargs)

    def delete(self, tbl=None, **kwargs):
        """Delete records from the specified table.
        
        Removes records from the database table based on the provided
        filter conditions. If no conditions are provided, all records
        in the table will be deleted.
        
        Args:
            tbl (str, optional): Table name. Uses self.table if not provided.
            **kwargs: Filter conditions as column=value pairs for WHERE clause.
                
        Warning:
            If no conditions are provided, ALL records in the table will be deleted.
            
        Example:
            # Delete specific record
            db.delete(rid=1)
            
            # Delete records matching multiple conditions
            db.delete(rating=1, header='Bad review')
            
            # Delete in specific table
            db.delete('reviews', rid=2)
            
            # Delete all records (use with caution!)
            db.delete()  # Deletes all records in current table
        """
        tbl = tbl or self.table
        assert tbl, "No table set for operation"
        constraints = self._form_constraints(kwargs=kwargs)
        query = 'DELETE FROM %s %s' % (tbl, constraints)
        self.cursor.execute(query, kwargs)

    def _misc(self, method, field, tbl=None, **kwargs):
        tbl = tbl or self.table
        assert tbl, "No table set for operation"
        constraints = self._form_constraints(kwargs=kwargs)
        query = 'SELECT %s(%s) FROM %s %s' % (method, field, tbl, constraints)
        self.cursor.execute(query, kwargs)
        try:
            return self.cursor.fetchone()[0]
        except Exception as err:
            log.exception(err)
            return None

    def count(self, tbl=None, **kwargs):
        """Count records in the specified table.
        
        Returns the number of records matching the given conditions.
        
        Args:
            tbl (str, optional): Table name. Uses self.table if not provided.
            **kwargs: Filter conditions as column=value pairs.
            
        Returns:
            int: Number of records matching the conditions.
            
        Example:
            # Count all records
            total = db.count()
            
            # Count with filtering
            high_rated = db.count(rating=5)
            
            # Count with range filter
            good_reviews = db.count(rating=(4, 5))
        """
        return self._misc('COUNT', '*', tbl=tbl, **kwargs)

    def min(self, field, tbl=None, **kwargs):
        """Get the minimum value of a field.
        
        Args:
            field (str): Name of the field to find minimum value for.
            tbl (str, optional): Table name. Uses self.table if not provided.
            **kwargs: Filter conditions as column=value pairs.
            
        Returns:
            The minimum value of the specified field, or None if no records.
            
        Raises:
            AssertionError: If field does not exist in the table.
            
        Example:
            # Find minimum rating
            min_rating = db.min('rating')
            
            # Find minimum rating with filtering
            min_rating = db.min('rating', header='Good product')
        """
        tbl = tbl or self.table
        assert field in self._get_fields(tbl)
        return self._misc('MIN', field, tbl=tbl, **kwargs)

    def max(self, field, tbl=None, **kwargs):
        """Get the maximum value of a field.
        
        Args:
            field (str): Name of the field to find maximum value for.
            tbl (str, optional): Table name. Uses self.table if not provided.
            **kwargs: Filter conditions as column=value pairs.
            
        Returns:
            The maximum value of the specified field, or None if no records.
            
        Raises:
            AssertionError: If field does not exist in the table.
            
        Example:
            # Find maximum rating
            max_rating = db.max('rating')
            
            # Find maximum rating with filtering
            max_rating = db.max('rating', header='Great product')
        """
        tbl = tbl or self.table
        assert field in self._get_fields(tbl)
        return self._misc('MAX', field, tbl=tbl, **kwargs)

    def avg(self, field, tbl=None, **kwargs):
        """Get the average value of a field.
        
        Args:
            field (str): Name of the field to calculate average for.
            tbl (str, optional): Table name. Uses self.table if not provided.
            **kwargs: Filter conditions as column=value pairs.
            
        Returns:
            float: The average value of the specified field, or None if no records.
            
        Raises:
            AssertionError: If field does not exist in the table.
            
        Example:
            # Calculate average rating
            avg_rating = db.avg('rating')
            
            # Calculate average rating with filtering
            avg_rating = db.avg('rating', header='Good product')
        """
        tbl = tbl or self.table
        assert field in self._get_fields(tbl)
        return self._misc('AVG', field, tbl=tbl, **kwargs)

    # Backward compatibility (release 0.0.1 ).
    write = create
    remove = delete
