# sql_inspect/__init__.py
from .middleware import SQLInspectMiddleware
from ._core import analyze_queries

__all__ = ["SQLInspectMiddleware", "analyze_queries"]
