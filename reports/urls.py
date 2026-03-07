from django.urls import path

from .views import download_report, reports_page


app_name = "reports"

urlpatterns = [
    path("", reports_page, name="index"),
    path("download/<int:report_id>/", download_report, name="download"),
]
