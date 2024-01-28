import json
from django.shortcuts import render
from .models import Product
from django.http import JsonResponse
from django.core.serializers import serialize


def Home(request):
    qs = Product.objects.all()

    serialized_data = serialize("json", qs)

    ww = Product.objects.all()
    ss = serialize("json", ww)
    
    serialized_data = json.loads(serialized_data)

    return JsonResponse(serialized_data, safe=False, status=200)
