#!/bin/env/python
'''
A simple sanity test for sql30 module.

If this module runs on your platform ( UNIX, WINDOWS, ESX etc.) you can use
this module.

USAGE: 
     python -msql30.tests.sanity
'''
import os
import sqlite3
import sys
import unittest

from sql30 import db


class Reviews(db.Model):
    TABLE = 'reviews'
    PKEY = 'rid'
    DB_SCHEMA = {
        'db_name': 'reviews.db',
        'tables': [
            {
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


# It should be a unittest testcase but module has no dependency on
# unittest module. On some platforms like ESX, if unittest module is
# not ported yet, this sanity check will fail. To handle that, it is
# shown as pure python test case.
class TestReviews(unittest.TestCase):
# class TestReviews(object):

    DB_NAME = './test_reviews.db'

    def setUp(self):
        self._delete_db()

    def tearDown(self):
        self._delete_db()

    def _delete_db(self):
        if os.path.exists(self.DB_NAME):
            os.remove(self.DB_NAME)

    def _print_all(self, db, tbl):
        results = db.read(tbl, include_header=True)
        rstrs = [[str(i) for i in x] for x in results]
        maxlen = max([max([len(i) for i in k]) for k in rstrs])

        print('-' * maxlen * len(rstrs[0]))
        for val in rstrs[0]:
            sys.stdout.write("%-*s" % (maxlen, val))

        for line in rstrs[1:]:
            print('\n', flush=True)
            for val in line:
                sys.stdout.write("%-*s" % (maxlen, val))
        print('\n\n', flush=True)

    def test_simple(self):
        db = Reviews(db_name=self.DB_NAME)

        tbl = 'reviews'

        print("Adding two records with in reviews table.")
        db.write(tbl, rid=1, header='good thing', rating=5)
        db.write(tbl, rid=2, header='bad thing', rating=1,
                 desc='what a disgusting thing')

        print("Printing record with id: 1")
        results = db.read(tbl, rid=1)
        print(results)

        # TEST CASE : check LIMIT keyword works.
        recs = db.read(tbl, LIMIT=1)
        assert len(recs) == 1, "LIMIT 1 didn't give 1 row"

        # TEST CASE 1 : Error when trying to add a record with same primary key
        try:
            print("Trying to create a new record with duplicate id 1")
            db.write(tbl, rid=1, header='good thing', rating=5)
        except sqlite3.IntegrityError as err:
            assert 'UNIQUE constraint failed: reviews.rid' in err.args

        # TEST CASE 2: Delete a record with primary key = 1
        self._print_all(db, tbl)
        print("Deleting record with id '1'")
        db.remove(tbl, rid=1)
        self._print_all(db, tbl)

        # TEST CASE 3: Delete a record with primary key = 2
        where = {'rid': 2}

        print("Updating record with id '2'")
        db.update(tbl, condition=where,
                  header='average item',
                  rating=2)
        self._print_all(db, tbl)

        # TEST CASE 4: Add the record again.
        print("Adding record with id '1' again.")
        db.write(tbl, rid=1, header='good thing', rating=5)
        self._print_all(db, tbl)

        db.close()


def main():
    obj = TestReviews()
    obj.setUp()
    obj.test_simple()
    obj.tearDown()


if __name__ == '__main__':
    main()
