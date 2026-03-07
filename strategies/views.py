from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.forms import ModelForm, inlineformset_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import urlencode

from iommi import Action, Column, LAST, Page, Table, html

from core.iommi import icon_edit_column, login_required_crud_paths
from core.strategy_context import get_active_strategy, require_active_strategy
from .models import MeasureResponsibility, MeasureType, Strategy, StrategyLevel, StrategyLevelType, StrategyStatus


AUDIT_FIELDS = ["created_at", "updated_at", "created_by", "updated_by"]


def active_strategy(request):
    return get_active_strategy(request)


def active_strategy_id(request):
    strategy = active_strategy(request)
    return strategy.pk if strategy else None


def current_strategy_level(request, params=None, **_):
    level = request.GET.get("level")
    if level:
        return level

    if params is not None and getattr(params, "pk", None):
        return StrategyLevel.objects.only("level").get(
            pk=params.pk,
            strategy_id=active_strategy_id(request),
        ).level

    return None


def strategy_level_label(request=None, params=None, form=None, **_):
    if form is not None and getattr(form, "instance", None) is not None:
        level = form.instance.level
    else:
        level = current_strategy_level(request, params=params)

    labels = {
        StrategyLevelType.HANDLUNGSFELD: "Handlungsfeld",
        StrategyLevelType.ZIEL: "Ziel",
        StrategyLevelType.MASSNAHME: "Massnahme",
    }
    return labels.get(level, "Strategieebene")


def parent_level_choices_queryset(request, params=None, **_):
    strategy_id = active_strategy_id(request)
    if not strategy_id:
        return StrategyLevel.objects.none()

    current_level = current_strategy_level(request, params=params)

    if current_level == StrategyLevelType.ZIEL:
        return StrategyLevel.objects.filter(
            strategy_id=strategy_id,
            level=StrategyLevelType.HANDLUNGSFELD,
        ).order_by("short_code", "title")

    if current_level == StrategyLevelType.MASSNAHME:
        return StrategyLevel.objects.filter(
            strategy_id=strategy_id,
            level=StrategyLevelType.ZIEL,
        ).order_by("short_code", "title")

    return StrategyLevel.objects.none()


def level_has_parent(request, params=None, **_):
    return current_strategy_level(request, params=params) in {
        StrategyLevelType.ZIEL,
        StrategyLevelType.MASSNAHME,
    }


def level_has_measure_type(request, params=None, **_):
    return current_strategy_level(request, params=params) == StrategyLevelType.MASSNAHME


def level_has_measure_schedule(request, params=None, **_):
    return current_strategy_level(request, params=params) == StrategyLevelType.MASSNAHME


def detail_show_level_field(form=None, **_):
    return bool(form and form.instance.level == StrategyLevelType.MASSNAHME)


def detail_show_sort_order_field(form=None, **_):
    return bool(form and form.instance.level == StrategyLevelType.MASSNAHME)


def detail_show_parent_field(form=None, **_):
    return bool(form and form.instance.level == StrategyLevelType.MASSNAHME)


def parent_field_display_name(request=None, form=None, **_):
    level = None
    if form is not None and getattr(form, "instance", None) is not None:
        level = form.instance.level
    elif request is not None:
        level = current_strategy_level(request)

    if level == StrategyLevelType.ZIEL:
        return "Handlungsfeld"
    if level == StrategyLevelType.MASSNAHME:
        return "Ziel"
    return "Parent"


def selected_parent_id(request):
    return request.GET.get("parent") or request.GET.get("query/parent")


def selected_ziele_handlungsfeld_id(request):
    return request.GET.get("handlungsfeld_filter")


def selected_massnahmen_handlungsfeld_id(request):
    return request.GET.get("handlungsfeld_filter")


def selected_massnahmen_ziel(request):
    ziel_id = request.GET.get("ziel_filter")
    if not ziel_id:
        return None

    queryset = StrategyLevel.objects.filter(
        pk=ziel_id,
        strategy_id=active_strategy_id(request),
        level=StrategyLevelType.ZIEL,
    )
    selected_handlungsfeld_id = selected_massnahmen_handlungsfeld_id(request)
    if selected_handlungsfeld_id:
        queryset = queryset.filter(parent_id=selected_handlungsfeld_id)
    return queryset.first()


def selected_massnahmen_ziel_id(request):
    ziel = selected_massnahmen_ziel(request)
    return str(ziel.pk) if ziel else None


def selected_ziel_ids(request):
    selected_ids = []
    for key in ("parent", "query/parent", "ziel_filter"):
        for value in request.GET.getlist(key):
            selected_ids.extend(part.strip() for part in value.split(",") if part.strip())
    return selected_ids


def selected_ziel_id(request):
    selected_ids = selected_ziel_ids(request)
    return selected_ids[0] if selected_ids else None


def create_parent_field_include(request, params=None, **_):
    current_level = current_strategy_level(request, params=params)
    if current_level != StrategyLevelType.MASSNAHME:
        return level_has_parent(request, params=params)
    return not selected_ziel_ids(request)


def create_strategy_level_instance(form, request, **_):
    strategy = active_strategy(request)
    instance = StrategyLevel(
        strategy=strategy,
        level=current_strategy_level(request),
    )
    preselected_parent_id = selected_parent_id(request)
    if instance.level in {StrategyLevelType.ZIEL, StrategyLevelType.MASSNAHME} and preselected_parent_id:
        instance.parent_id = preselected_parent_id
    return instance


def strategy_level_redirect_to(form, **_):
    level = form.instance.level
    redirects = {
        StrategyLevelType.HANDLUNGSFELD: "/strategies/handlungsfelder/",
        StrategyLevelType.ZIEL: "/strategies/ziele/",
        StrategyLevelType.MASSNAHME: "/strategies/massnahmen/",
    }
    return redirects.get(level, "/strategies/levels/")


class MassnahmeForm(ModelForm):
    FIELD_TOOLTIPS = {
        "short_code": "Eindeutiges Kürzel der Massnahme.",
        "title": "Kurzbezeichnung der Massnahme.",
        "description": "Inhaltliche Beschreibung der Massnahme.",
        "implementation_description": "Konkrete Umsetzungsschritte und Vorgehen.",
        "parent": "Übergeordnetes Ziel, dem die Massnahme zugeordnet ist.",
        "measure_type": "Kategorie bzw. Typ der Massnahme.",
        "start_date": "Geplanter Start der Umsetzung.",
        "end_date": "Geplantes Ende der Umsetzung.",
        "total_effort": "Gesamter geplanter Aufwand in Personentagen (PT).",
        "total_cost": "Gesamte geplante Kosten in CHF.",
        "status": "Aktueller Status der Massnahme.",
        "sort_order": "Reihenfolge in Listenansichten (kleiner = weiter oben).",
    }

    class Meta:
        model = StrategyLevel
        fields = [
            "short_code",
            "title",
            "description",
            "implementation_description",
            "parent",
            "measure_type",
            "start_date",
            "end_date",
            "total_effort",
            "total_cost",
            "status",
            "sort_order",
        ]
        labels = {
            "total_effort": "Aufwand total (PT)",
            "total_cost": "Kosten total (CHF)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, tooltip in self.FIELD_TOOLTIPS.items():
            field = self.fields.get(field_name)
            if field is None:
                continue
            field.help_text = tooltip
            field.widget.attrs["title"] = tooltip


class MeasureResponsibilityForm(ModelForm):
    class Meta:
        model = MeasureResponsibility
        fields = ["person", "role", "description"]


MassnahmeResponsibilityFormSet = inlineformset_factory(
    StrategyLevel,
    MeasureResponsibility,
    form=MeasureResponsibilityForm,
    fk_name="measure",
    extra=5,
    can_delete=True,
)


def handlungsfeld_choices(request, **_):
    return StrategyLevel.objects.filter(
        strategy_id=active_strategy_id(request),
        level=StrategyLevelType.HANDLUNGSFELD,
    ).order_by("short_code", "title")


def ziel_choices(request, **_):
    queryset = StrategyLevel.objects.filter(
        strategy_id=active_strategy_id(request),
        level=StrategyLevelType.ZIEL,
    )
    selected_handlungsfeld_id = (
        selected_massnahmen_handlungsfeld_id(request)
        or request.GET.get("handlungsfeld")
        or request.GET.get("query/handlungsfeld")
    )
    if selected_handlungsfeld_id:
        queryset = queryset.filter(parent_id=selected_handlungsfeld_id)
    return queryset.order_by("short_code", "title")


def massnahmen_create_href(request, **_):
    query = {"level": StrategyLevelType.MASSNAHME}
    ziel_id = selected_massnahmen_ziel_id(request) or selected_ziel_id(request)
    if ziel_id:
        query["parent"] = ziel_id
    return f"/strategies/levels/create/?{urlencode(query)}"


def massnahmen_new_is_disabled(request, **_):
    return not (selected_massnahmen_ziel_id(request) or selected_ziel_id(request))


def massnahmen_rows(request, **_):
    queryset = StrategyLevel.objects.filter(
        level=StrategyLevelType.MASSNAHME,
        strategy_id=active_strategy_id(request),
    ).select_related("strategy", "parent", "parent__parent", "measure_type").prefetch_related(
        Prefetch(
            "responsibilities",
            queryset=MeasureResponsibility.objects.select_related("person__user").order_by(
                "person__short_code",
            ),
            to_attr="prefetched_responsibilities",
        )
    )

    selected_handlungsfeld_id = selected_massnahmen_handlungsfeld_id(request)
    selected_ziel = selected_massnahmen_ziel_id(request)
    if selected_handlungsfeld_id:
        queryset = queryset.filter(parent__parent_id=selected_handlungsfeld_id)
    if selected_ziel:
        queryset = queryset.filter(parent_id=selected_ziel)
    return queryset


def massnahmen_filter_panel(request, **_):
    return html.div(
        template="strategies/massnahmen_filter_panel.html",
        extra__handlungsfelder=handlungsfeld_choices(request),
        extra__ziele=ziel_choices(request),
        extra__selected_handlungsfeld_id=selected_massnahmen_handlungsfeld_id(request),
        extra__selected_ziel_id=selected_massnahmen_ziel_id(request),
        extra__new_href=massnahmen_create_href(request),
        extra__new_disabled=massnahmen_new_is_disabled(request),
    )


def massnahme_responsible_people_display(row, **_):
    responsibilities = getattr(row, "prefetched_responsibilities", None)
    if responsibilities is None:
        responsibilities = row.responsibilities.select_related("person__user").all()

    names = []
    for responsibility in responsibilities:
        names.append(responsibility.person.short_code)
    return ", ".join(dict.fromkeys(names))


@login_required
def massnahmen_page(request):
    page = Page(
        title="Massnahmen",
        parts__filter_panel=massnahmen_filter_panel(request),
        parts__table=massnahmen_table,
    )
    return page.as_view()(request)


@login_required
@require_active_strategy
def massnahme_edit_page(request, pk):
    measure = get_object_or_404(
        StrategyLevel.objects.select_related("strategy", "parent"),
        pk=pk,
        strategy_id=active_strategy_id(request),
    )
    if measure.level != StrategyLevelType.MASSNAHME:
        raise Http404("Only Massnahmen can be edited on this page.")

    form = MassnahmeForm(request.POST or None, instance=measure)
    form.fields["parent"].queryset = StrategyLevel.objects.filter(
        strategy_id=measure.strategy_id,
        level=StrategyLevelType.ZIEL,
    ).order_by("short_code", "title")
    form.fields["measure_type"].queryset = MeasureType.objects.order_by("label")

    responsibilities = MassnahmeResponsibilityFormSet(
        request.POST or None,
        instance=measure,
        prefix="responsibilities",
    )

    if request.method == "POST" and form.is_valid() and responsibilities.is_valid():
        updated_measure = form.save(commit=False)
        updated_measure.updated_by = request.user
        if updated_measure.created_by_id is None:
            updated_measure.created_by = request.user
        updated_measure.save()
        form.save_m2m()

        responsibility_instances = responsibilities.save(commit=False)
        for deleted in responsibilities.deleted_objects:
            deleted.delete()
        for responsibility in responsibility_instances:
            responsibility.measure = updated_measure
            responsibility.updated_by = request.user
            if responsibility.created_by_id is None:
                responsibility.created_by = request.user
            responsibility.save()
        redirect_to = request.POST.get("next") or "/strategies/massnahmen/"
        return redirect(redirect_to)

    return render(
        request,
        "strategies/massnahme_edit.html",
        {
            "form": form,
            "responsibilities": responsibilities,
            "measure": measure,
        },
    )


def ziele_create_href(request, **_):
    query = {"level": StrategyLevelType.ZIEL}
    handlungsfeld_id = selected_ziele_handlungsfeld_id(request)
    if handlungsfeld_id:
        query["parent"] = handlungsfeld_id
    return f"/strategies/levels/create/?{urlencode(query)}"


def ziele_new_is_disabled(request, **_):
    return not selected_ziele_handlungsfeld_id(request)


def ziele_rows(request, **_):
    queryset = StrategyLevel.objects.filter(
        level=StrategyLevelType.ZIEL,
        strategy_id=active_strategy_id(request),
    ).select_related("strategy", "parent").order_by("short_code", "title")
    selected_handlungsfeld_id = selected_ziele_handlungsfeld_id(request)
    if selected_handlungsfeld_id:
        queryset = queryset.filter(parent_id=selected_handlungsfeld_id)
    return queryset


def ziele_filter_panel(request, **_):
    return html.div(
        template="strategies/ziele_filter_panel.html",
        extra__handlungsfelder=handlungsfeld_choices(request),
        extra__selected_handlungsfeld_id=selected_ziele_handlungsfeld_id(request),
        extra__new_href=ziele_create_href(request),
        extra__new_disabled=ziele_new_is_disabled(request),
    )


@login_required
def ziele_page(request):
    page = Page(
        title="Ziele",
        parts__filter_panel=ziele_filter_panel(request),
        parts__table=ziele_table,
    )
    return page.as_view()(request)


strategy_crud = login_required_crud_paths(
    model=Strategy,
    include_table=False,
    table__title="Strategien",
    table__page_size=20,
    table__columns__id__include=False,
    table__columns__title__cell__url=lambda row, **_: f"/strategies/{row.pk}/",
    create__title="Strategie erfassen",
    create__auto__exclude=AUDIT_FIELDS,
    create__fields__image__extra__file_item_template=None,
    edit__title="Strategie bearbeiten",
    edit__auto__exclude=AUDIT_FIELDS,
    edit__fields__image__extra__file_item_template=None,
    detail__title=lambda form, **_: form.instance.title,
    detail__auto__exclude=AUDIT_FIELDS,
    detail__fields__image__extra__file_item_template=None,
    delete__title=lambda form, **_: f"Strategie löschen: {form.instance.title}",
)


@login_required
def strategy_card_list(request):
    active = active_strategy(request)
    strategies = Strategy.objects.exclude(status=StrategyStatus.INACTIVE).order_by("sort_order", "title")
    return render(
        request,
        "strategies/strategy_card_list.html",
        {
            "strategies": strategies,
            "active_strategy_id": active.pk if active else None,
        },
    )


level_crud = login_required_crud_paths(
    model=StrategyLevel,
    require_strategy=True,
    table__title="Strategieebenen",
    table__page_size=25,
    table__rows=lambda request, **_: StrategyLevel.objects.filter(strategy_id=active_strategy_id(request)).select_related(
        "strategy",
        "parent",
        "measure_type",
    ),
    table__columns__id__include=False,
    table__columns__strategy__include=False,
    table__columns__level__filter__include=True,
    table__columns__title__filter__include=True,
    table__columns__short_code__filter__include=True,
    table__columns__parent__filter__include=True,
    table__columns__measure_type__filter__include=True,
    table__columns__title__cell__url=lambda row, **_: f"/strategies/levels/{row.pk}/",
    create__title=lambda request, **_: f"{strategy_level_label(request=request)} erfassen",
    create__auto__exclude=AUDIT_FIELDS,
    create__extra__new_instance=create_strategy_level_instance,
    create__extra__redirect_to=strategy_level_redirect_to,
    create__fields__level__include=lambda request, **_: current_strategy_level(request) is None,
    create__fields__sort_order__after=LAST,
    create__fields__strategy__choices=lambda request, **_: Strategy.objects.filter(pk=active_strategy_id(request)),
    create__fields__strategy__include=False,
    create__fields__parent__choices=parent_level_choices_queryset,
    create__fields__parent__include=create_parent_field_include,
    create__fields__measure_type__include=level_has_measure_type,
    create__fields__implementation_description__include=level_has_measure_schedule,
    create__fields__implementation_description__after="description",
    create__fields__start_date__include=level_has_measure_schedule,
    create__fields__end_date__include=level_has_measure_schedule,
    create__fields__status__include=level_has_measure_schedule,
    create__fields__total_effort__include=level_has_measure_schedule,
    create__fields__total_effort__display_name="Aufwand total (PT)",
    create__fields__total_cost__include=level_has_measure_schedule,
    create__fields__total_cost__display_name="Kosten total (CHF)",
    edit__title=lambda form, **_: f"{strategy_level_label(form=form)} bearbeiten",
    edit__auto__exclude=AUDIT_FIELDS,
    edit__extra__redirect_to=strategy_level_redirect_to,
    edit__instance=lambda params, request, **_: StrategyLevel.objects.get(
        pk=params.pk,
        strategy_id=active_strategy_id(request),
    ),
    edit__fields__sort_order__after=LAST,
    edit__fields__strategy__choices=lambda request, **_: Strategy.objects.filter(pk=active_strategy_id(request)),
    edit__fields__strategy__include=False,
    edit__fields__parent__choices=parent_level_choices_queryset,
    edit__fields__parent__include=level_has_parent,
    edit__fields__parent__display_name=parent_field_display_name,
    edit__fields__parent__after="level",
    edit__fields__measure_type__include=level_has_measure_type,
    edit__fields__implementation_description__include=level_has_measure_schedule,
    edit__fields__implementation_description__after="description",
    edit__fields__start_date__include=level_has_measure_schedule,
    edit__fields__end_date__include=level_has_measure_schedule,
    edit__fields__status__include=level_has_measure_schedule,
    edit__fields__total_effort__include=level_has_measure_schedule,
    edit__fields__total_effort__display_name="Aufwand total (PT)",
    edit__fields__total_cost__include=level_has_measure_schedule,
    edit__fields__total_cost__display_name="Kosten total (CHF)",
    detail__title=lambda form, **_: form.instance.title,
    detail__auto__exclude=AUDIT_FIELDS,
    detail__template="strategies/level_detail_form.html",
    detail__instance=lambda params, request, **_: StrategyLevel.objects.get(
        pk=params.pk,
        strategy_id=active_strategy_id(request),
    ),
    detail__fields__strategy__choices=lambda request, **_: Strategy.objects.filter(pk=active_strategy_id(request)),
    detail__fields__strategy__include=False,
    detail__fields__level__include=detail_show_level_field,
    detail__fields__parent__choices=parent_level_choices_queryset,
    detail__fields__parent__include=detail_show_parent_field,
    detail__fields__measure_type__include=level_has_measure_type,
    detail__fields__implementation_description__include=level_has_measure_schedule,
    detail__fields__implementation_description__after="description",
    detail__fields__status__after=0,
    detail__fields__start_date__include=level_has_measure_schedule,
    detail__fields__end_date__include=level_has_measure_schedule,
    detail__fields__status__include=level_has_measure_schedule,
    detail__fields__total_effort__include=level_has_measure_schedule,
    detail__fields__total_effort__display_name="Aufwand total (PT)",
    detail__fields__total_cost__include=level_has_measure_schedule,
    detail__fields__total_cost__display_name="Kosten total (CHF)",
    detail__fields__sort_order__include=detail_show_sort_order_field,
    detail__fields__sort_order__after=LAST,
    delete__title=lambda form, **_: f"Strategieebene loeschen: {form.instance.title}",
    delete__instance=lambda params, request, **_: StrategyLevel.objects.get(
        pk=params.pk,
        strategy_id=active_strategy_id(request),
    ),
)


measure_type_crud = login_required_crud_paths(
    model=MeasureType,
    table__title="Massnahmentypen",
    table__page_size=20,
    table__columns__code__filter__include=True,
    table__columns__label__filter__include=True,
    table__columns__is_active__filter__include=True,
    table__columns__id__include=False,
    table__columns__label__cell__url=lambda row, **_: f"/strategies/measure-types/{row.pk}/",
    create__title="Massnahmentyp erfassen",
    create__auto__exclude=AUDIT_FIELDS,
    edit__title="Massnahmentyp bearbeiten",
    edit__auto__exclude=AUDIT_FIELDS,
    detail__title=lambda form, **_: form.instance.label,
    detail__auto__exclude=AUDIT_FIELDS,
    delete__title=lambda form, **_: f"Massnahmentyp löschen: {form.instance.label}",
)


responsibility_crud = login_required_crud_paths(
    model=MeasureResponsibility,
    require_strategy=True,
    table__title="Massnahmenverantwortlichkeiten",
    table__page_size=25,
    table__rows=lambda request, **_: MeasureResponsibility.objects.filter(
        measure__strategy_id=active_strategy_id(request)
    ).select_related("measure", "person"),
    table__columns__id__include=False,
    table__columns__measure__filter__include=True,
    table__columns__person__filter__include=True,
    table__columns__role__filter__include=True,
    table__columns__description__filter__include=True,
    table__columns__measure__cell__url=lambda row, **_: f"/strategies/responsibilities/{row.pk}/",
    create__title="Verantwortlichkeit erfassen",
    create__auto__exclude=AUDIT_FIELDS,
    create__fields__measure__choices=lambda request, **_: StrategyLevel.objects.filter(
        strategy_id=active_strategy_id(request),
        level=StrategyLevelType.MASSNAHME,
    ).order_by("short_code", "title"),
    edit__title="Verantwortlichkeit bearbeiten",
    edit__auto__exclude=AUDIT_FIELDS,
    edit__instance=lambda params, request, **_: MeasureResponsibility.objects.get(
        pk=params.pk,
        measure__strategy_id=active_strategy_id(request),
    ),
    edit__fields__measure__choices=lambda request, **_: StrategyLevel.objects.filter(
        strategy_id=active_strategy_id(request),
        level=StrategyLevelType.MASSNAHME,
    ).order_by("short_code", "title"),
    detail__title=lambda form, **_: str(form.instance),
    detail__auto__exclude=AUDIT_FIELDS,
    detail__instance=lambda params, request, **_: MeasureResponsibility.objects.get(
        pk=params.pk,
        measure__strategy_id=active_strategy_id(request),
    ),
    detail__fields__measure__choices=lambda request, **_: StrategyLevel.objects.filter(
        strategy_id=active_strategy_id(request),
        level=StrategyLevelType.MASSNAHME,
    ).order_by("short_code", "title"),
    delete__title=lambda form, **_: f"Verantwortlichkeit löschen: {form.instance}",
    delete__instance=lambda params, request, **_: MeasureResponsibility.objects.get(
        pk=params.pk,
        measure__strategy_id=active_strategy_id(request),
    ),
)


handlungsfelder_table = Table(
    auto__model=StrategyLevel,
    title="Handlungsfelder",
    actions__new=Action(
        display_name="Neu",
        attrs__href=f"/strategies/levels/create/?level={StrategyLevelType.HANDLUNGSFELD}",
        attrs__class__primary_action=True,
    ),
    rows=lambda request, **_: StrategyLevel.objects.filter(
        level=StrategyLevelType.HANDLUNGSFELD,
        strategy_id=active_strategy_id(request),
    ).select_related("strategy"),
    page_size=20,
    columns__id__include=False,
    columns__level__include=False,
    columns__description__include=False,
    columns__implementation_description__include=False,
    columns__parent__include=False,
    columns__measure_type__include=False,
    columns__total_effort__include=False,
    columns__total_cost__include=False,
    columns__start_date__include=False,
    columns__end_date__include=False,
    columns__status__include=False,
    columns__sort_order__include=False,
    columns__created_at__include=False,
    columns__updated_at__include=False,
    columns__created_by__include=False,
    columns__updated_by__include=False,
    columns__title__display_name="Handlungsfeld",
    columns__title__filter__include=True,
    columns__short_code__filter__include=True,
    columns__short_code__after="edit",
    columns__title__after="short_code",
    columns__strategy__display_name="Strategie",
    columns__strategy__after="title",
    columns__strategy__cell__value=lambda row, **_: row.strategy.short_code if row.strategy else "",
    columns__title__cell__url=lambda row, **_: f"/strategies/levels/{row.pk}/",
    columns__edit=icon_edit_column(
        after=0,
        cell__url=lambda row, **_: f"/strategies/levels/{row.pk}/edit/",
    ),
)


ziele_table = Table(
    auto__model=StrategyLevel,
    title="Zielliste",
    rows=ziele_rows,
    page_size=20,
    columns__id__include=False,
    columns__strategy__include=False,
    columns__level__include=False,
    columns__description__include=False,
    columns__implementation_description__include=False,
    columns__measure_type__include=False,
    columns__total_effort__include=False,
    columns__total_cost__include=False,
    columns__start_date__include=False,
    columns__end_date__include=False,
    columns__status__include=False,
    columns__sort_order__include=False,
    columns__created_at__include=False,
    columns__updated_at__include=False,
    columns__created_by__include=False,
    columns__updated_by__include=False,
    columns__title__filter__include=True,
    columns__short_code__filter__include=True,
    columns__short_code__after="edit",
    columns__title__after="short_code",
    columns__parent__filter__include=False,
    columns__parent__display_name="Handlungsfeld",
    columns__parent__after="title",
    columns__title__cell__url=lambda row, **_: f"/strategies/levels/{row.pk}/",
    columns__edit=icon_edit_column(
        after=0,
        cell__url=lambda row, **_: f"/strategies/levels/{row.pk}/edit/",
    ),
)


massnahmen_table = Table(
    auto__model=StrategyLevel,
    title="Massnahmenliste",
    rows=massnahmen_rows,
    page_size=20,
    columns__id__include=False,
    columns__strategy__include=False,
    columns__level__include=False,
    columns__description__include=False,
    columns__implementation_description__include=False,
    columns__measure_type__include=False,
    columns__total_effort__include=False,
    columns__total_cost__include=False,
    columns__sort_order__include=False,
    columns__created_at__include=False,
    columns__updated_at__include=False,
    columns__created_by__include=False,
    columns__updated_by__include=False,
    columns__title__filter__include=True,
    columns__title__display_name="Massnahme",
    columns__short_code__filter__include=True,
    columns__short_code__after="edit",
    columns__title__after="short_code",
    columns__parent__filter__include=False,
    columns__parent__display_name="Ziel",
    columns__parent__after="title",
    columns__parent__cell__value=lambda row, **_: row.parent.title if row.parent else "",
    columns__responsible_people=Column(
        display_name="Verantwortlich",
        after="parent",
        cell__value=massnahme_responsible_people_display,
    ),
    columns__dauer=Column(
        display_name="Dauer",
        after="responsible_people",
        cell__value=lambda row, **_: f"{row.start_year_display} - {row.end_year_display}".strip(" -"),
    ),
    columns__start_date__include=False,
    columns__end_date__include=False,
    columns__status__after="dauer",
    columns__title__cell__url=lambda row, **_: f"/strategies/levels/{row.pk}/",
    columns__edit=icon_edit_column(
        after=0,
        cell__url=lambda row, **_: f"/strategies/massnahmen/{row.pk}/edit/",
    ),
)
