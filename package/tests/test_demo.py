from demo_app.models import Product
from django.urls import reverse
import pytest


@pytest.mark.django_db
@pytest.mark.urls("demo_app.urls")
class TestDemoAPP:
    def test_product(self, client, settings):
        settings.DEBUG = True
        url = reverse("test_demo")

        response = client.get(url)
        print(response)

        assert response.status_code == 200
        qs = Product.objects.all().count()

        assert qs == 0
