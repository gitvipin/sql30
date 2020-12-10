# scale.py
import os
import unittest

from sql30 import db

DB_NAME = './count.db'


class Square(db.Model):
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


class MiscTest(unittest.TestCase):

    TABLE = 'square'

    def setUp(self):
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)

        self.db = Square()
        self.db.table = self.TABLE

        # add 3 records
        self.db.write(num=1, square=1)
        self.db.write(num=2, square=4)
        self.db.write(num=3, square=9)
        self.db.commit()

    def test_count(self):
        """
        Tests for context manager operations.
        """
        import pdb ; pdb.set_trace()
        with Square() as db:
            db.table = self.TABLE
            self.assertEqual(db.count(), 3)

            self.assertEqual(db.count(num=2), 1)
            self.assertEqual(db.count(square=9), 1)



    def tearDown(self):
        os.remove(DB_NAME)
