# scale.py
import os
import threading
import unittest

from sql30 import db

DB_NAME = './square.db'


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


class ScaleTest(unittest.TestCase):

    SQUARE_NUM_UPTO = 20   # make it multiple of 5
    TABLE = 'square'

    def setUp(self):
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)

        db = Config()
        db.table = self.TABLE
        db.create(num=-1, square=1)

    def test_scale(self):

        def func(start, end):
            db = Config()
            db.table = self.TABLE
            for x in range(start, end):
                db.create(num=x, square=x*x)
            db.close()

        # Below 50 threads are created in parallel which make
        # entries in the database at the same time by adding the
        # square of 5 numbers (each) at the same time.
        workers = []
        for i in range(int(self.SQUARE_NUM_UPTO / 5)):
            start, end = i*5, i*5 + 5
            t = threading.Thread(target=func, args=(start, end))
            workers.append(t)
            t.start()

        _ = [t.join() for t in workers]

        db = Config()
        db.table = self.TABLE

        # read all the records and check that entries were made for all
        # of them.
        recs = db.read()
        # print (sorted(recs))
        keys = [x for x, _ in recs]
        # print(sorted(keys))
        assert all([x in keys for x in range(self.SQUARE_NUM_UPTO)])

    def test_context(self):
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
        with db.getContext() as db:
            recs = db.read(tbl=db.TABLE, num=-2)
            self.assertEqual(len(recs), 1)

    def tearDown(self):
        os.remove(DB_NAME)
