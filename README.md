This is the test version of the sql-inspect package. It inspect view request to database
and print the SQL translation of the queries to the terminal.

## Installation

include the middleware in the settings.py file as specified below:

```
MIDDLEWARE = [
    ...,
    "sql-inspect.middleware.SQLInspectMiddleware"
]
```