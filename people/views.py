from iommi import Column

from core.iommi import login_required_crud_paths
from .models import Person


AUDIT_FIELDS = ["created_at", "updated_at", "created_by", "updated_by"]


person_crud = login_required_crud_paths(
    model=Person,
    table__title="Personen",
    table__page_size=25,
    table__columns__user__filter__include=True,
    table__columns__short_code__filter__include=True,
    table__columns__function_title__filter__include=True,
    table__columns__organizational_unit__filter__include=True,
    table__columns__is_active_profile__filter__include=True,
    table__columns__id__include=False,
    table__columns__user__cell__url=lambda row, **_: f"/people/{row.pk}/",
    table__columns__edit=Column.edit(after=0, cell__url=lambda row, **_: f"/people/{row.pk}/edit/"),
    table__columns__delete=Column.delete(cell__url=lambda row, **_: f"/people/{row.pk}/delete/"),
    create__title="Person erfassen",
    create__auto__exclude=AUDIT_FIELDS,
    edit__title="Person bearbeiten",
    edit__auto__exclude=AUDIT_FIELDS,
    detail__title=lambda form, **_: str(form.instance),
    detail__auto__exclude=AUDIT_FIELDS,
    delete__title=lambda form, **_: f"Person loeschen: {form.instance}",
)
