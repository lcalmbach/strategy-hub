from django.contrib import admin

from .models import Function, Person


@admin.register(Function)
class FunctionAdmin(admin.ModelAdmin):
    list_display = ("sort_order", "code", "label", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "label")


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("short_code", "function", "organizational_unit", "is_active_profile")
    search_fields = ("short_code", "function__code", "function__label", "user__username")
