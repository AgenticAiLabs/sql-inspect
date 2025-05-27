"""
sql_inspect.middleware
======================

Lightweight middleware integration for Django that defers importing
heavy dependencies (like SQL parsing and formatting libraries) until first use.

To use, point Django’s MIDDLEWARE setting at this symbol:

    'sql_inspect.middleware.SQLInspectMiddleware'

This middleware is designed to be used in development only — it
only activates when `settings.DEBUG` is `True`.
"""

from __future__ import annotations
from typing import Callable
from django.conf import settings


def _lazy_load():
    """
    Lazily imports the core module to avoid slow startup times.
    """
    from . import _core  # noqa: E402
    return _core


def SQLInspectMiddleware(get_response: Callable):
    """
    Django middleware to inspect SQL queries after each request.

    When `DEBUG = True`, this middleware will:
    - Collect SQL queries from Django’s DB connection.
    - Group and analyze them (optionally by similarity).
    - Output a formatted and highlighted summary to stdout.

    Args:
        get_response: The next middleware or view in the Django stack.

    Returns:
        A callable that wraps the request/response lifecycle.
    """
    core = _lazy_load()
    config = core.SQLInspectConfig()
    cache = core.get_query_cache(config)
    outputter = core.StreamingOutputter(config.streaming_threshold)

    log_func = print

    def middleware(request):
        response = get_response(request)
        if settings.DEBUG:
            core._process_queries(config, cache, outputter, log_func)
        return response

    return middleware
