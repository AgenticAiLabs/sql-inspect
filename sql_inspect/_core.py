"""
sql_inspect.core
================

Core engine for SQL-Inspect: caching, batching, formatting, and streaming query insights.
Designed to be imported lazily to keep Django startup light.

Only the `analyze_queries` function is intended for public use; all other
components are used internally by the middleware or for advanced usage.

Usage:
    from sql_inspect.core import analyze_queries
"""

from __future__ import annotations

import hashlib
import threading
import weakref
from collections import defaultdict
from typing import Dict, Iterator, List, Optional

from django.conf import settings
from django.db import connection
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers.sql import SqlLexer
from sqlparse import format as sql_format


# Internal cache store
_cache_instances: weakref.WeakValueDictionary[int, QueryCache] = weakref.WeakValueDictionary()
_strong_cache_refs: dict[int, QueryCache] = {}


def get_query_cache(config: SQLInspectConfig) -> QueryCache:
    """
    Returns a singleton-style instance of QueryCache, sized based on config.
    """
    size = getattr(config, "cache_size", 1000) if config else 1000

    if size in _strong_cache_refs:
        return _strong_cache_refs[size]

    cache = _cache_instances.get(size)
    if cache is None:
        cache = QueryCache(max_size=size)
        _cache_instances[size] = cache
        _strong_cache_refs[size] = cache
    return cache


class QueryCache:
    """
    Thread-safe LRU cache for formatted SQL queries.

    Attributes:
        max_size: Maximum number of cached entries.
    """

    def __init__(self, max_size: int = 1000) -> None:
        self.max_size = max_size
        self._cache: dict[str, str] = {}
        self._access_order: list[str] = []
        self._lock = threading.RLock()

    def _hash(self, sql: str) -> str:
        return hashlib.md5(sql.encode("utf-8")).hexdigest()

    def get(self, sql: str) -> Optional[str]:
        """
        Retrieves the formatted SQL from cache, if available.
        """
        h = self._hash(sql)
        with self._lock:
            if h in self._cache:
                self._access_order.remove(h)
                self._access_order.append(h)
                return self._cache[h]
        return None

    def set(self, sql: str, formatted: str) -> None:
        """
        Stores formatted SQL in cache, evicting LRU if needed.
        """
        h = self._hash(sql)
        with self._lock:
            if h in self._cache:
                self._access_order.remove(h)
            elif len(self._cache) >= self.max_size:
                lru = self._access_order.pop(0)
                self._cache.pop(lru, None)
            self._cache[h] = formatted
            self._access_order.append(h)


class LazyQuery:
    """
    Wraps a SQL query for lazy formatting and syntax highlighting.

    Attributes:
        sql: Raw SQL string.
        time: Execution time as string.
    """

    def __init__(self, qdata: dict, cache: QueryCache) -> None:
        self.sql: str = qdata["sql"]
        self.time: str = qdata["time"]
        self._cache = cache
        self._formatted: Optional[str] = None
        self._highlighted: Optional[str] = None

    @property
    def formatted_sql(self) -> str:
        """
        Returns pretty-formatted SQL with indentation.
        Uses cache if available.
        """
        if self._formatted is None:
            self._formatted = self._cache.get(self.sql)
            if not self._formatted:
                self._formatted = sql_format(self.sql, reindent=True)
                self._cache.set(self.sql, self._formatted)
        return self._formatted

    @property
    def highlighted_sql(self) -> str:
        """
        Returns syntax-highlighted SQL using Pygments.
        """
        if self._highlighted is None:
            self._highlighted = highlight(
                self.formatted_sql, SqlLexer(), TerminalFormatter()
            )
        return self._highlighted

    def get_signature(self) -> str:
        """
        Normalizes SQL query into a pattern for duplicate detection.
        """
        import re
        s = self.sql.strip().upper()
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r"'[^']*'", "'?'", s)
        return s


class QueryBatch:
    """
    Groups similar queries and aggregates their timing statistics.

    Attributes:
        signature: Normalized signature of query pattern.
        queries: List of LazyQuery objects.
    """

    def __init__(self, signature: str) -> None:
        self.signature = signature
        self.queries: List[LazyQuery] = []
        self.total_time = 0.0

    def add(self, q: LazyQuery) -> None:
        """
        Adds a LazyQuery to the batch and updates total time.
        """
        self.queries.append(q)
        self.total_time += float(q.time)

    @property
    def count(self) -> int:
        return len(self.queries)

    @property
    def avg_time(self) -> float:
        return self.total_time / self.count if self.count else 0.0

    @property
    def min_time(self) -> float:
        return min(float(q.time) for q in self.queries) if self.queries else 0.0

    @property
    def max_time(self) -> float:
        return max(float(q.time) for q in self.queries) if self.queries else 0.0


class StreamingOutputter:
    """
    Yields lines summarizing SQL query statistics or details.
    """

    def __init__(self, threshold: int = 100) -> None:
        self.threshold = threshold

    def output(
        self, batches: Dict[str, QueryBatch], show_individual: bool = True
    ) -> Iterator[str]:
        yield "=" * 30
        yield "[ SQL Query Stats ]"
        yield "=" * 30 + "\n"

        total = sum(b.count for b in batches.values())
        uniq = len(batches)

        yield f"Total queries: {total}"
        yield f"Unique query patterns: {uniq}"
        yield f"Duplicates: {total - uniq}\n"

        for i, (_sig, b) in enumerate(
            sorted(batches.items(), key=lambda kv: kv[1].total_time, reverse=True), 1
        ):
            yield f"Pattern {i}: {b.count} executions"
            yield f"Total time: {b.total_time:.4f}s"
            yield f"Avg time: {b.avg_time:.4f}s"
            yield f"Min/Max: {b.min_time:.4f}s / {b.max_time:.4f}s"

            if show_individual and b.count <= 5:
                yield "Example query:"
                yield b.queries[0].highlighted_sql
            else:
                yield "Query pattern:"
                yield b.signature

            yield "-" * 30 + "\n"


class SQLInspectConfig:
    """
    Configuration loader for SQL Inspect.

    Reads Django settings and applies defaults for cache, batching, etc.
    """

    def __init__(self) -> None:
        self.cache_size = getattr(settings, "SQL_INSPECT_CACHE_SIZE", 1000)
        self.streaming_threshold = getattr(settings, "SQL_INSPECT_STREAMING_THRESHOLD", 100)
        self.batch_similar = getattr(settings, "SQL_INSPECT_BATCH_SIMILAR", True)
        self.show_individual = getattr(settings, "SQL_INSPECT_SHOW_INDIVIDUAL", True)
        self.lazy_evaluation = getattr(settings, "SQL_INSPECT_LAZY_EVAL", True)


def _emit(lines: Iterator[str], log_func) -> None:
    for ln in lines:
        log_func(ln)


def _process_queries_shared(
    cfg: SQLInspectConfig,
    cache: QueryCache,
    out: StreamingOutputter,
    log_func,
) -> None:
    """
    Internal function: processes queries from Django's connection.queries.
    """
    if not connection.queries:
        return

    lqs = [LazyQuery(q, cache) for q in connection.queries]

    if cfg.batch_similar:
        batches: Dict[str, QueryBatch] = defaultdict(lambda: QueryBatch(""))
        for q in lqs:
            sig = q.get_signature()
            if not batches[sig].signature:
                batches[sig].signature = sig
            batches[sig].add(q)
        _emit(out.output(batches, cfg.show_individual), log_func)
    else:
        seen: set[str] = set()
        log_func("=" * 30)
        log_func("[ SQL Query Stats ]")
        log_func("=" * 30 + "\n")

        for i, q in enumerate(lqs, 1):
            dup = q.sql in seen
            seen.add(q.sql)
            status = "DUPLICATE" if dup else ""
            log_func(f"Query {i}: Execution Time - ({q.time}s). {status}")
            log_func(q.highlighted_sql)

        log_func(f"Number of query(s): {len(lqs)}")
        log_func(f"Number of duplicates: {len(lqs) - len(seen)}")
        log_func("-" * 30 + "\n")


def _process_queries(
    cfg: SQLInspectConfig, cache, out, log_func=print
) -> None:
    """
    Middleware-only internal hook to inspect SQL queries after a request.
    """
    _process_queries_shared(cfg, cache, out, log_func)


def analyze_queries(
    queries: List[dict],
    *,
    batch_similar: bool = True,
    collapse_numeric_literals: bool = False,
) -> str:
    """
    Public API: Analyzes a list of SQL query dicts (mimicking Django's connection.queries).

    Args:
        queries: List of dicts with 'sql' and 'time' keys.
        batch_similar: Whether to group queries by normalized patterns.
        collapse_numeric_literals: If True, replaces numbers in queries with placeholders.

    Returns:
        str: Formatted analysis output as a string.
    """
    cfg = SQLInspectConfig()
    cache = get_query_cache(cfg)
    out = StreamingOutputter(cfg.streaming_threshold)

    if collapse_numeric_literals:
        import re

        def legacy_sig(self: LazyQuery) -> str:  # type: ignore
            s = self.sql.strip().upper()
            s = re.sub(r"\s+", " ", s)
            s = re.sub(r"\b\d+\b", "?", s)
            s = re.sub(r"'[^']*'", "'?'", s)
            return s

        LazyQuery.get_signature = legacy_sig  # type: ignore

    lqs = [LazyQuery(q, cache) for q in queries]

    if batch_similar:
        batches: Dict[str, QueryBatch] = defaultdict(lambda: QueryBatch(""))
        for q in lqs:
            sig = q.get_signature()
            if not batches[sig].signature:
                batches[sig].signature = sig
            batches[sig].add(q)
        return "\n".join(out.output(batches))
    else:
        return "\n".join(
            f"Query {i+1}: {q.time}s\n{q.highlighted_sql}" for i, q in enumerate(lqs)
        )
