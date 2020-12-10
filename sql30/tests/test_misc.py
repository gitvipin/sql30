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

        # Populate 3 records for validating queries later.
        self.db.write(num=1, square=1)
        self.db.write(num=2, square=4)
        self.db.write(num=3, square=9)
        self.db.commit()

    def test_count(self):
        """
        Tests for COUNT operations.
        """
        with Square() as db:
            db.table = self.TABLE
            # case 1: Total numnber of records should be 3.
            self.assertEqual(db.count(), 3)

            # Number of records where num is 2 should be 1.
            self.assertEqual(db.count(num=2), 1)

            # Number of records where square is 9 should be 1.
            self.assertEqual(db.count(square=9), 1)

            # Number of records where 4 <= square <= 9 should be 1.
            self.assertEqual(db.count(square=[4, 9]), 2)

    def test_min(self):
        """
        Tests for MIN operations.
        """
        with Square() as db:
            db.table = self.TABLE
            # Minimum value for num is 1
            self.assertEqual(db.min('num'), 1)
            # Minimum value for square is 1
            self.assertEqual(db.min('square'), 1)

            # Minimum value for square when num = 2, is 4
            self.assertEqual(db.min('square', num=2), 4)
            # Minimum value for square when 3 <= num <= 5, is 9
            self.assertEqual(db.min('square', num=[3, 5]), 9)

    def test_max(self):
        """
        Tests for MAX operations.
        """
        with Square() as db:
            db.table = self.TABLE
            # Maximum value for num is 3
            self.assertEqual(db.max('num'), 3)
            # Maximum value for square is 9
            self.assertEqual(db.max('square'), 9)

            # Maximum value for square when num = 2, is 4
            self.assertEqual(db.max('square', num=2), 4)

            # Minimum value for square when 0 <= num <= 5, is 9
            self.assertEqual(db.max('square', num=[0, 5]), 9)

    def test_avg(self):
        """
        Tests for AVERAGE operations.
        """
        with Square() as db:
            db.table = self.TABLE
            # Average of all num values is 2.
            self.assertEqual(db.avg('num'), 2)
            self.assertEqual(db.avg('square', num=3), 9)

            # Average value of square when 1 <= num <= 2 should be 2.5
            self.assertEqual(db.avg('square', num=(1, 2)), 2.5)

    def test_range(self):
        """
        Tests for RANGE operations.
        """
        with Square() as db:
            db.table = self.TABLE
            # Read records where : 0 <= num <= 3. There should be 3 records.
            self.assertEqual(len(db.read(num=(0, 3))), 3)

            # Read records where : 1 <= num <= 2. There should be 2 records.
            self.assertEqual(len(db.read(num=(1, 2))), 2)

            # Read records where : 2 < quare < 5. There should be 1 record.
            # Also check that list based range is expected
            self.assertEqual(len(db.read(square=[2, 5])), 1)

            # Check that range is inclusive i.e. no records for :
            # 2 <= square <= 3.
            self.assertEqual(len(db.read(square=[2, 3])), 0)

    def tearDown(self):
        os.remove(DB_NAME)
