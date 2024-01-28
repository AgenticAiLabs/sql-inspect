import json
from django.shortcuts import render
from .models import Product
from django.http import JsonResponse
from django.core.serializers import serialize
from django.db import connection
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers.sql import SqlLexer
from sqlparse import format


def Home(request):
    qs = Product.objects.all()
    serialized_data = serialize("json", qs)

    queries = list(connection.queries)

    for sq in queries:
        sqlformatted = format(str(sq["sql"]), reindent=True)
        sqlformatted = highlight(sqlformatted, SqlLexer(), TerminalFormatter())
        print(sqlformatted)

    serialized_data = json.loads(serialized_data)

    return JsonResponse(serialized_data, safe=False, status=200)
