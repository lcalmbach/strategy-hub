from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from iommi import Column, Page, Table, html

from controlling.models import ControllingPeriod, ControllingRecord, ControllingRecordStatus
from core.strategy_context import get_active_strategy, select_active_strategy
from strategies.models import Strategy, StrategyLevel, StrategyLevelType


@login_required
def dashboard_home(request):
    active_strategy = get_active_strategy(request)
    active_strategy_id = active_strategy.pk if active_strategy else None

    selected_strategy_intro = (
        f"Aktive Strategie: {active_strategy.title}"
        if active_strategy
        else "Bitte waehle zuerst eine Strategie aus. Danach werden Handlungsfelder, Ziele, Massnahmen und Controlling-Records auf diese Strategie eingeschraenkt."
    )

    page = Page(
        title="Dashboard",
        parts__intro=html.p(
            selected_strategy_intro
        ),
        parts__summary=html.div(
            html.p(f"Aktive Strategien: {Strategy.objects.filter(is_active=True).count()}"),
            html.p(
                f"Massnahmen: {StrategyLevel.objects.filter(level=StrategyLevelType.MASSNAHME, strategy_id=active_strategy_id).count() if active_strategy_id else 0}"
            ),
            html.p(
                f"Offene Controlling-Records: {ControllingRecord.objects.filter(status=ControllingRecordStatus.OPEN, measure__strategy_id=active_strategy_id).count() if active_strategy_id else 0}"
            ),
        ),
        parts__active_strategies=Table(
            auto__model=Strategy,
            title="Strategie auswaehlen",
            rows=Strategy.objects.filter(is_active=True).order_by("title"),
            page_size=10,
            columns__id__include=False,
            columns__select=Column(
                display_name="Aktion",
                cell__value=lambda row, **_: "Ausgewaehlt" if active_strategy_id == row.pk else "Auswaehlen",
                cell__url=lambda row, **_: f"/select-strategy/{row.pk}/",
                sortable=False,
            ),
            columns__title__cell__url=lambda row, **_: f"/select-strategy/{row.pk}/",
            columns__vision__include=False,
            columns__mission__include=False,
            columns__short_description__include=False,
            columns__image__include=False,
            columns__document_url__include=False,
            columns__created_at__include=False,
            columns__updated_at__include=False,
            columns__created_by__include=False,
            columns__updated_by__include=False,
        ),
        parts__current_periods=Table(
            auto__model=ControllingPeriod,
            title="Aktuelle Perioden",
            rows=ControllingPeriod.objects.order_by("-start_date")[:10],
            page_size=10,
            columns__id__include=False,
            columns__name__cell__url=lambda row, **_: f"/controlling/periods/{row.pk}/",
            columns__created_at__include=False,
            columns__updated_at__include=False,
            columns__created_by__include=False,
            columns__updated_by__include=False,
        ),
        parts__open_records=Table(
            auto__model=ControllingRecord,
            title="Offene Records",
            rows=ControllingRecord.objects.select_related("measure", "period").filter(
                status=ControllingRecordStatus.OPEN,
                measure__strategy_id=active_strategy_id,
            )[:10],
            page_size=10,
            columns__id__include=False,
            columns__measure__cell__url=lambda row, **_: f"/controlling/records/{row.pk}/",
            columns__plan_result_description__include=False,
            columns__plan_effort_description__include=False,
            columns__plan_cost_description__include=False,
            columns__actual_result_description__include=False,
            columns__actual_effort_description__include=False,
            columns__actual_cost_description__include=False,
            columns__created_at__include=False,
            columns__updated_at__include=False,
            columns__created_by__include=False,
            columns__updated_by__include=False,
        ),
    )
    return page.as_view()(request)


@login_required
def select_strategy(request, strategy_id):
    select_active_strategy(request, strategy_id)
    return redirect("home")


@login_required
def profile_page(request):
    active_strategy = get_active_strategy(request)

    page = Page(
        title="Profil",
        parts__intro=html.div(
            html.p(f"Benutzername: {request.user.username}"),
            html.p(f"E-Mail: {request.user.email or '-'}"),
            html.p(
                f"Aktive Strategie: {active_strategy.title}"
                if active_strategy
                else "Aktive Strategie: keine ausgewaehlt"
            ),
        ),
    )
    return page.as_view()(request)


@login_required
@require_POST
def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/accounts/login/")
