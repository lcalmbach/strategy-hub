from django.contrib import admin

from .models import Person


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("short_code", "function_title", "organizational_unit", "is_active_profile")
    search_fields = ("short_code", "function_title", "user__username")
