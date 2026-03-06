from decimal import Decimal
from pathlib import Path
import re

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Count, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.text import slugify
from django.utils.safestring import mark_safe
from django.utils.html import escape, format_html, format_html_join
from django.views.decorators.http import require_POST

from iommi import Page, html
from plotly import graph_objects as go
from plotly.offline import plot

from controlling.models import ControllingPeriod, ControllingRecordStatus
from core.strategy_context import get_active_strategy, require_active_strategy, select_active_strategy
from strategies.models import ResponsibilityRole, StrategyLevel, StrategyLevelType

try:
    import markdown as markdown_lib
except ImportError:  # pragma: no cover - optional dependency
    markdown_lib = None


HELP_FILE_PATH = Path(settings.BASE_DIR) / "docs" / "HILFE.md"


def decimal_display(value):
    return f"{(value or Decimal('0.00')):.2f}"


def rounded_int_display(value):
    return f"{int((value or Decimal('0.00')).quantize(Decimal('1')))}"


def rounded_int_with_separator_display(value):
    number = int((value or Decimal("0.00")).quantize(Decimal("1")))
    return f"{number:,}".replace(",", "'")


def render_markdown_content(content: str) -> str:
    if markdown_lib is not None:
        md = markdown_lib.Markdown(extensions=["extra", "sane_lists", "toc"])
        body_html = md.convert(content)
        if md.toc:
            toc_html = f"<h2>Inhaltsverzeichnis</h2>{md.toc}"
            return f"{toc_html}{body_html}"
        return body_html

    def inline_format(text: str) -> str:
        escaped = escape(text)
        escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
        escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
        return escaped

    toc_items = []
    html_parts = []
    in_list = False

    for raw_line in content.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            continue

        if stripped.startswith("# "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            heading_text = stripped[2:].strip()
            heading_id = slugify(heading_text, allow_unicode=True)
            toc_items.append((heading_id, heading_text))
            html_parts.append(f'<h1 id="{heading_id}">{inline_format(heading_text)}</h1>')
            continue
        if stripped.startswith("## "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            heading_text = stripped[3:].strip()
            heading_id = slugify(heading_text, allow_unicode=True)
            toc_items.append((heading_id, heading_text))
            html_parts.append(f'<h2 id="{heading_id}">{inline_format(heading_text)}</h2>')
            continue
        if stripped.startswith("### "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            heading_text = stripped[4:].strip()
            heading_id = slugify(heading_text, allow_unicode=True)
            toc_items.append((heading_id, heading_text))
            html_parts.append(f'<h3 id="{heading_id}">{inline_format(heading_text)}</h3>')
            continue

        if stripped.startswith("- "):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f"<li>{inline_format(stripped[2:])}</li>")
            continue

        if in_list:
            html_parts.append("</ul>")
            in_list = False
        html_parts.append(f"<p>{inline_format(stripped)}</p>")

    if in_list:
        html_parts.append("</ul>")

    if not toc_items:
        return "\n".join(html_parts)

    toc_html = ["<h2>Inhaltsverzeichnis</h2>", "<ul>"]
    for heading_id, heading_text in toc_items:
        toc_html.append(f'<li><a href="#{heading_id}">{inline_format(heading_text)}</a></li>')
    toc_html.append("</ul>")
    return "\n".join(toc_html + html_parts)


def ampel_bucket(record):
    status = record.umsetzung_status_effective
    if not status:
        return None
    if status == "green":
        return "gruen"
    if status == "yellow":
        return "orange"
    return "rot"


def actuals_started(period):
    return period.status in {"open_for_actuals", "closed"}


def handlungsfeld_color_map(records):
    palette = [
        "#1d4ed8",
        "#059669",
        "#dc2626",
        "#d97706",
        "#7c3aed",
        "#0891b2",
        "#be123c",
        "#4f46e5",
    ]
    handlungsfelder = []
    for record in records:
        handlungsfeld = record.measure.parent.parent if record.measure.parent and record.measure.parent.parent else None
        if handlungsfeld and handlungsfeld.pk not in {pk for pk, _, _ in handlungsfelder}:
            handlungsfelder.append((handlungsfeld.pk, handlungsfeld.short_code, handlungsfeld.title))
    return {
        pk: {"color": palette[index % len(palette)], "label": f"{short_code} {title}".strip()}
        for index, (pk, short_code, title) in enumerate(handlungsfelder)
    }


def render_scatter_plot(records, plan_attr, actual_attr, title, x_label, y_label):
    if not records:
        return html.p(f"{title}: keine Daten vorhanden.")

    colors = handlungsfeld_color_map(records)
    traces_by_key = {}
    for record in records:
        handlungsfeld = record.measure.parent.parent if record.measure.parent and record.measure.parent.parent else None
        if handlungsfeld:
            handlungsfeld_key = handlungsfeld.pk
            label = colors[handlungsfeld_key]["label"]
            color = colors[handlungsfeld_key]["color"]
        else:
            handlungsfeld_key = "none"
            label = "Ohne Handlungsfeld"
            color = "#6b7280"

        if handlungsfeld_key not in traces_by_key:
            traces_by_key[handlungsfeld_key] = {
                "name": label,
                "x": [],
                "y": [],
                "text": [],
                "color": color,
            }

        traces_by_key[handlungsfeld_key]["x"].append(float(getattr(record, plan_attr)))
        traces_by_key[handlungsfeld_key]["y"].append(float(getattr(record, actual_attr)))
        traces_by_key[handlungsfeld_key]["text"].append(
            f"{record.measure.short_code} {record.measure.title}"
        )

    max_value = max(
        max(max(trace["x"]), max(trace["y"]))
        for trace in traces_by_key.values()
        if trace["x"] and trace["y"]
    )

    figure = go.Figure()
    for trace in traces_by_key.values():
        figure.add_trace(
            go.Scatter(
                x=trace["x"],
                y=trace["y"],
                text=trace["text"],
                name=trace["name"],
                mode="markers",
                hovertemplate="%{text}<br>Plan: %{x}<br>Ist: %{y}<extra>%{fullData.name}</extra>",
                marker={
                    "size": 12,
                    "color": trace["color"],
                    "line": {"width": 1, "color": "white"},
                },
            )
        )
    figure.update_layout(
        margin={"l": 60, "r": 24, "t": 56, "b": 56},
        height=380,
        paper_bgcolor="white",
        plot_bgcolor="#f8fafc",
        title={"text": title, "x": 0.02, "xanchor": "left"},
        xaxis={
            "title": x_label,
            "gridcolor": "#dbe4ee",
            "zeroline": False,
            "range": [0, max_value * 1.08],
        },
        yaxis={
            "title": y_label,
            "gridcolor": "#dbe4ee",
            "zeroline": False,
            "range": [0, max_value * 1.08],
        },
        legend={"orientation": "h", "y": -0.22},
        shapes=[
            {
                "type": "line",
                "x0": 0,
                "y0": 0,
                "x1": max_value * 1.05,
                "y1": max_value * 1.05,
                "line": {"color": "#94a3b8", "width": 1.5, "dash": "dot"},
            }
        ],
    )

    return html.div(
        mark_safe(
            plot(
                figure,
                output_type="div",
                include_plotlyjs=True,
                config={"displayModeBar": False, "responsive": True},
            )
        )
    )


def render_goal_summary_table(period):
    goal_rows = period.records.values(
        "measure__parent__short_code",
        "measure__parent__title",
    ).annotate(
        measures=Count("id"),
        plan_effort=Sum("plan_effort_person_days"),
        actual_effort=Sum("actual_effort_person_days"),
        plan_cost=Sum("plan_cost_chf"),
        actual_cost=Sum("actual_cost_chf"),
    ).order_by("measure__parent__short_code", "measure__parent__title")

    if not goal_rows:
        return html.p("Für diese Periode sind noch keine Records vorhanden.")

    body = format_html_join(
        "",
        "<tr>"
        "<td>{}</td>"
        "<td>{}</td>"
        "<td>{}</td>"
        "<td>{}</td>"
        "<td>{}</td>"
        "<td>{}</td>"
        "</tr>",
        (
            (
                f"{row['measure__parent__short_code']} {row['measure__parent__title']}".strip(),
                row["measures"],
                rounded_int_display(row["plan_effort"]),
                rounded_int_display(row["actual_effort"]),
                rounded_int_with_separator_display(row["plan_cost"]),
                rounded_int_with_separator_display(row["actual_cost"]),
            )
            for row in goal_rows
        ),
    )
    return html.div(
        format_html(
            "<table>"
            "<thead>"
            "<tr>"
            "<th>Ziel</th>"
            "<th>Massnahmen</th>"
            "<th>Plan-Aufwand</th>"
            "<th>Ist-Aufwand</th>"
            "<th>Plan-Kosten CHF</th>"
            "<th>Ist-Kosten CHF</th>"
            "</tr>"
            "</thead>"
            "<tbody>{}</tbody>"
            "</table>",
            body,
        )
    )


def colored_dot(color, label):
    return format_html(
        '<span title="{}" aria-label="{}" style="display:inline-block;width:12px;height:12px;border-radius:999px;background:{};"></span>',
        label,
        label,
        color,
    )


def render_people_summary_table(period):
    summaries = {}
    for record in period.records.all():
        bucket = ampel_bucket(record)
        responsibilities = [
            responsibility
            for responsibility in record.measure.responsibilities.all()
            if responsibility.role == ResponsibilityRole.RESPONSIBLE
        ]

        seen_person_ids = set()
        for responsibility in responsibilities:
            person = responsibility.person
            if person.pk in seen_person_ids:
                continue
            seen_person_ids.add(person.pk)

            display_name = person.user.get_full_name().strip() or person.short_code
            summary = summaries.setdefault(
                person.pk,
                {
                    "name": display_name,
                    "short_code": person.short_code,
                    "measures": 0,
                    "gruen": 0,
                    "orange": 0,
                    "rot": 0,
                    "ohne_ampel": 0,
                },
            )
            summary["measures"] += 1
            if bucket is None:
                summary["ohne_ampel"] += 1
            else:
                summary[bucket] += 1

    if not summaries:
        return html.p("Für diese Periode sind keine verantwortlichen Mitarbeitenden zugeordnet.")

    rows = sorted(summaries.values(), key=lambda item: (item["name"], item["short_code"]))
    body = format_html_join(
        "",
        "<tr>"
        "<td>{}</td>"
        "<td>{}</td>"
        '<td style="text-align:center;">{}</td>'
        '<td style="text-align:center;">{}</td>'
        '<td style="text-align:center;">{}</td>'
        '<td style="text-align:center;">{}</td>'
        "</tr>",
        (
            (
                f"{row['name']} ({row['short_code']})",
                row["measures"],
                row["gruen"],
                row["orange"],
                row["rot"],
                row["ohne_ampel"],
            )
            for row in rows
        ),
    )
    return html.div(
        format_html(
            '<table style="width:100%;">'
            "<thead>"
            "<tr>"
            "<th>Mitarbeitende</th>"
            "<th>Anzahl Massnahmen</th>"
            '<th style="width:72px;text-align:center;">{}</th>'
            '<th style="width:72px;text-align:center;">{}</th>'
            '<th style="width:72px;text-align:center;">{}</th>'
            '<th style="width:72px;text-align:center;">{}</th>'
            "</tr>"
            "</thead>"
            "<tbody>{}</tbody>"
            "</table>",
            colored_dot("#16a34a", "Grün"),
            colored_dot("#f59e0b", "Orange"),
            colored_dot("#dc2626", "Rot"),
            colored_dot("#9ca3af", "Ohne Ampel"),
            body,
        )
    )


def render_period_summary(period):
    records = list(period.records.all())
    total_records = len(records)
    open_records = sum(
        1
        for record in records
        if record.status_id and record.status.code == ControllingRecordStatus.OPEN
    )
    avg_fulfillment = (
        sum(record.actual_fulfillment_percent for record in records) / total_records if total_records else Decimal("0.00")
    )
    total_plan_effort = sum((record.plan_effort_person_days for record in records), Decimal("0.00"))
    total_actual_effort = sum((record.actual_effort_person_days for record in records), Decimal("0.00"))
    total_plan_cost = sum((record.plan_cost_chf for record in records), Decimal("0.00"))
    total_actual_cost = sum((record.actual_cost_chf for record in records), Decimal("0.00"))

    status_counts = {}
    for record in records:
        status_label = record.status.name if record.status_id else "Ohne Status"
        status_counts[status_label] = status_counts.get(status_label, 0) + 1
    status_summary = ", ".join(f"{label}: {count}" for label, count in status_counts.items()) or "Keine Records"

    ampel_counts = {"gruen": 0, "orange": 0, "rot": 0}
    for record in records:
        bucket = ampel_bucket(record)
        if bucket:
            ampel_counts[bucket] += 1

    section_parts = [
        html.h2(f"Periode {period.name}"),
        html.p(f"Status: {period.get_status_display()}"),
        html.p(f"Zeitraum: {period.start_date} bis {period.end_date}"),
        html.p(f"Record-Status: {status_summary}"),
        html.p(f"Offene Records: {open_records} von {total_records}"),
        html.p(f"Durchschnittlicher Erfüllungsgrad: {decimal_display(avg_fulfillment)}%"),
        html.p(
            f"Gesamt Aufwand Plan/Ist: {rounded_int_display(total_plan_effort)} / {rounded_int_display(total_actual_effort)} PT"
        ),
        html.p(
            f"Gesamt Kosten Plan/Ist: {rounded_int_with_separator_display(total_plan_cost)} / {rounded_int_with_separator_display(total_actual_cost)} CHF"
        ),
    ]

    if actuals_started(period):
        section_parts.append(
            html.p(
                f"Ampel Massnahmen: Grün {ampel_counts['gruen']}, Orange {ampel_counts['orange']}, Rot {ampel_counts['rot']}"
            )
        )
    else:
        section_parts.append(html.p("Ampel Massnahmen: Controlling-Start noch nicht erreicht."))

    section_parts.append(html.h3("Plan und Ist pro Ziel"))
    section_parts.append(render_goal_summary_table(period))
    section_parts.append(
        render_scatter_plot(
            records,
            "plan_cost_chf",
            "actual_cost_chf",
            "Scatter Plot Kosten",
            "Kosten geplant",
            "Kosten Ist",
        )
    )
    section_parts.append(
        render_scatter_plot(
            records,
            "plan_effort_person_days",
            "actual_effort_person_days",
            "Scatter Plot Aufwand",
            "Aufwand geplant",
            "Aufwand Ist",
        )
    )
    section_parts.append(html.h3("Verantwortliche Mitarbeitende"))
    section_parts.append(render_people_summary_table(period))

    return html.div(*section_parts)


@login_required
@require_active_strategy
def dashboard_home(request):
    active_strategy = get_active_strategy(request)

    periods = ControllingPeriod.objects.filter(strategy=active_strategy).prefetch_related(
        "records",
        "records__measure",
        "records__measure__parent",
        "records__measure__parent__parent",
        "records__measure__responsibilities",
        "records__measure__responsibilities__person",
        "records__measure__responsibilities__person__user",
    ).order_by("-start_date", "-pk")

    page_parts = {
        "title": "Dashboard",
        "parts__intro": html.div(
            html.h1(active_strategy.title),
            html.p(f"Handlungsfelder: {StrategyLevel.objects.filter(strategy=active_strategy, level=StrategyLevelType.HANDLUNGSFELD).count()}"),
            html.p(f"Ziele: {StrategyLevel.objects.filter(strategy=active_strategy, level=StrategyLevelType.ZIEL).count()}"),
            html.p(f"Massnahmen: {StrategyLevel.objects.filter(strategy=active_strategy, level=StrategyLevelType.MASSNAHME).count()}"),
        ),
    }

    if periods:
        for index, period in enumerate(periods):
            page_parts[f"parts__period_{index}"] = render_period_summary(period)
    else:
        page_parts["parts__periods_empty"] = html.p("Für die ausgewählte Strategie sind noch keine Controlling-Perioden erfasst.")

    page = Page(**page_parts)
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
                else "Aktive Strategie: keine ausgewählt"
            ),
        ),
    )
    return page.as_view()(request)


@login_required
def help_page(request):
    if HELP_FILE_PATH.exists():
        markdown_content = HELP_FILE_PATH.read_text(encoding="utf-8")
    else:
        markdown_content = "# Hilfe\n\nDie Hilfedatei wurde nicht gefunden."

    page = Page(
        title="Hilfe",
        parts__content=html.div(
            mark_safe(render_markdown_content(markdown_content)),
        ),
    )
    return page.as_view()(request)


@login_required
@require_POST
def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/accounts/login/")
