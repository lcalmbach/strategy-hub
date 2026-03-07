from django.urls import include, path

from .views import function_crud, organization_crud, person_crud


app_name = "people"

urlpatterns = [
    path("functions/", include(function_crud)),
    path("organizations/", include(organization_crud)),
    *person_crud,
]
