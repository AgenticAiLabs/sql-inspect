# SQL-Inspect

The SQ:-Inspect package is a django middleware that inspects view request to database
and print the SQL translation of the queries to the terminal.

## Installation

include the middleware in the settings.py file as specified below:

```
MIDDLEWARE = [
    ...,
    "sql-inspect.middleware.SQLInspectMiddleware"
]
```