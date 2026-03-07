from django.contrib import admin

from .models import Function, Organization, Person


@admin.register(Function)
class FunctionAdmin(admin.ModelAdmin):
    list_display = ("sort_order", "code", "label", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "label")


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("short_code", "function", "organization", "is_active_profile")
    search_fields = ("short_code", "function__code", "function__label", "user__username")


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("sort_order", "short_code", "bereich", "abteilung", "is_active")
    list_filter = ("is_active",)
    search_fields = ("short_code", "bereich", "abteilung")
