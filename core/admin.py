from django.contrib import admin

from .models import Code, CodeCategory, InitiativeRoleCode, InitiativeStatusCode


@admin.register(CodeCategory)
class CodeCategoryAdmin(admin.ModelAdmin):
    list_display = ("sort_order", "key", "name")
    search_fields = ("key", "name")


@admin.register(Code)
class CodeAdmin(admin.ModelAdmin):
    list_display = ("category", "sort_order", "code", "name", "short_name")
    list_filter = ("category",)
    search_fields = ("code", "name", "short_name", "category__name", "category__key")


@admin.register(InitiativeStatusCode)
class InitiativeStatusCodeAdmin(admin.ModelAdmin):
    list_display = ("sort_order", "code", "name", "short_name")
    search_fields = ("code", "name", "short_name")


@admin.register(InitiativeRoleCode)
class InitiativeRoleCodeAdmin(admin.ModelAdmin):
    list_display = ("sort_order", "code", "name", "short_name")
    search_fields = ("code", "name", "short_name")
