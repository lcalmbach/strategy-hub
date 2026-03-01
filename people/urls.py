from django.urls import path

from .views import person_crud


app_name = "people"

urlpatterns = [
    *person_crud,
]
