from django.http import HttpResponse
from .models import Product


def test_endpoint(request):
    query_count = int(request.GET.get("query_count", 1))
    qs = None
    for _ in range(query_count):
        qs = Product.objects.all()
        qs = qs.count()
    return HttpResponse(qs)


async def test_endpoint_async(request):
    query_count = int(request.GET.get("query_count", 1))

    for _ in range(query_count):
        # Perform DB access in async-compatible way
        await Product.objects.all().aexists()

    return HttpResponse("OK")
