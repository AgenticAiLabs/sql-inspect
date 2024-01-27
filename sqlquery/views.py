import json
from django.shortcuts import render
from .models import Product
from django.http import JsonResponse
from django.core.serializers import serialize


# Create your views here.
def Home(request):
    qs = Product.objects.all()
    serialized_data = serialize(qs)
    serialized_data = json.loads(serialized_data)

    return JsonResponse(serialized_data, status=200)
