import io
import re
import zipfile
from datetime import date, datetime, time
from decimal import Decimal
from xml.sax.saxutils import escape as xml_escape

from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.timezone import now

from core.strategy_context import require_active_strategy

from .models import Report


READ_ONLY_SQL_PATTERN = re.compile(r"^\s*(select|with)\b", flags=re.IGNORECASE)


class ReportExecutionError(ValueError):
    pass


def validate_read_only_sql(sql: str) -> None:
    if not READ_ONLY_SQL_PATTERN.match(sql or ""):
        raise ReportExecutionError("Nur read-only SQL mit SELECT oder WITH ist erlaubt.")

    sql_without_trailing_semicolon = (sql or "").strip().rstrip(";").strip()
    if ";" in sql_without_trailing_semicolon:
        raise ReportExecutionError("Mehrere SQL-Statements sind nicht erlaubt.")


def normalize_sql_params(params):
    if params in (None, {}, []):
        return None
    if isinstance(params, (dict, list, tuple)):
        return params
    raise ReportExecutionError("Report-Parameter müssen ein JSON-Objekt oder ein JSON-Array sein.")


def run_report(report: Report):
    validate_read_only_sql(report.sql)
    sql_params = normalize_sql_params(report.params)

    with connection.cursor() as cursor:
        cursor.execute(report.sql, sql_params)
        column_names = [column[0] for column in (cursor.description or [])]
        rows = cursor.fetchall()
    return column_names, rows


def excel_column_label(index: int) -> str:
    label = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        label = chr(65 + remainder) + label
    return label


def xml_text(value) -> str:
    return xml_escape(str(value), {'"': "&quot;", "'": "&apos;"})


def serialize_cell(value):
    if value is None:
        return "inlineStr", ""
    if isinstance(value, bool):
        return "b", "1" if value else "0"
    if isinstance(value, (int, float, Decimal)):
        return "n", str(value)
    if isinstance(value, (datetime, date, time)):
        return "inlineStr", value.isoformat()
    return "inlineStr", str(value)


def build_sheet_xml(columns, rows) -> str:
    sheet_rows = []

    if columns:
        header_cells = []
        for column_index, column in enumerate(columns, start=1):
            cell_ref = f"{excel_column_label(column_index)}1"
            header_cells.append(
                f'<c r="{cell_ref}" t="inlineStr"><is><t xml:space="preserve">{xml_text(column)}</t></is></c>'
            )
        sheet_rows.append(f'<row r="1">{"".join(header_cells)}</row>')

    start_row = 2 if columns else 1
    for row_index, row_values in enumerate(rows, start=start_row):
        cells = []
        for column_index, raw_value in enumerate(row_values, start=1):
            cell_ref = f"{excel_column_label(column_index)}{row_index}"
            cell_type, cell_value = serialize_cell(raw_value)
            if cell_type == "n":
                cells.append(f'<c r="{cell_ref}"><v>{xml_text(cell_value)}</v></c>')
            elif cell_type == "b":
                cells.append(f'<c r="{cell_ref}" t="b"><v>{cell_value}</v></c>')
            else:
                cells.append(
                    f'<c r="{cell_ref}" t="inlineStr"><is><t xml:space="preserve">{xml_text(cell_value)}</t></is></c>'
                )
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(sheet_rows)}</sheetData>"
        "</worksheet>"
    )


def build_xlsx(columns, rows) -> bytes:
    sheet_xml = build_sheet_xml(columns, rows)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as workbook:
        workbook.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/styles.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            "</Types>",
        )
        workbook.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="xl/workbook.xml"/>'
            "</Relationships>",
        )
        workbook.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Report" sheetId="1" r:id="rId1"/></sheets>'
            "</workbook>",
        )
        workbook.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            'Target="worksheets/sheet1.xml"/>'
            '<Relationship Id="rId2" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
            'Target="styles.xml"/>'
            "</Relationships>",
        )
        workbook.writestr(
            "xl/styles.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
            '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
            '<borders count="1"><border/></borders>'
            '<cellStyleXfs count="1"><xf/></cellStyleXfs>'
            '<cellXfs count="1"><xf xfId="0"/></cellXfs>'
            "</styleSheet>",
        )
        workbook.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return buffer.getvalue()


@login_required
@require_active_strategy
def reports_page(request):
    reports = Report.objects.all()
    selected_report = None
    columns = []
    rows = []
    error_message = None

    if request.method == "POST":
        report_id = request.POST.get("report")
        selected_report = get_object_or_404(Report, pk=report_id)
        try:
            columns, rows = run_report(selected_report)
        except ReportExecutionError as exc:
            error_message = str(exc)

    context = {
        "reports": reports,
        "selected_report": selected_report,
        "columns": columns,
        "rows": rows,
        "error_message": error_message,
    }
    return render(request, "reports/index.html", context)


@login_required
@require_active_strategy
def download_report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    columns, rows = run_report(report)

    timestamp = now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", report.name).strip("_") or "report"
    filename = f"{safe_name}_{timestamp}.xlsx"
    xlsx_bytes = build_xlsx(columns, rows)

    response = HttpResponse(
        xlsx_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
