from django.contrib import admin

from .models import ControllingPeriod, ControllingRecord, ControllingRecordResponsibility


@admin.register(ControllingPeriod)
class ControllingPeriodAdmin(admin.ModelAdmin):
    list_display = ("strategy","name", "start_date", "end_date", "status")
    list_filter = ("strategy", "status")
    search_fields = ("name",)


@admin.register(ControllingRecord)
class ControllingRecordAdmin(admin.ModelAdmin):
    list_display = ("measure", "period", "status", "plan_cost_chf", "actual_cost_chf")
    list_filter = ("status", "period")
    search_fields = ("measure__title", "period__name")


@admin.register(ControllingRecordResponsibility)
class ControllingRecordResponsibilityAdmin(admin.ModelAdmin):
    list_display = ("controlling_record", "person", "role")
    list_filter = ("role",)
    search_fields = ("person__short_code", "controlling_record__measure__title")
