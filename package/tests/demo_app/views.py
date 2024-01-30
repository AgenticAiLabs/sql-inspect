from django.http import HttpResponse
from .models import Product


def test_endpoint(request):
    qs = Product.objects.all()

    return HttpResponse(qs)
