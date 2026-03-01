from django.urls import include, path

from .views import period_crud, record_crud, record_responsibility_crud


app_name = "controlling"

urlpatterns = [
    path("periods/", include(period_crud)),
    path("records/", include(record_crud)),
    path("responsibilities/", include(record_responsibility_crud)),
]
