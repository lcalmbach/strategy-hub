from iommi import Column

from core.iommi import login_required_crud_paths
from core.strategy_context import get_active_strategy
from strategies.models import StrategyLevel, StrategyLevelType
from .models import ControllingPeriod, ControllingRecord, ControllingRecordResponsibility


AUDIT_FIELDS = ["created_at", "updated_at", "created_by", "updated_by"]


def active_strategy(request):
    return get_active_strategy(request)


def active_strategy_id(request):
    strategy = active_strategy(request)
    return strategy.pk if strategy else None


period_crud = login_required_crud_paths(
    model=ControllingPeriod,
    table__title="Controlling-Perioden",
    table__page_size=20,
    table__columns__name__filter__include=True,
    table__columns__year__filter__include=True,
    table__columns__month__filter__include=True,
    table__columns__status__filter__include=True,
    table__columns__is_locked__filter__include=True,
    table__columns__id__include=False,
    table__columns__name__cell__url=lambda row, **_: f"/controlling/periods/{row.pk}/",
    create__title="Controlling-Periode erfassen",
    create__auto__exclude=AUDIT_FIELDS,
    edit__title="Controlling-Periode bearbeiten",
    edit__auto__exclude=AUDIT_FIELDS,
    detail__title=lambda form, **_: form.instance.name,
    detail__auto__exclude=AUDIT_FIELDS,
    delete__title=lambda form, **_: f"Periode loeschen: {form.instance.name}",
)


record_crud = login_required_crud_paths(
    model=ControllingRecord,
    require_strategy=True,
    table__title="Controlling-Records",
    table__page_size=25,
    table__rows=lambda request, **_: ControllingRecord.objects.filter(
        measure__strategy_id=active_strategy_id(request)
    ).select_related("period", "measure", "measure__strategy"),
    table__columns__id__include=False,
    table__columns__period__filter__include=True,
    table__columns__measure__filter__include=True,
    table__columns__status__filter__include=True,
    table__columns__plan_cost_chf__filter__include=True,
    table__columns__actual_cost_chf__filter__include=True,
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
    table__columns__edit=Column.edit(after=0, cell__url=lambda row, **_: f"/controlling/responsibilities/{row.pk}/edit/"),
    table__columns__delete=Column.delete(cell__url=lambda row, **_: f"/controlling/responsibilities/{row.pk}/delete/"),
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
