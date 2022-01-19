[![Downloads](https://pepy.tech/badge/sql30)](https://pepy.tech/project/sql30)

# SQL30

sql30 is a zero weight ORM for sqlite3 in Python. 

It is written using pure python constructs and has no dependency on any other module. There is no `requirements.txt` in the project in fact. Having zero dependency on any other module makes this package usable on variety of platforms including the ones which have limited or delayed support such as ESX.


## Usage


SQL30 is incredibly simple to use. 

All it requires is to define your database schema using a simple JSON. Then, pre-defined interface can be used to perform CRUD operations. As is true for any ORM, user doesn't need to know how the operations are translated back to SQL statements for `sqlite3`. 

In the schema,
- Database filename is provided using the key `db_name`.
- Multiple tables can be defined under `tables` key in JSON.
- Fields / Columns for each table are added using `fields` key in JSON. Field name and it's type is provided as key value pair again.
- Primary Key for each table can be defined using key `primary_key`

Let's take an example. 

### Example

Let's say we have to store the reviews of a product in database and we chose sqlite3 for the purpose. Using SQL30, a sample schema can be defined as shown below.


```python

# reviews.py
from sql30 import db

class Reviews(db.Model):
    TABLE = 'reviews'
    PKEY = 'rid'
    DB_SCHEMA = {
        'db_name': './reviews.db',
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

```

Now, we can create instance of Review and that will handle CRUD operations to database for us. 

```python
>>> import os
>>> import reviews

# delete old database if you want to
>>> os.remove('reviews.db')

# Create ORM layer object instance.
>>> db = reviews.Reviews()

# With this, we can create/write records to db as following.
>>> db.tbl = 'reviews' # Select database table, for all the future CRUD operations.
                       # You can switch between tables in case of multiple tables in DB.
>>> db.write(rid=1, header='good thing', rating=5)
>>> db.write(header='bad thing', rid=2, rating=1, desc='what a disgusting thing')

# We can then read back the records individually are as whole as shown below.

# To read all the records from a table, simply pass the table name.
>>> db.read()
[(1, 'good thing', 5, ''), (2, 'bad thing', 1, 'what a disgusting thing')]

# To read the records from table, simply pass on the condition as params.
>>> db.read(rid=1) # Get records from table WHERE rid=1
[(1, 'good thing', 5, '')]

# Get records from table WHERE rid=1 and rating=3. Note that, there is no
# restriction on the order in which condition needs to be provided. Only
# the param name should be one of the COLUMN(s) in table.
>>> db.read(rating=3, rid=1)
[]
>>> db.read(rating=5, rid=1)
[(1, 'good thing', 5, '')]

# If we try to add another record with same primary key, it will error out.
>>> db.write(rid=1, header='good thing', rating=5)
Traceback (most recent call last):
  ...
  ...
sqlite3.IntegrityError: UNIQUE constraint failed: reviews.rid

# Updating the record is also possible by providing condition for records and updated values.
>>> where = {'rid': 2}
>>> db.update(condition=where, header='average item', rating=2)
>>> db.read()
[(1, 'good thing', 5, ''), (2, 'average item', 2, 'what a disgusting thing')]

# Deleteing the records is possble with any level of filtering.
>>> db.remove(rid=1)
>>> db.read()
[(2, 'average item', 2, 'what a disgusting thing')]

# At this point, however, all of your records are being maintained by SQLITE in-memory.
# However, commit API can be used to persist them in the DB file.
>>> db.commit()
```

## Browsing Database Contents

SQLITE database can be browsed a couple of ways. Some of these are mentioned here.

### sql30 server
Traditionally, `sqlite3` has been used to browse database contents. However `sql30` comes with a utility that helps you browse contents of your SQLITE database in your favorite browser. SQL30 essentially reads the contents of your database, builds schema from it and then runs a HTTP server that responds to HTTP API requests to server contents of specific tables. Example below explains it further.

##### Database Browsing Example

```bash
git clone http://github.com/gitvipin/sql30.git
cd sql30
# General sample sqlite3 DB file.
python3 -msql30.tests.sanity -x
# Serve the contents of database on HTTP server.
python3 -msql30.cmd  -s  -p 8008 -x -d ./test_reviews.db
```

Once above steps are run successfuly, you can browse data from your browser on http://localhost:8008/tables/reviews

![SQL30 Browser](https://github.com/gitvipin/sql30/blob/master/sql30/doc/sql30.png)

### sqlite3
Using `sqlite` utility is a common method users like to look down at DB contents. Example below throws some light on this. More commands on SQLITE3 CLI can be found here: https://sqlite.org/cli.html .

```bash
(LPAD) root@Pali/tmp/LPAD$ sqlite3 reviews.db
SQLite version 3.22.0 2018-01-22 18:45:57
Enter ".help" for usage hints.
sqlite> .header on
sqlite> .column on
sqlite> select * from reviews;
header      rid         desc        rating
----------  ----------  ----------  ----------
average it  2           what a dis  2
sqlite> .quit
(LPAD) root@Pali/tmp/LPAD$
```

Other option is to install sqlite extensions in your code editors if they support it. Visual Studio Code is one that has extension for it.


## Installation

Fetching / Installing SQL30 is simple. Easiest way to consume sql30 is by installing it from pypi server (https://pypi.org/project/sql30/) by running following command. 

```
pip install sql30
```

However, if your machine doesn't have access to pypi server, it is easy to get and build a wheel for SQL30 from a machine which has access to pypi server. 
Following are the steps for the same. 

```
$ virtualenv -p python3 . 
$ mkdir unpacked
$ bin/pip install --target=./unpacked/ sql30
$ cd unpacked
$ zip -r9 ../sql30.egg *
$ cd -
# 
```

sql30.egg file generated by above steps can now be taken and used with any machine with python3 and sqlite3 (python module) available. An example of the same is shown below. Here sql30.egg is being taken to an ESX Hypervisor with a Python 3.5.6 version and shown to consume egg file. 

```
[root@prom-0505695d9ce:~] PYTHONPATH=sql30.egg python
Python 3.5.6 (default, Feb  2 2019, 01:09:51)
[GCC 4.6.3] on linux
Type "help", "copyright", "credits" or "license" for more information.
No entry for terminal type "screen.xterm-256color";
using dumb terminal settings.
>>> from sql30 import db
>>> import os
>>> os.system('uname -a')
VMkernel prom-0505695d9ce.xyz.test 6.5.0 #1 SMP Release build-13753126 May 19 2019 21:13:25 x86_64 x86_64 x86_64 ESXi
0
>>> class Dummy(db.Model):
...     pass
...
>>> dir(Dummy)
['DB_SCHEMA', 'VALIDATE_BEFORE_WRITE', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_form_constraints', '_get_fields', '_get_schema', '_validate_bfr_write', 'close', 'commit', 'create_table', 'cursor', 'init_db', 'read', 'remove', 'table_exists', 'update', 'write']
```

## Repository

https://github.com/gitvipin/sql30 


## Requirements

Python 3.4+

Share and enjoy!