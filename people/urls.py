from django.urls import include, path

from .views import function_crud, person_crud


app_name = "people"

urlpatterns = [
    path("functions/", include(function_crud)),
    *person_crud,
]
