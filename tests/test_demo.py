import pytest
import re
import asyncio
from django.urls import reverse
import django


# ─────────────────────────────────────────────────────────────────────────────
# Utility – strip ANSI colour codes from captured output
# ─────────────────────────────────────────────────────────────────────────────
def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


@pytest.fixture(autouse=True)
def setup_django_middleware(settings):
    settings.MIDDLEWARE = [
        "django.middleware.common.CommonMiddleware",
        "sql_inspect.middleware.SQLInspectMiddleware",
    ]
    settings.DEBUG = True
    settings.SQL_INSPECT_CACHE_SIZE = 10
    settings.SQL_INSPECT_STREAMING_THRESHOLD = 5
    settings.SQL_INSPECT_BATCH_SIMILAR = True
    settings.SQL_INSPECT_SHOW_INDIVIDUAL = True
    settings.SQL_INSPECT_LAZY_EVAL = True
    django.setup()


# ════════════════════════════════════════════════════════════════════════════
#  S Y N C   M I D D L E W A R E   T E S T S
# ════════════════════════════════════════════════════════════════════════════
@pytest.mark.django_db
@pytest.mark.urls("demo_app.urls")
class TestSQLInspectSync:
    def test_basic_query_output(self, client, capsys):
        url = reverse("test_demo") + "?query_count=3"
        response = client.get(url)
        captured = strip_ansi(capsys.readouterr().out)

        assert response.status_code == 200
        assert "Total queries:" in captured
        assert "Duplicates:" in captured

    def test_batching_vs_individual(self, client, capsys, settings):
        url = reverse("test_demo") + "?query_count=4"

        # Batching ON → expect "Pattern 1:"
        client.get(url)
        captured = strip_ansi(capsys.readouterr().out)
        assert "Pattern 1:" in captured

        # Batching OFF → expect individual query lines
        settings.SQL_INSPECT_BATCH_SIMILAR = False
        client.get(url)
        captured = strip_ansi(capsys.readouterr().out)
        assert re.search(r"Total time:\s*\d+\.\d+s", captured)

    def test_streaming_threshold(self, client, capsys, settings):
        high_query_count = settings.SQL_INSPECT_STREAMING_THRESHOLD + 2
        url = reverse("test_demo") + f"?query_count={high_query_count}"
        client.get(url)
        captured = strip_ansi(capsys.readouterr().out)
        assert "Total queries:" in captured

    def test_cache_effectiveness(self, client, capsys):
        url = reverse("test_demo") + "?query_count=2"
        client.get(url)  # first hit – warm cache
        capsys.readouterr()  # clear buffer

        client.get(url)  # second hit – should hit cache
        captured = strip_ansi(capsys.readouterr().out)
        assert "Duplicates:" in captured
