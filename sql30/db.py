#!/bin/env/python
'''
A simple interface for interacting with SQLite example.
'''
import logging
import os
import sqlite3


log = logging.getLogger(__name__)

PATHSEP = '/'


class Model(object):

    DB_SCHEMA = {
            'db_name': 'DEFAULT_DB',
            'tables': []
            }
    VALIDATE_BEFORE_WRITE = False

    # Location where database files should be saved.
    DB_FILE_LOC = '/opt/sql30/'

    # Initialize global connection to sqlite database.
    INIT_CONNECTION = True

    def __init__(self, **kwargs):
        # set default DB file location
        self._db_loc = kwargs.get('db_loc', None) or self.DB_FILE_LOC

        self._db = kwargs.get('db_name', None) or self.DB_SCHEMA['db_name']
        if PATHSEP not in self._db:
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

        if self.INIT_CONNECTION:
            self.init_connection()

        self._table = None

        # Initialize Database
        self.init_db(schema=self.DB_SCHEMA)

    @property
    def table(self):
        return self._table

    @table.setter
    def table(self, val):
        self._table = val

    @property
    def db_loc(self):
        return self._db_loc

    @db_loc.setter
    def db_loc(self, val):
        self._db_loc = val

    @property
    def db_file(self):
        return self._db

    @property
    def connection(self):
        # If you are inside a context, all the operations are presumed
        # to be done on the context. Otherwise, it is global context.
        return self._context_conn or self._conn

    @property
    def cursor(self):
        return self._context_cursor if self._context_conn else self._cursor

    def init_connection(self):
        """
        Initializes connection to database. It must be called before performing
        any CRUD operations. It is automatically called unless INIT_CONNECTION
        is set to false intentionally in which case, user must call it
        explicitly.
        """
        if not self._conn:
            self._conn = sqlite3.connect(self._db)
            self._cursor = self._conn.cursor()

    def commit(self):
        if self.verbose:
            log.debug("Performing COMMIT via %s", self.connection)
        self.connection.commit()

    def close(self, commit=True):
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
        assert not self._context_conn, "nested context not allowed"
        self._context_conn = sqlite3.connect(self._db)
        self._context_cursor = self._context_conn.cursor()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
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

    def init_db(self, schema):
        '''
        Initializes Databse using schema by creating tables specified in
        the schema.
        {
          'tables': [
            {
                'name': 'stocks',
                'fields': {
                    'date' : 'text',
                    'trans': 'text'
                }
            },
            {
                'name': 'people',
                'fields': {
                    'name' : 'text',
                    'addr': 'text'
                }
            }]
        }
        '''
        for table in schema['tables']:
            self.create_table(schema=table)

    def table_exists(self, tbl_name):
        """
        Returns True if table exists else False
        """
        return True if self.read('sqlite_master',
                                 type='table',
                                 name=tbl_name) else False

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

        if self.table_exists(tbl_name):
            if self.verbose:
                log.debug("Table %s exists, skipped from creation", tbl_name)
            return

        cols = []

        # Python dictionaries aren't guaranted to be read back in same order
        # as they are declared. It is for this reason we ask for column_order,
        # in schema declaration
        for cname, ctype in schema['fields'].items():
            _col = '%s %s' % (cname, ctype)
            if cname == pkey:
                _col += ' PRIMARY KEY'
            cols.append(_col)
        cols = '(%s)' % ','.join(cols)

        cmnd = '''CREATE TABLE %s %s''' % (tbl_name, cols)
        log.info("Creating Table as : %s", cmnd)
        self.cursor.execute(cmnd)

    def _get_schema(self, tbl_name):
        """
        """
        tbl_schema = [x for x in self.DB_SCHEMA['tables'] if
                      x['name'] == tbl_name]
        return tbl_schema[0] if tbl_schema else None

    def _get_fields(self, tbl_name):
        """
        """
        _schema = self._get_schema(tbl_name)
        return [key for key, _ in _schema['fields'].items()]

    def _form_constraints(self, _separator='and', kwargs=None):
        constraints = ['%s=:%s' % (key, key) for key, _ in kwargs.items()]
        return (' %s ' % _separator).join(constraints)

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
        tbl = tbl or self.table
        assert tbl, "No table set for operation"
        self._validate_bfr_write(tbl, kwargs)
        tbl_schema = self._get_schema(tbl)

        # Python must be greater than 3.6 for this to work. Python 3.6 onwards
        # guarantes that keys of a dictionry by default come in same order as
        # they were declared. Here, we simply form an ordered tuple of values
        # in the same order as the columns were declared in schema.
        values = [kwargs.get(field, '') for field, _
                  in tbl_schema['fields'].items()]

        self.cursor.execute('INSERT INTO %s VALUES (%s)' % (tbl,
                            ','.join(['?'] * len(values))),
                            values)

    def read(self, tbl=None, include_header=False, **kwargs):
        """
        Read from Table all the records with requested constraints.
        """
        tbl = tbl or self.table
        assert tbl, "No table set for operation"
        if kwargs:
            constraints = self._form_constraints(kwargs=kwargs)
            query = 'SELECT * FROM %s WHERE %s' % (tbl, constraints)
            self.cursor.execute(query, kwargs)
        else:
            query = 'SELECT * FROM %s ' % tbl
            self.cursor.execute(query, kwargs)

        result = self.cursor.fetchall()  # TODO : Can be inefficient at scale.
        if include_header:
            header = [d[0] for d in self.cursor.description]
            result.insert(0, header)

        return result

    def update(self, tbl=None, condition={}, **kwargs):
        tbl = tbl or self.table
        assert tbl, "No table set for operation"
        msg = "With no/empty condition, WHERE clause cannot be set for UPDATE"
        assert condition, msg
        cond = self._form_constraints(kwargs=condition)
        values = self._form_constraints(_separator=',', kwargs=kwargs)
        query = 'UPDATE %s SET %s WHERE %s' % (tbl, values, cond)
        kwargs.update(condition)
        self.cursor.execute(query, kwargs)

    def delete(self, tbl=None, **kwargs):
        tbl = tbl or self.table
        assert tbl, "No table set for operation"
        constraints = self._form_constraints(kwargs=kwargs)
        query = 'DELETE FROM %s WHERE %s' % (tbl, constraints)
        self.cursor.execute(query, kwargs)

    def count(self, tbl=None, **kwargs):
        tbl = tbl or self.table
        assert tbl, "No table set for operation"
        constraints = self._form_constraints(kwargs=kwargs)
        if constraints:
            query = 'SELECT COUNT(*) FROM %s WHERE %s' % (tbl, constraints)
        else:
            query = 'SELECT COUNT(*) FROM %s ' % tbl

        self.cursor.execute(query, kwargs)
        try:
            return self.cursor.fetchone()[0]
        except:
            return None

    # Backward compatibility (release 0.0.1 ).
    write = create
    remove = delete
