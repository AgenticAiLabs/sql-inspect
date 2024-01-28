import json
from django.shortcuts import render
from .models import Product
from django.http import JsonResponse
from django.core.serializers import serialize


# Create your views here.
def Home(request):
    qs = Product.objects.all()
    serialized_data = serialize("json", qs)
    serialized_data = json.loads(serialized_data)

    print("seriela: ", serialized_data)

    return JsonResponse({"status": "success", "data": serialized_data}, status=200)
