from django.urls import path, include
from .views import Home

urlpatterns = [path("", Home, name="Home")]
