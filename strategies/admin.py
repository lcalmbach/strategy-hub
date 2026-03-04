from django.contrib import admin

from .models import MeasureResponsibility, MeasureType, Strategy, StrategyLevel


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = ("sort_order", "short_code", "title", "status", "valid_from", "valid_until", "is_active")
    list_filter = ("status", "is_active")
    search_fields = ("short_code", "title", "short_description")


@admin.register(MeasureType)
class MeasureTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "label", "is_active")
    search_fields = ("code", "label")


@admin.register(StrategyLevel)
class StrategyLevelAdmin(admin.ModelAdmin):
    list_display = ("title", "strategy", "level", "parent", "short_code", "status", "start_date", "end_date")
    list_filter = ("level", "strategy", "status")
    search_fields = ("title", "short_code")


@admin.register(MeasureResponsibility)
class MeasureResponsibilityAdmin(admin.ModelAdmin):
    list_display = ("measure", "person", "role", "valid_from", "valid_until")
    list_filter = ("role",)
    search_fields = ("measure__title", "person__short_code")
