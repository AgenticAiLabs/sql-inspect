from django.urls import path
from . import views


urlpatterns = [path("", views.test_endpoint, name="test_demo")]
