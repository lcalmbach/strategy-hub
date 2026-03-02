from iommi import Column

from core.iommi import icon_delete_column, icon_edit_column, login_required_crud_paths
from core.strategy_context import get_active_strategy
from strategies.models import StrategyLevel, StrategyLevelType
from .models import ControllingPeriod, ControllingRecord, ControllingRecordResponsibility


AUDIT_FIELDS = ["created_at", "updated_at", "created_by", "updated_by"]


def active_strategy(request):
    return get_active_strategy(request)


def active_strategy_id(request):
    strategy = active_strategy(request)
    return strategy.pk if strategy else None


def create_controlling_period_instance(request, **_):
    return ControllingPeriod(strategy=active_strategy(request))


period_crud = login_required_crud_paths(
    model=ControllingPeriod,
    require_strategy=True,
    table__title="Controlling-Perioden",
    table__page_size=20,
    table__columns__name__include=True,
    table__columns__start_date__include=True,
    table__columns__end_date__include=True,
    table__rows=lambda request, **_: ControllingPeriod.objects.filter(
        strategy_id=active_strategy_id(request)
    ).select_related("strategy"),
    table__columns__name__filter__include=True,
    table__columns__status__filter__include=True,
    table__columns__is_locked__filter__include=True,
    table__columns__id__include=False,
    table__columns__strategy__include=False,
    table__columns__planning_deadline__include=False,
    table__columns__actuals_deadline__include=False,
    table__columns__status__include=False,
    table__columns__is_locked__include=False,
    table__columns__created_at__include=False,
    table__columns__updated_at__include=False,
    table__columns__created_by__include=False,
    table__columns__updated_by__include=False,
    table__columns__name__cell__url=lambda row, **_: f"/controlling/periods/{row.pk}/",
    create__title="Controlling-Periode erfassen",
    create__auto__exclude=AUDIT_FIELDS,
    create__extra__new_instance=create_controlling_period_instance,
    create__fields__strategy__include=False,
    edit__title="Controlling-Periode bearbeiten",
    edit__auto__exclude=AUDIT_FIELDS,
    edit__instance=lambda params, request, **_: ControllingPeriod.objects.get(
        pk=params.pk,
        strategy_id=active_strategy_id(request),
    ),
    edit__fields__strategy__include=False,
    detail__title=lambda form, **_: form.instance.name,
    detail__auto__exclude=AUDIT_FIELDS,
    detail__instance=lambda params, request, **_: ControllingPeriod.objects.get(
        pk=params.pk,
        strategy_id=active_strategy_id(request),
    ),
    detail__fields__strategy__include=False,
    delete__title=lambda form, **_: f"Periode loeschen: {form.instance.name}",
    delete__instance=lambda params, request, **_: ControllingPeriod.objects.get(
        pk=params.pk,
        strategy_id=active_strategy_id(request),
    ),
)


record_crud = login_required_crud_paths(
    model=ControllingRecord,
    require_strategy=True,
    table__title="Controlling-Records",
    table__page_size=25,
    table__rows=lambda request, **_: ControllingRecord.objects.filter(
        measure__strategy_id=active_strategy_id(request)
    ).select_related("period", "measure", "measure__parent", "measure__strategy"),
    table__columns__id__include=False,
    table__columns__measure__display_name="Massnahme",
    table__columns__measure__after="goal",
    table__columns__measure__include=True,
    table__columns__period__display_name="Planungsperiode",
    table__columns__period__include=True,
    table__columns__status__include=True,
    table__columns__goal=Column(
        display_name="Ziel",
        after="edit",
        cell__value=lambda row, **_: row.measure.parent.title if row.measure.parent else "",
        cell__url=lambda row, **_: f"/strategies/levels/{row.measure.parent.pk}/" if row.measure.parent else None,
        sortable=False,
    ),
    table__columns__period__filter__include=True,
    table__columns__measure__filter__include=True,
    table__columns__status__filter__include=True,
    table__columns__plan_cost_chf__filter__include=True,
    table__columns__actual_cost_chf__filter__include=True,
    table__columns__plan_result_description__include=False,
    table__columns__plan_effort_person_days__include=False,
    table__columns__plan_effort_description__include=False,
    table__columns__plan_cost_chf__include=False,
    table__columns__plan_cost_description__include=False,
    table__columns__actual_fulfillment_percent__include=False,
    table__columns__actual_result_description__include=False,
    table__columns__actual_effort_person_days__include=False,
    table__columns__actual_effort_description__include=False,
    table__columns__actual_cost_chf__include=False,
    table__columns__actual_cost_description__include=False,
    table__columns__created_at__include=False,
    table__columns__updated_at__include=False,
    table__columns__created_by__include=False,
    table__columns__updated_by__include=False,
    table__columns__measure__cell__url=lambda row, **_: f"/controlling/records/{row.pk}/",
    create__title="Controlling-Record erfassen",
    create__auto__exclude=AUDIT_FIELDS,
    create__fields__measure__choices=lambda request, **_: StrategyLevel.objects.filter(
        strategy_id=active_strategy_id(request),
        level=StrategyLevelType.MASSNAHME,
    ),
    edit__title="Controlling-Record bearbeiten",
    edit__auto__exclude=AUDIT_FIELDS,
    edit__instance=lambda params, request, **_: ControllingRecord.objects.get(
        pk=params.pk,
        measure__strategy_id=active_strategy_id(request),
    ),
    edit__fields__measure__choices=lambda request, **_: StrategyLevel.objects.filter(
        strategy_id=active_strategy_id(request),
        level=StrategyLevelType.MASSNAHME,
    ),
    detail__title=lambda form, **_: str(form.instance),
    detail__auto__exclude=AUDIT_FIELDS,
    detail__instance=lambda params, request, **_: ControllingRecord.objects.get(
        pk=params.pk,
        measure__strategy_id=active_strategy_id(request),
    ),
    detail__fields__measure__choices=lambda request, **_: StrategyLevel.objects.filter(
        strategy_id=active_strategy_id(request),
        level=StrategyLevelType.MASSNAHME,
    ),
    delete__title=lambda form, **_: f"Record loeschen: {form.instance}",
    delete__instance=lambda params, request, **_: ControllingRecord.objects.get(
        pk=params.pk,
        measure__strategy_id=active_strategy_id(request),
    ),
)


record_responsibility_crud = login_required_crud_paths(
    model=ControllingRecordResponsibility,
    require_strategy=True,
    table__title="Record-Verantwortlichkeiten",
    table__page_size=25,
    table__rows=lambda request, **_: ControllingRecordResponsibility.objects.filter(
        controlling_record__measure__strategy_id=active_strategy_id(request)
    ).select_related("controlling_record", "person", "controlling_record__measure"),
    table__columns__id__include=False,
    table__columns__controlling_record__filter__include=True,
    table__columns__person__filter__include=True,
    table__columns__role__filter__include=True,
    table__columns__controlling_record__cell__url=lambda row, **_: f"/controlling/responsibilities/{row.pk}/",
    table__columns__edit=icon_edit_column(after=0, cell__url=lambda row, **_: f"/controlling/responsibilities/{row.pk}/edit/"),
    table__columns__delete=icon_delete_column(cell__url=lambda row, **_: f"/controlling/responsibilities/{row.pk}/delete/"),
    create__title="Record-Verantwortlichkeit erfassen",
    create__auto__exclude=AUDIT_FIELDS,
    create__fields__controlling_record__choices=lambda request, **_: ControllingRecord.objects.filter(
        measure__strategy_id=active_strategy_id(request)
    ).select_related("measure", "period"),
    edit__title="Record-Verantwortlichkeit bearbeiten",
    edit__auto__exclude=AUDIT_FIELDS,
    edit__instance=lambda params, request, **_: ControllingRecordResponsibility.objects.get(
        pk=params.pk,
        controlling_record__measure__strategy_id=active_strategy_id(request),
    ),
    edit__fields__controlling_record__choices=lambda request, **_: ControllingRecord.objects.filter(
        measure__strategy_id=active_strategy_id(request)
    ).select_related("measure", "period"),
    detail__title=lambda form, **_: str(form.instance),
    detail__auto__exclude=AUDIT_FIELDS,
    detail__instance=lambda params, request, **_: ControllingRecordResponsibility.objects.get(
        pk=params.pk,
        controlling_record__measure__strategy_id=active_strategy_id(request),
    ),
    detail__fields__controlling_record__choices=lambda request, **_: ControllingRecord.objects.filter(
        measure__strategy_id=active_strategy_id(request)
    ).select_related("measure", "period"),
    delete__title=lambda form, **_: f"Verantwortlichkeit loeschen: {form.instance}",
    delete__instance=lambda params, request, **_: ControllingRecordResponsibility.objects.get(
        pk=params.pk,
        controlling_record__measure__strategy_id=active_strategy_id(request),
    ),
)
