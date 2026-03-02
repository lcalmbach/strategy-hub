from iommi import Column

from core.iommi import icon_delete_column, icon_edit_column, login_required_crud_paths
from .models import Person


AUDIT_FIELDS = ["created_at", "updated_at", "created_by", "updated_by"]


person_crud = login_required_crud_paths(
    model=Person,
    table__title="Personen",
    table__page_size=25,
    table__columns__first_name=Column(
        display_name="Vorname",
        attr="user__first_name",
        after="last_name",
        cell__value=lambda row, **_: row.user.first_name,
        sortable=False,
        filter__include=True,
    ),
    table__columns__last_name=Column(
        display_name="Nachname",
        after="edit",
        attr="user__last_name",
        cell__value=lambda row, **_: row.user.last_name,
        sortable=False,
        filter__include=True,
    ),
    table__columns__short_code__display_name="Kuerzel",
    table__columns__short_code__after="first_name",
    table__columns__short_code__include=True,
    table__columns__function_title__display_name="Funktion",
    table__columns__function_title__after="short_code",
    table__columns__function_title__include=True,
    table__columns__user__filter__include=True,
    table__columns__short_code__filter__include=True,
    table__columns__function_title__filter__include=True,
    table__columns__organizational_unit__filter__include=True,
    table__columns__is_active_profile__filter__include=True,
    table__columns__id__include=False,
    table__columns__user__include=False,
    table__columns__organizational_unit__include=False,
    table__columns__is_active_profile__include=False,
    table__columns__created_at__include=False,
    table__columns__updated_at__include=False,
    table__columns__created_by__include=False,
    table__columns__updated_by__include=False,
    table__columns__last_name__cell__url=lambda row, **_: f"/people/{row.pk}/",
    table__columns__edit=icon_edit_column(after=0, cell__url=lambda row, **_: f"/people/{row.pk}/edit/"),
    table__columns__delete=icon_delete_column(after="function_title", cell__url=lambda row, **_: f"/people/{row.pk}/delete/"),
    create__title="Person erfassen",
    create__auto__exclude=AUDIT_FIELDS,
    edit__title="Person bearbeiten",
    edit__auto__exclude=AUDIT_FIELDS,
    detail__title=lambda form, **_: str(form.instance),
    detail__auto__exclude=AUDIT_FIELDS,
    delete__title=lambda form, **_: f"Person loeschen: {form.instance}",
)
