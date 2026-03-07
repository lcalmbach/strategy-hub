from django.db.models import F
from iommi import Column

from core.iommi import icon_delete_column, icon_edit_column, login_required_crud_paths
from .models import Function, Organization, Person


AUDIT_FIELDS = ["created_at", "updated_at", "created_by", "updated_by"]


function_crud = login_required_crud_paths(
    model=Function,
    table__title="Funktionen",
    table__page_size=25,
    table__columns__id__include=False,
    table__columns__code__filter__include=True,
    table__columns__label__filter__include=True,
    table__columns__is_active__filter__include=True,
    table__columns__code__cell__url=lambda row, **_: f"/people/functions/{row.pk}/",
    create__title="Funktion erfassen",
    create__auto__exclude=AUDIT_FIELDS,
    edit__title="Funktion bearbeiten",
    edit__auto__exclude=AUDIT_FIELDS,
    detail__title=lambda form, **_: form.instance.label,
    detail__auto__exclude=AUDIT_FIELDS,
    delete__title=lambda form, **_: f"Funktion löschen: {form.instance.label}",
)


organization_crud = login_required_crud_paths(
    model=Organization,
    table__title="Organisationen",
    table__page_size=25,
    table__columns__id__include=False,
    table__columns__short_code__filter__include=True,
    table__columns__short_code__include=True,
    table__columns__bereich__filter__include=True,
    table__columns__abteilung__filter__include=True,
    table__columns__is_active__filter__include=True,
    table__columns__bereich__after="short_code",
    table__columns__bereich__cell__url=lambda row, **_: f"/people/organizations/{row.pk}/",
    create__title="Organisation erfassen",
    create__auto__exclude=AUDIT_FIELDS,
    edit__title="Organisation bearbeiten",
    edit__auto__exclude=AUDIT_FIELDS,
    detail__title=lambda form, **_: str(form.instance),
    detail__auto__exclude=AUDIT_FIELDS,
    delete__title=lambda form, **_: f"Organisation löschen: {form.instance}",
)


person_crud = login_required_crud_paths(
    model=Person,
    table__title="Personen",
    table__page_size=25,
    table__rows=lambda request, **_: Person.objects.select_related("user", "function", "organization").annotate(
        last_name_sort=F("user__last_name"),
        first_name_sort=F("user__first_name"),
    ),
    table__columns__first_name=Column(
        display_name="Vorname",
        attr="first_name_sort",
        after="last_name",
        cell__value=lambda row, **_: row.user.first_name,
        sortable=True,
        filter__include=True,
    ),
    table__columns__last_name=Column(
        display_name="Nachname",
        after="edit",
        attr="last_name_sort",
        cell__value=lambda row, **_: row.user.last_name,
        cell__url=lambda row, **_: f"/people/{row.pk}/",
        sortable=True,
        filter__include=True,
    ),
    table__columns__short_code__display_name="Kürzel",
    table__columns__short_code__after="first_name",
    table__columns__short_code__include=True,
    table__columns__function__display_name="Funktion",
    table__columns__function__after="short_code",
    table__columns__function__include=True,
    table__columns__function__cell__value=lambda row, **_: row.function.label if row.function else "",
    table__columns__function__filter__include=True,
    table__columns__organization__display_name="Organisation",
    table__columns__organization__after="function",
    table__columns__organization__include=True,
    table__columns__organization__cell__value=lambda row, **_: str(row.organization) if row.organization else "",
    table__columns__organization__filter__include=True,
    table__columns__short_code__filter__include=True,
    table__columns__is_active_profile__filter__include=True,
    table__columns__id__include=False,
    table__columns__user__include=False,
    table__columns__is_active_profile__include=False,
    table__columns__created_at__include=False,
    table__columns__updated_at__include=False,
    table__columns__created_by__include=False,
    table__columns__updated_by__include=False,
    table__columns__edit=icon_edit_column(after=0, cell__url=lambda row, **_: f"/people/{row.pk}/edit/"),
    table__columns__delete=icon_delete_column(after="function", cell__url=lambda row, **_: f"/people/{row.pk}/delete/"),
    create__title="Person erfassen",
    create__auto__exclude=AUDIT_FIELDS,
    edit__title="Person bearbeiten",
    edit__auto__exclude=AUDIT_FIELDS,
    detail__title=lambda form, **_: str(form.instance),
    detail__auto__exclude=AUDIT_FIELDS,
    delete__title=lambda form, **_: f"Person löschen: {form.instance}",
)
