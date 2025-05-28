import pytest
import re
from sql_inspect import inspect_queries


def strip_ansi(text):
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


@pytest.mark.parametrize(
    "queries,batch_similar,expected_counts",
    [
        (
            [{"sql": "SELECT 1", "time": 0.01}],
            False,
            {"total": 1, "duplicates": 0, "unique": 1},
        ),
        (
            [{"sql": "SELECT 1", "time": 0.01}, {"sql": "SELECT 1", "time": 0.02}],
            False,
            {"total": 2, "duplicates": 1, "unique": 1},
        ),
        (
            [{"sql": "SELECT 1", "time": 0.01}, {"sql": "SELECT 1", "time": 0.02}],
            True,
            {"total": 2, "duplicates": 1, "unique": 1},
        ),
        (
            [{"sql": "SELECT 1", "time": 0.01}, {"sql": "SELECT 2", "time": 0.02}],
            True,
            {"total": 2, "duplicates": 0, "unique": 2},
        ),
    ],
)
def test_inspect_queries_basic(queries, batch_similar, expected_counts):
    result = strip_ansi(inspect_queries(queries, batch_similar=batch_similar))

    if batch_similar:
        assert f"Total queries: {expected_counts['total']}" in result
        assert (
            f"Unique query patterns: {expected_counts['unique']}" in result
            or f"Unique queries: {expected_counts['unique']}" in result
        )
        if "Duplicates" in result:
            assert f"Duplicates: {expected_counts['duplicates']}" in result
    else:
        for i in range(expected_counts["total"]):
            assert f"Query {i+1}:" in result


def test_inspect_queries_empty_list():
    result = strip_ansi(inspect_queries([], batch_similar=True))
    assert "Total queries: 0" in result
    assert "Unique queries: 0" in result or "Unique query patterns: 0" in result
    assert "Duplicates: 0" in result


def test_inspect_queries_query_normalization():
    queries = [
        {"sql": "SELECT * FROM table WHERE id = 1", "time": 0.01},
        {"sql": "SELECT * FROM table WHERE id = 2", "time": 0.02},
        {"sql": "SELECT * FROM table WHERE id = 3", "time": 0.03},
    ]
    result = strip_ansi(
        inspect_queries(
            queries,
            batch_similar=True,
            collapse_numeric_literals=True,  # Fix: enable numeric normalization
        )
    )
    assert "Total queries: 3" in result
    assert "Unique query patterns: 1" in result or "Unique queries: 1" in result
    assert "Duplicates: 2" in result


def test_inspect_queries_formatting_and_timing_aggregation():
    queries = [
        {"sql": "SELECT * FROM users WHERE active = true", "time": 0.01},
        {"sql": "SELECT * FROM users WHERE active = true", "time": 0.03},
        {"sql": "SELECT * FROM users WHERE active = false", "time": 0.02},
    ]
    result = strip_ansi(inspect_queries(queries, batch_similar=True))
    assert "Total time:" in result
    assert "Avg time:" in result
    assert "Min/Max:" in result
