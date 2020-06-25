#!/bin/env/python
'''
A simple interface for interacting with SQLite example.
'''
import logging
import sqlite3


log = logging.getLogger(__name__)


class Model(object):

    DB_SCHEMA = {
            'db_name' : 'DEFAULT_DB',
            'tables': []
            }
    VALIDATE_BEFORE_WRITE = False

    def __init__(self, **kwargs):
        self._db = kwargs.get('db_name', None) or self.DB_SCHEMA['db_name']
        self.DB_SCHEMA['db_name'] = self._db    # if came from kwargs
        self._conn = sqlite3.connect(self._db)
        self._cursor = self._conn.cursor()

        # Initialize Database
        self.init_db(schema=self.DB_SCHEMA)

    @property
    def cursor(self):
        return self._cursor

    def commit(self):
        self._conn.commit()

    def close(self, commit=True):
        if commit:
            self._conn.commit()
        self._conn.close()

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
            log.info("Table %s exists, skipped from creation", tbl_name)
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
        print ("Creating Table as : ", cmnd)
        self._cursor.execute(cmnd)

    def _get_schema(self, tbl_name):
        """
        """
        tbl_schema = [x for x in self.DB_SCHEMA['tables'] if x['name'] == tbl_name]
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

    def write(self, tbl, **kwargs):
        self._validate_bfr_write(tbl, kwargs)
        tbl_schema = self._get_schema(tbl)

        # Python must be greater than 3.6 for this to work. Python 3.6 onwards
        # guarantes that keys of a dictionry by default come in same order as
        # they were declared. Here, we simply form an ordered tuple of values
        # in the same order as the columns were declared in schema.
        values = [kwargs.get(field, '') for field, _ in tbl_schema['fields'].items()]

        self._cursor.execute(
                'INSERT INTO %s VALUES (%s)' % (tbl,','.join(['?'] * len(values))),
                values)

    def read(self, tbl, include_header=False, **kwargs):
        """
        Read from Table all the records with requested constraints.
        """
        if kwargs:
            constraints = self._form_constraints(kwargs=kwargs)
            query = 'SELECT * FROM %s WHERE %s' % (tbl, constraints)
            self._cursor.execute(query, kwargs)
        else:
            query = 'SELECT * FROM %s ' % tbl
            self._cursor.execute(query, kwargs)

        result = self._cursor.fetchall()    # TODO : Can be inefficient at scale.
        if include_header:
            header = [d[0] for d in self._cursor.description]
            result.insert(0, header)

        return result

    def update(self, tbl, condition, **kwargs):
        cond = self._form_constraints(kwargs=condition)
        values = self._form_constraints(_separator=',', kwargs=kwargs)
        query = 'UPDATE %s SET %s WHERE %s' % (tbl, values, cond)
        kwargs.update(condition)
        self._cursor.execute(query, kwargs)

    def remove(self, tbl, **kwargs):
        constraints = self._form_constraints(kwargs=kwargs)
        query = 'DELETE FROM %s WHERE %s' % (tbl, constraints)
        self._cursor.execute(query, kwargs)
