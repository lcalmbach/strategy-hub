from django.urls import include, path

from .views import (
    create_missing_records_for_period,
    delete_controlling_period_direct,
    delete_controlling_record_direct,
    period_crud,
    record_crud,
    record_responsibility_crud,
)


app_name = "controlling"

urlpatterns = [
    path("periods/<pk>/delete-direct/", delete_controlling_period_direct, name="period_delete_direct"),
    path(
        "periods/<pk>/generate-missing-records/",
        create_missing_records_for_period,
        name="period_generate_missing_records",
    ),
    path("records/<pk>/delete-direct/", delete_controlling_record_direct, name="record_delete_direct"),
    path("periods/", include(period_crud)),
    path("records/", include(record_crud)),
    path("responsibilities/", include(record_responsibility_crud)),
]
