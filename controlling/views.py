from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.utils.html import format_html
from iommi import Action, Column

from core.iommi import icon_delete_column, icon_edit_column, login_required_crud_paths
from core.models import Code
from core.strategy_context import get_active_strategy, require_active_strategy
from strategies.models import ResponsibilityRole, StrategyLevel, StrategyLevelType
from .models import AmpelStatus, ControllingPeriod, ControllingRecord, ControllingRecordResponsibility, ControllingRecordStatus
from .services import open_period


AUDIT_FIELDS = ["created_at", "updated_at", "created_by", "updated_by"]


def active_strategy(request):
    return get_active_strategy(request)


def active_strategy_id(request):
    strategy = active_strategy(request)
    return strategy.pk if strategy else None


def create_controlling_period_instance(request, **_):
    return ControllingPeriod(strategy=active_strategy(request))


PLAN_FIELDS = {
    "plan_result_description",
    "plan_effort_person_days",
    "plan_effort_description",
    "plan_cost_chf",
    "plan_cost_description",
}
ACTUAL_FIELDS = {
    "actual_fulfillment_percent",
    "actual_result_description",
    "actual_effort_person_days",
    "actual_effort_description",
    "actual_cost_chf",
    "actual_cost_description",
    "umsetzung_status_manual",
    "kosten_status_manual",
    "aufwand_status_manual",
}


def current_record_status(request=None, form=None, **_):
    def normalize_status(raw_value):
        if not raw_value:
            return ""
        if hasattr(raw_value, "code"):
            return raw_value.code
        raw_value = str(raw_value)
        known_codes = {
            ControllingRecordStatus.OPEN,
            ControllingRecordStatus.PLANNING_IN_PROGRESS,
            ControllingRecordStatus.PLANNING_COMPLETED,
            ControllingRecordStatus.CONTROLLING_IN_PROGRESS,
            ControllingRecordStatus.CONTROLLING_COMPLETED,
        }
        if raw_value in known_codes:
            return raw_value
        if raw_value.isdigit():
            code = Code.objects.filter(pk=int(raw_value), category_id=1).only("code").first()
            return code.code if code else raw_value
        return raw_value

    if request is not None:
        posted_status = normalize_status(request.POST.get("status"))
        if posted_status:
            return posted_status
        query_status = normalize_status(request.GET.get("status"))
        if query_status:
            return query_status

    if form is not None and getattr(form, "instance", None) is not None:
        return normalize_status(form.instance.status)
    return ControllingRecordStatus.OPEN


def include_record_field(field_name: str, request=None, form=None, **_):
    status = current_record_status(request=request, form=form)
    if status == ControllingRecordStatus.PLANNING_IN_PROGRESS:
        return field_name in PLAN_FIELDS
    if status == ControllingRecordStatus.CONTROLLING_IN_PROGRESS:
        return field_name in ACTUAL_FIELDS
    if status == ControllingRecordStatus.CONTROLLING_COMPLETED:
        return True
    return True


def record_field_include(field_name: str):
    return lambda request=None, form=None, **kwargs: include_record_field(
        field_name,
        request=request,
        form=form,
        **kwargs,
    )


AMPEL_COLORS = {
    AmpelStatus.GREEN: "#16a34a",
    AmpelStatus.YELLOW: "#f59e0b",
    AmpelStatus.RED: "#dc2626",
    "": "#9ca3af",
}

AMPEL_LABELS = {
    AmpelStatus.GREEN: "Grün",
    AmpelStatus.YELLOW: "Gelb",
    AmpelStatus.RED: "Rot",
    "": "Keine Ampel",
}


def ampel_cell(color, title):
    return format_html(
        '<span title="{}" aria-label="{}" style="display:inline-block;width:14px;height:14px;border-radius:999px;background:{};"></span>',
        title,
        title,
        color,
    )


def ampel_cell_for_status(status: str, title: str):
    return ampel_cell(AMPEL_COLORS.get(status, "#9ca3af"), title)


def umsetzung_ampel(row, **_):
    source = "manuell" if row.umsetzung_status_manual else "automatisch"
    status = row.umsetzung_status_effective
    title = (
        f"Umsetzung ({source}): {AMPEL_LABELS.get(status, 'Keine Ampel')} "
        f"(Ist {row.actual_fulfillment_percent}% vs. Plan 100%)"
    )
    return ampel_cell_for_status(status, title)


def kosten_ampel(row, **_):
    source = "manuell" if row.kosten_status_manual else "automatisch"
    status = row.kosten_status_effective
    title = (
        f"Ausgaben ({source}): {AMPEL_LABELS.get(status, 'Keine Ampel')} "
        f"(Ist {row.actual_cost_chf} vs. Plan {row.plan_cost_chf})"
    )
    return ampel_cell_for_status(status, title)


def aufwand_ampel(row, **_):
    source = "manuell" if row.aufwand_status_manual else "automatisch"
    status = row.aufwand_status_effective
    title = (
        f"Aufwand ({source}): {AMPEL_LABELS.get(status, 'Keine Ampel')} "
        f"(Ist {row.actual_effort_person_days} vs. Plan {row.plan_effort_person_days})"
    )
    return ampel_cell_for_status(status, title)


def responsible_people_display(row, **_):
    responsibilities = getattr(row, "prefetched_responsibilities", None)
    if responsibilities is None:
        responsibilities = row.responsibilities.select_related("person__user").filter(role=ResponsibilityRole.RESPONSIBLE)

    short_codes = []
    for responsibility in responsibilities:
        short_codes.append(responsibility.person.short_code)
    return ", ".join(dict.fromkeys(short_codes))


@login_required
@require_active_strategy
def delete_controlling_period_direct(request, pk):
    period = get_object_or_404(
        ControllingPeriod,
        pk=pk,
        strategy_id=active_strategy_id(request),
    )
    period_name = period.name
    period.delete()
    messages.success(request, f"Periode gelöscht: {period_name}")
    return redirect("/controlling/periods/")


@login_required
@require_active_strategy
def delete_controlling_record_direct(request, pk):
    record = get_object_or_404(
        ControllingRecord,
        pk=pk,
        measure__strategy_id=active_strategy_id(request),
    )
    record_label = str(record)
    record.delete()
    messages.success(request, f"Record gelöscht: {record_label}")
    return redirect("/controlling/records/")


@login_required
@require_active_strategy
def create_missing_records_for_period(request, pk):
    period = get_object_or_404(
        ControllingPeriod,
        pk=pk,
        strategy_id=active_strategy_id(request),
    )
    created_records, existing_count = open_period(period, created_by=request.user)
    created_count = len(created_records)
    if created_count:
        messages.success(
            request,
            (
                f"{created_count} fehlende Records für '{period.name}' erstellt "
                f"(bereits vorhanden: {existing_count})."
            ),
        )
    else:
        messages.info(request, f"Keine fehlenden Records gefunden für '{period.name}'.")
    return redirect(f"/controlling/periods/{period.pk}/")


period_crud = login_required_crud_paths(
    model=ControllingPeriod,
    require_strategy=True,
    table__title="Controlling-Perioden",
    table__page_size=20,
    table__columns__name__include=True,
    table__columns__start_date__include=True,
    table__columns__end_date__include=True,
    table__columns__start_date__display_name="Beginn",
    table__columns__end_date__display_name="Ende",
    table__columns__planning_deadline__include=True,
    table__columns__planning_deadline__display_name="Planung Ende",
    table__columns__planning_deadline__after="end_date",
    table__columns__controlling_deadline__include=True,
    table__columns__controlling_deadline__display_name="Controlling Ende",
    table__columns__controlling_deadline__after="planning_deadline",
    table__rows=lambda request, **_: ControllingPeriod.objects.filter(
        strategy_id=active_strategy_id(request)
    ).select_related("strategy"),
    table__columns__name__filter__include=True,
    table__columns__status__filter__include=True,
    table__columns__id__include=False,
    table__columns__strategy__include=False,
    table__columns__status__include=False,
    table__columns__invitation_planning_mail_text__include=False,
    table__columns__invitation_controlling_mail_text__include=False,
    table__columns__created_at__include=False,
    table__columns__updated_at__include=False,
    table__columns__created_by__include=False,
    table__columns__updated_by__include=False,
    table__columns__name__cell__url=lambda row, **_: f"/controlling/periods/{row.pk}/",
    table__columns__edit=icon_edit_column(after=0, cell__url=lambda row, **_: f"/controlling/periods/{row.pk}/edit/"),
    table__columns__delete=icon_delete_column(cell__url=lambda row, **_: f"/controlling/periods/{row.pk}/delete-direct/"),
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
    detail__actions__generate_missing_records=Action(
        display_name="Fehlende Controlling Records 🚀",
        attrs__href=lambda form, **_: f"/controlling/periods/{form.instance.pk}/generate-missing-records/",
        attrs__class__primary_action=True,
    ),
    delete__title=lambda form, **_: f"Periode löschen: {form.instance.name}",
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
    ).select_related("period", "measure", "measure__parent", "measure__strategy").prefetch_related(
        Prefetch(
            "responsibilities",
            queryset=ControllingRecordResponsibility.objects.select_related("person__user")
            .filter(role=ResponsibilityRole.RESPONSIBLE)
            .order_by("person__short_code"),
            to_attr="prefetched_responsibilities",
        )
    ),
    table__columns__id__include=False,
    table__columns__measure__display_name="Massnahme",
    table__columns__measure__include=True,
    table__columns__measure__cell__value=lambda row, **_: (
        row.measure.display_label[:50] + "..." if len(row.measure.display_label) > 50 else row.measure.display_label
    ),
    table__columns__responsible=Column(
        display_name="Verantwortlich",
        after="measure",
        cell__value=responsible_people_display,
        sortable=False,
    ),
    table__columns__period__display_name="Planungsperiode",
    table__columns__period__include=True,
    table__columns__status__include=True,
    table__columns__status__cell__value=lambda row, **_: row.status.name if row.status_id else "",
    table__columns__umsetzung=Column(
        display_name="Umsetzung",
        after="status",
        cell__value=umsetzung_ampel,
        sortable=False,
    ),
    table__columns__kosten=Column(
        display_name="Kosten",
        after="umsetzung",
        cell__value=kosten_ampel,
        sortable=False,
    ),
    table__columns__aufwand=Column(
        display_name="Aufwand",
        after="kosten",
        cell__value=aufwand_ampel,
        sortable=False,
    ),
    table__columns__period__filter__include=True,
    table__columns__measure__filter__include=True,
    table__columns__measure__filter__choices=lambda request, **_: StrategyLevel.objects.filter(
        strategy_id=active_strategy_id(request),
        level=StrategyLevelType.MASSNAHME,
    ).order_by("short_code", "title"),
    table__columns__status__filter__include=True,
    table__columns__plan_cost_chf__filter__include=True,
    table__columns__actual_cost_chf__filter__include=True,
    table__columns__plan_result_description__include=False,
    table__columns__umsetzung_status_manual__include=False,
    table__columns__kosten_status_manual__include=False,
    table__columns__aufwand_status_manual__include=False,
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
    table__columns__edit=icon_edit_column(after=0, cell__url=lambda row, **_: f"/controlling/records/{row.pk}/edit/"),
    table__columns__delete=icon_delete_column(cell__url=lambda row, **_: f"/controlling/records/{row.pk}/delete-direct/"),
    create__title="Controlling-Record erfassen",
    create__auto__exclude=AUDIT_FIELDS,
    create__fields__measure__choices=lambda request, **_: StrategyLevel.objects.filter(
        strategy_id=active_strategy_id(request),
        level=StrategyLevelType.MASSNAHME,
    ),
    create__fields__plan_result_description__include=record_field_include("plan_result_description"),
    create__fields__plan_effort_person_days__include=record_field_include("plan_effort_person_days"),
    create__fields__plan_effort_description__include=record_field_include("plan_effort_description"),
    create__fields__plan_cost_chf__include=record_field_include("plan_cost_chf"),
    create__fields__plan_cost_description__include=record_field_include("plan_cost_description"),
    create__fields__actual_fulfillment_percent__include=record_field_include("actual_fulfillment_percent"),
    create__fields__actual_result_description__include=record_field_include("actual_result_description"),
    create__fields__actual_effort_person_days__include=record_field_include("actual_effort_person_days"),
    create__fields__actual_effort_description__include=record_field_include("actual_effort_description"),
    create__fields__actual_cost_chf__include=record_field_include("actual_cost_chf"),
    create__fields__actual_cost_description__include=record_field_include("actual_cost_description"),
    create__fields__umsetzung_status_manual__include=record_field_include("umsetzung_status_manual"),
    create__fields__kosten_status_manual__include=record_field_include("kosten_status_manual"),
    create__fields__aufwand_status_manual__include=record_field_include("aufwand_status_manual"),
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
    edit__fields__plan_result_description__include=record_field_include("plan_result_description"),
    edit__fields__plan_effort_person_days__include=record_field_include("plan_effort_person_days"),
    edit__fields__plan_effort_description__include=record_field_include("plan_effort_description"),
    edit__fields__plan_cost_chf__include=record_field_include("plan_cost_chf"),
    edit__fields__plan_cost_description__include=record_field_include("plan_cost_description"),
    edit__fields__actual_fulfillment_percent__include=record_field_include("actual_fulfillment_percent"),
    edit__fields__actual_result_description__include=record_field_include("actual_result_description"),
    edit__fields__actual_effort_person_days__include=record_field_include("actual_effort_person_days"),
    edit__fields__actual_effort_description__include=record_field_include("actual_effort_description"),
    edit__fields__actual_cost_chf__include=record_field_include("actual_cost_chf"),
    edit__fields__actual_cost_description__include=record_field_include("actual_cost_description"),
    edit__fields__umsetzung_status_manual__include=record_field_include("umsetzung_status_manual"),
    edit__fields__umsetzung_status_manual__after="actual_cost_description",
    edit__fields__kosten_status_manual__include=record_field_include("kosten_status_manual"),
    edit__fields__kosten_status_manual__after="umsetzung_status_manual",
    edit__fields__aufwand_status_manual__include=record_field_include("aufwand_status_manual"),
    edit__fields__aufwand_status_manual__after="kosten_status_manual",
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
    detail__fields__plan_result_description__include=record_field_include("plan_result_description"),
    detail__fields__plan_effort_person_days__include=record_field_include("plan_effort_person_days"),
    detail__fields__plan_effort_description__include=record_field_include("plan_effort_description"),
    detail__fields__plan_cost_chf__include=record_field_include("plan_cost_chf"),
    detail__fields__plan_cost_description__include=record_field_include("plan_cost_description"),
    detail__fields__actual_fulfillment_percent__include=record_field_include("actual_fulfillment_percent"),
    detail__fields__actual_result_description__include=record_field_include("actual_result_description"),
    detail__fields__actual_effort_person_days__include=record_field_include("actual_effort_person_days"),
    detail__fields__actual_effort_description__include=record_field_include("actual_effort_description"),
    detail__fields__actual_cost_chf__include=record_field_include("actual_cost_chf"),
    detail__fields__actual_cost_description__include=record_field_include("actual_cost_description"),
    detail__fields__umsetzung_status_manual__include=record_field_include("umsetzung_status_manual"),
    detail__fields__kosten_status_manual__include=record_field_include("kosten_status_manual"),
    detail__fields__aufwand_status_manual__include=record_field_include("aufwand_status_manual"),
    delete__title=lambda form, **_: f"Record löschen: {form.instance}",
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
    delete__title=lambda form, **_: f"Verantwortlichkeit löschen: {form.instance}",
    delete__instance=lambda params, request, **_: ControllingRecordResponsibility.objects.get(
        pk=params.pk,
        controlling_record__measure__strategy_id=active_strategy_id(request),
    ),
)
