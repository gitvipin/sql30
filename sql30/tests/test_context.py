# scale.py
import os
import unittest

from sql30 import db

DB_NAME = 'context.db'


class Config(db.Model):
    TABLE = 'square'
    PKEY = 'num'
    DB_SCHEMA = {
        'db_name': DB_NAME,
        'tables': [
            {
                'name': TABLE,
                'fields': {
                    'num': 'int',
                    'square': 'int',
                    },
                'primary_key': PKEY
            }]
        }
    VALIDATE_BEFORE_WRITE = True
    INIT_CONNECTION = True


class ContextTest(unittest.TestCase):

    TABLE = 'square'

    def setUp(self):
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)

        self.db = Config()
        self.db.table = self.TABLE
        self.db.create(num=-1, square=1)
        self.db.commit()

    def test_create(self):
        """
        Tests for context manager operations.
        """
        # TEST CASE 1:
        # Create a new database instance and use it under context
        # manager. This is the suggested usecase. Context Manager
        # when exiting, commits the work and also closes the
        # connection so user doesn't have to explicitly do so.
        with Config() as db:
            db.table = db.TABLE
            db.create(num=-2, square=4)

        # TEST CASE 2:
        # Read data back in new context to ensure data was saved in
        # the previous context.
        db = Config()
        with db.getContext() as conn:
            recs = conn.read(tbl=conn.TABLE, num=-2)
            self.assertEqual(len(recs), 1)

    def test_init(self):
        try:
            self.db.create(num=-3, square=9)
        except AttributeError as err:
            # This exception would come if we close the connection
            # at line number 40 instead of just saving work.
            msg = "'NoneType' object has no attribute 'execute'"
            self.assertIn(msg, err.args)

        self.db.init_connection()
        self.db.create(num=-4, square=16)
        self.db.close()

    def test_read(self):
        with Config() as db:
            recs = db.read(tbl=db.TABLE, num=-1)
            self.assertEqual(len(recs), 1)
