"""
Unittest for testing SQL30_DB_DIR based path feature.

NOTE: This test file is deliberately not named as test_path.py
but rather as testPath.py. It is because this test modifes the
local environment variable and hence must be run separately.

All the test_*.py tests are run together.
"""

import os
import tempfile
import unittest

from sql30 import db

DB_NAME = './path.db'


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


class PathTest(unittest.TestCase):

    TABLE = 'square'

    def setUp(self):
        """
        setUp is run before each test.
        """
        # Chose a temporary directory for DB file path.
        self.db_test_dir = tempfile.mkdtemp()

        os.environ['SQL30_DB_DIR'] = self.db_test_dir

        self.db_path = os.path.join(self.db_test_dir, DB_NAME)

        self.db = Square()
        self.db.table = self.TABLE

        # Populate 3 records for validating queries later.
        self.db.write(num=1, square=1)
        self.db.write(num=2, square=4)
        self.db.write(num=3, square=9)
        self.db.commit()

    def test_db_path(self):
        """
        Test - SQL30_DB_DIR honored.
        """
        assert os.path.exists(self.db_path)

    def test_db_path_matches(self):
        """
        Test - SQL30_DB_DIR honored for future operations.
        """
        with Square() as db:
            msg = "DB file path error."
            assert os.path.samefile(db._db, self.db_path), msg

    def test_db_loc_path(self):
        """
        Test - SQL30_DB_DIR overrides db_loc argument.
        """
        with Square(db_loc='./does/not/matter/') as db:
            msg = "DB file path error."
            assert os.path.samefile(db._db, self.db_path), msg

            db.table = self.TABLE
            # case 1: Total numnber of records should be 3.
            self.assertEqual(db.count(), 3)

            # Number of records where num is 2 should be 1.
            self.assertEqual(db.count(num=2), 1)

            # Number of records where square is 9 should be 1.
            self.assertEqual(db.count(square=9), 1)

            # Number of records where 4 <= square <= 9 should be 1.
            self.assertEqual(db.count(square=[4, 9]), 2)

    def tearDown(self):
        """
        tearDown is run after each test.
        """
        os.remove(self.db_path)

        # Do not use shtutil.rmtree() as it will delete contents
        # automatically. Delete using os.rmdir() insteas as it
        # expects directory to be empty which becomes another test
        # to ensure only one file was created by this test.
        os.rmdir(self.db_test_dir)
