from django.http import HttpResponse
from .models import Product


def test_endpoint(request):
    query_count = request.GET.get("query_count", 1)

    qs = None
    for i in range(int(query_count)):
        qs = Product.objects.all()
        qs = qs.count()

    return HttpResponse(qs)
