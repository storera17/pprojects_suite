from __future__ import annotations

import datetime as _dt
import zipfile
from dataclasses import dataclass, field
from numbers import Real
from pathlib import Path
from typing import Any

_CONTENT_TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"
_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
_OFFICE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


@dataclass
class Sheet:
    name: str
    headers: list[str]
    rows: list[list[Any]] = field(default_factory=list)


def write_workbook(path: str | Path, sheets: list[Sheet]) -> Path:
    """Write ``sheets`` to an ``.xlsx`` file at ``path`` and return the resolved path."""
    if not sheets:
        sheets = [Sheet("Sheet1", [], [])]
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _content_types_xml(len(sheets)))
        archive.writestr("_rels/.rels", _root_rels_xml())
        archive.writestr("xl/workbook.xml", _workbook_xml(sheets))
        archive.writestr("xl/_rels/workbook.xml.rels", _workbook_rels_xml(len(sheets)))
        for index, sheet in enumerate(sheets, start=1):
            archive.writestr(f"xl/worksheets/sheet{index}.xml", _sheet_xml(sheet))
    return target


def _content_types_xml(sheet_count: int) -> str:
    overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
        f'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for i in range(1, sheet_count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Types xmlns="{_CONTENT_TYPES}">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        f"{overrides}</Types>"
    )


def _root_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{_REL}">'
        f'<Relationship Id="rId1" Type="{_OFFICE_REL}/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )


def _workbook_xml(sheets: list[Sheet]) -> str:
    entries = "".join(
        f'<sheet name="{_escape(_safe_sheet_name(sheet.name))}" sheetId="{i}" r:id="rId{i}"/>'
        for i, sheet in enumerate(sheets, start=1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<workbook xmlns="{_MAIN}" xmlns:r="{_OFFICE_REL}">'
        f"<sheets>{entries}</sheets></workbook>"
    )


def _workbook_rels_xml(sheet_count: int) -> str:
    rels = "".join(
        f'<Relationship Id="rId{i}" Type="{_OFFICE_REL}/worksheet" Target="worksheets/sheet{i}.xml"/>'
        for i in range(1, sheet_count + 1)
    )
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{_REL}">{rels}</Relationships>'
    )


def _sheet_xml(sheet: Sheet) -> str:
    rows_xml: list[str] = []
    all_rows = [sheet.headers, *sheet.rows] if sheet.headers else sheet.rows
    for row_index, row in enumerate(all_rows, start=1):
        cells = "".join(_cell_xml(row_index, col_index, value) for col_index, value in enumerate(row, start=1))
        rows_xml.append(f'<row r="{row_index}">{cells}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet xmlns="{_MAIN}"><sheetData>{"".join(rows_xml)}</sheetData></worksheet>'
    )


def _cell_xml(row_index: int, col_index: int, value: Any) -> str:
    ref = f"{_column_letter(col_index)}{row_index}"
    if isinstance(value, bool):
        # bool is a subclass of int; treat as text so TRUE/FALSE read clearly.
        return f'<c r="{ref}" t="inlineStr"><is><t>{_escape(str(value))}</t></is></c>'
    if isinstance(value, Real):
        return f'<c r="{ref}"><v>{value}</v></c>'
    if value is None:
        return f'<c r="{ref}" t="inlineStr"><is><t></t></is></c>'
    text = value.isoformat() if isinstance(value, (_dt.datetime, _dt.date)) else str(value)
    return f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{_escape(text)}</t></is></c>'


def _column_letter(index: int) -> str:
    letters = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def _safe_sheet_name(name: str) -> str:
    # Excel forbids these characters in sheet names and caps length at 31.
    cleaned = "".join(" " if ch in "[]:*?/\\" else ch for ch in name).strip() or "Sheet"
    return cleaned[:31]


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
