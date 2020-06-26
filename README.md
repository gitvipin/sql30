# Sql30

sql30 is a zero weight ORM for sqlite3 in Python. 

It is written using pure python constructs and has no dependency on any other module. There is no `requirements.txt` in the project in fact. Having zero dependency on any other module makes this package usable on variety of platforms including the ones which have limited or delayed support such as ESX.


Usage
------------

SQL30 is incredibly simple to use. 

All it requires is to define your database schema using a simple JSON. Then, pre-defined interface can be used to perform CRUD operations. As is true for any ORM, user doesn't need to know how the operations are translated back to SQL statements for `sqlite3`. 

In the schema,
- Database filename is provided using the key `db_name`.
- Multiple tables can be defined under `tables` key in JSON.
- Fields / Columns for each table are added using `fields` key in JSON. Field name and it's type is provided as key value pair again.
- Primary Key for each table can be defined using key `primary_key`

Let's take an example. 

Example

Let's say we have to store the reviews of a product in database and we chose sqlite3 for the purpose. Using SQL30, a sample schema can be defined as shown below.


```python

# reviews.py
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
>>> db.write(tbl, rid=1, header='good thing', rating=5)
>>> db.write(tbl, rid=2, header='bad thing', rating=1, desc='what a disgusting thing')

# We can read back the records as shown below.
>>> tbl = 'reviews'
>>> results = db.read(tbl, rid=1)

# Querying over the records is possble as below.
>>> results = db.read(tbl, rating=3, rid=1)

# If we try to add another record with same primary key, it will error out.
>>> db.write(tbl, rid=1, header='good thing', rating=5)

# Updating the record is also possible by providing condition for records and updated values.
>>> where = {'rid': 2}
>>> db.update(tbl, condition=where, header='average item', rating=2)

# Deleteing the records is possble with any level of filtering.
>>> db.remove(tbl, rid=1)
```


Repository
------------
https://github.com/gitvipin/sql30 


Requirements
------------
Python 3.4+

Share and enjoy!
