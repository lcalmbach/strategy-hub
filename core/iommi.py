from django.contrib.auth.decorators import login_required
from django.urls import path

from iommi import Action, Column, Form, Table
from iommi.declarative.dispatch import dispatch
from iommi.declarative.namespace import EMPTY, setdefaults_path

from core.strategy_context import require_active_strategy


def icon_edit_column(**kwargs):
    return Column.edit(
        display_name="",
        extra__icon_attrs__title="Bearbeiten",
        extra__icon_attrs__aria_label="Bearbeiten",
        header__attrs__title="Bearbeiten",
        **kwargs,
    )


def icon_delete_column(**kwargs):
    return Column.delete(
        display_name="",
        extra__icon_attrs__title="Loeschen",
        extra__icon_attrs__aria_label="Loeschen",
        header__attrs__title="Loeschen",
        **kwargs,
    )


@dispatch(
    table=EMPTY,
    create=EMPTY,
    edit=EMPTY,
    delete=EMPTY,
    detail=EMPTY,
)
def login_required_crud_paths(
    *,
    model,
    table,
    create,
    edit,
    delete,
    detail,
    name_prefix="",
    require_strategy=False,
    include_table=True,
):
    table = setdefaults_path(
        table,
        auto__model=model,
        actions__new=Action(
            display_name="Neu",
            attrs__href="create/",
            attrs__class__primary_action=True,
        ),
        columns__edit=icon_edit_column(
            after=0,
            cell__url=lambda row, **_: f"{row.pk}/edit/",
        ),
        columns__delete=icon_delete_column(
            cell__url=lambda row, **_: f"{row.pk}/delete/",
        ),
    )
    detail = setdefaults_path(
        detail,
        auto__model=model,
        editable=False,
        instance=lambda params, **_: model.objects.get(pk=params.pk),
        title=lambda form, **_: (form.model or form.instance)._meta.verbose_name,
    )
    create = setdefaults_path(
        create,
        auto__model=model,
    )
    edit = setdefaults_path(
        edit,
        auto__model=model,
        instance=lambda params, **_: model.objects.get(pk=params.pk),
    )
    delete = setdefaults_path(
        delete,
        auto__model=model,
        instance=lambda params, **_: model.objects.get(pk=params.pk),
    )

    def wrap(view):
        if require_strategy:
            view = require_active_strategy(view)
        return login_required(view)

    paths = [
        path("create/", wrap(Form.create(**create).as_view()), name=f"{name_prefix}create"),
        path("<pk>/", wrap(Form(**detail).as_view()), name=f"{name_prefix}detail"),
        path("<pk>/edit/", wrap(Form.edit(**edit).as_view()), name=f"{name_prefix}edit"),
        path("<pk>/delete/", wrap(Form.delete(**delete).as_view()), name=f"{name_prefix}delete"),
    ]
    if include_table:
        paths.insert(0, path("", wrap(Table(**table).as_view()), name=f"{name_prefix}list"))
    return paths
