# scale.py
import os
import threading
import unittest

from sql30 import db

DB_NAME = 'config.db'


class Config(db.Model):
    TABLE = 'config'
    PKEY = 'rid'
    DB_SCHEMA = {
        'db_name': DB_NAME,
        'tables': [
            {
                'name': TABLE,
                'fields': {
                    'cid': 'int',
                    'value': 'int',
                    },
                'primary_key': PKEY
            }]
        }
    VALIDATE_BEFORE_WRITE = True


class ScaleTest(unittest.TestCase):

    SQUARE_NUM_UPTO = 250   # make it multiple of 5

    def setUp(self):
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)

        db = Config()
        db.table = 'config'
        db.create(cid=-1, value=1)

    def test_scale(self):

        def func(start, end):
            db = Config()
            db.table = 'config'
            for x in range(start, end):
                db.create(cid=x, value=x*x)
            db.commit()

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
        db.table = 'config'

        # read all the records and check that entries were made for all
        # of them.
        recs = db.read()
        keys = [x for x, _ in recs]
        # print(sorted(keys))
        assert all([x in keys for x in range(self.SQUARE_NUM_UPTO)])

    def tearDown(self):
        os.remove(DB_NAME)