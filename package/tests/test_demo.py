from demo_app.models import Product
from django.urls import reverse
import pytest
import sys


@pytest.mark.django_db
@pytest.mark.urls("demo_app.urls")
class TestDemoAPP:
    @pytest.fixture(scope="function")
    def initial_setup(self, client, settings, capsys):
        """perform initial setup for the test"""

        def _setup(query_count=1, debug=True):
            """perform initial setup based on passed args"""

            settings.DEBUG = debug
            url = reverse("test_demo") + f"?query_count={query_count}"

            self.response = client.get(url)
            self.captured_stdout = capsys.readouterr()

        return _setup

    def test_product(self, initial_setup):
        """test the url http endpoint status"""

        initial_setup()
        assert self.response.status_code == 200

    def test_stdout(self, initial_setup):
        """tests the middleware output in stdout"""

        initial_setup()
        assert "Number of query(s): 1" in self.captured_stdout.out

    def test_duplicate_stdout(self, initial_setup):
        """tests the middleware output in stdout for duplicates"""

        initial_setup(query_count=2)
        assert "Number of duplicates: 1" in self.captured_stdout.out
