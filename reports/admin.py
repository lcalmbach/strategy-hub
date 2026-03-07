from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description", "sql")
