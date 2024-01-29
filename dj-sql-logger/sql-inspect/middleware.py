from django.conf import settings
from django.db import connection
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers.sql import SqlLexer
from sqlparse import format


def SQLInspectMiddleware(get_response):
    def middleware(request):
        response = get_response(request)

        if settings.DEBUG:
            queries = connection.queries
            duplicates = set()
            q_num = len(queries)

            num_lines = 30

            print("=" * num_lines)
            print("[ SQL Query Stats ]")
            print("=" * num_lines, "\n")

            for i in range(q_num):
                q = queries[i]
                dup_num_initial = len(duplicates)
                sqlformatted = format(str(q["sql"]), reindent=True)

                duplicates.add(q["sql"])
                is_duplicate = "DUPLICATE" if dup_num_initial == len(duplicates) > 0 else ""
                
                sqlformatted = highlight(sqlformatted, SqlLexer(), TerminalFormatter())
                print(f"Query {i + 1}: Execution Time - ({q['time']}s). {is_duplicate}")
                print(f"{sqlformatted}\n")

            print(f"Number of query(s): {q_num}")
            print(f"Number of duplicates: {q_num - len(duplicates)}")
            print("-" * num_lines, "\n")
        
        return response

    return middleware
