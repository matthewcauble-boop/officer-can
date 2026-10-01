"""
.xlsx / .xlsm extraction and filling using openpyxl.

Designed for vendor onboarding workbooks where labels sit in one column and the
answer cell sits in an adjacent column on the same row. A typical large-supplier
customer setup workbook puts labels in column G and answer cells in column U on per-sheet pages like 'Sold - to',
'Ship - to', 'Bill - to', and 'Summary and Completion'.

EXTRACTION format:
{
    "sheets": [
        {
            "name": "Sold - to",
            "rows": [
                {"row": 14, "label": "Company name", "answer_cell": "U14", "current_value": ""},
                {"row": 17, "label": "Street",        "answer_cell": "U17", "current_value": ""},
                ...
            ],
            "answer_col": "U",
            "label_col": "G"
        },
        ...
    ],
    "macro_enabled": true,
    "named_ranges": ["alert_incompleteitems", "languageoffset", ...]
}

FILL OPERATION locator shapes:

  Set a specific A1 cell on a named sheet (most precise, most common):
    {"type": "cell_address", "sheet": "Sold - to", "cell": "U14"}

  Find a row whose label-column cell matches `label` (case-insensitive,
  whitespace-trimmed), then write to the same row's answer column. Optional
  `sheet` scopes the search; otherwise the first matching sheet wins. Useful
  when row numbers shift between versions of a vendor's form template:
    {"type": "after_label", "sheet": "Sold - to", "label": "Company name"}

  Write to a workbook-defined named range:
    {"type": "named_range", "name": "company_name_sold_to"}

  Skip (record an intentional non-fill, e.g. signature, bank account):
    {"type": "skip", "field": "Bank Account Number"}

The handler auto-detects label/answer columns by scanning for a known set of
"sentinel" labels (Company name, Street, City, ...) in column G of the first
data sheet, but allows the caller to override per-sheet via:
    {"locator": {"type": "after_label", "sheet": "Sold - to",
                 "label_col": "G", "answer_col": "U", "label": "Company name"}}

Macro-enabled workbooks (.xlsm) are preserved via openpyxl's keep_vba=True so
the form's validation macros survive the round-trip.
"""

from __future__ import annotations

import io
import logging
from typing import Any

from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string
from openpyxl.utils.cell import coordinate_from_string

log = logging.getLogger("form-fill.xlsx")

# Sheets that are pure helper/translation tables, never user-facing
HELPER_SHEET_HINTS = ("internal", "dropdown", "translation", "lookup", "config",
                     "_helper", "setup_main", "setup_drop", "_helpers")

# Labels that strongly indicate this is a vendor onboarding form (used for the
# auto-detect of label/answer columns).
SENTINEL_LABELS = {
    "company name", "street", "city", "country", "postal code", "region/state",
    "general email address", "first name general contact person",
    "telephone", "currency", "payment method", "vat/tax registration number",
    "name of requester", "date of submission",
}


# ---- extraction --------------------------------------------------------------

def extract_xlsx_structure(raw: bytes, keep_vba: bool = False) -> tuple[dict, bool, list[str]]:
    """Walk every user-facing sheet, surface (row, label, answer-cell, current value).

    Loads with data_only=True so we see cached values of formula-driven labels
    (vendor forms commonly compute labels via i18n lookups). Filling uses a
    separate data_only=False load so formulas survive the round-trip.
    """
    wb = load_workbook(io.BytesIO(raw), keep_vba=keep_vba, data_only=True)

    sheets: list[dict] = []
    notes: list[str] = []
    macro_enabled = keep_vba

    for sn in wb.sheetnames:
        if any(h in sn.lower() for h in HELPER_SHEET_HINTS):
            continue
        ws = wb[sn]
        label_col, answer_col = _detect_label_answer_cols(ws)
        if not label_col or not answer_col:
            continue

        rows: list[dict] = []
        l_idx = column_index_from_string(label_col)
        a_idx = column_index_from_string(answer_col)
        for r in range(1, ws.max_row + 1):
            label = ws.cell(row=r, column=l_idx).value
            if not label:
                continue
            label_s = str(label).strip()
            # Skip empty + formula-string cells (data_only failed to cache)
            if label_s.startswith("=") or not label_s:
                continue
            current = ws.cell(row=r, column=a_idx).value
            rows.append({
                "row": r,
                "label": label_s,
                "answer_cell": f"{answer_col}{r}",
                "current_value": "" if current is None else str(current),
            })

        if rows:
            sheets.append({
                "name": sn,
                "rows": rows,
                "label_col": label_col,
                "answer_col": answer_col,
            })

    named_ranges: list[str] = []
    try:
        named_ranges = [n.name for n in wb.defined_names.definedName]
    except AttributeError:
        # openpyxl >= 3.1
        try:
            named_ranges = list(wb.defined_names)
        except Exception:
            named_ranges = []

    structure = {
        "sheets": sheets,
        "macro_enabled": macro_enabled,
        "named_ranges": named_ranges,
    }

    fillable = len(sheets) > 0
    if not fillable:
        notes.append("No data sheets with label/answer column pairs detected. Likely not a fillable workbook.")
    if macro_enabled:
        notes.append("Macro-enabled workbook (.xlsm) — macros preserved on round-trip.")

    return structure, fillable, notes


def _detect_label_answer_cols(ws) -> tuple[str | None, str | None]:
    """Return (label_col, answer_col) by scanning for sentinel labels.

    Label column: the column with the most sentinel-label matches in rows 1..200.

    Answer column: the column to the right of label_col where merged-range
    anchors most often line up with the rows that contain labels. Vendor
    onboarding forms almost always render the answer "box" as a horizontal
    merge (e.g. U:W or U:AD) anchored on the same row as the label, so this
    pattern is a strong fingerprint. Falls back to "first column right of
    label_col with any pre-filled value" if no merge pattern emerges, then
    finally to label_col+4.
    """
    rows_to_scan = min(ws.max_row, 300)
    cols_to_scan = min(ws.max_column, 60)

    # 1. Label column — highest sentinel count
    label_counts: dict[int, int] = {}
    sentinel_rows: set[int] = set()
    for r in range(1, rows_to_scan + 1):
        for c in range(1, cols_to_scan + 1):
            v = ws.cell(row=r, column=c).value
            if not isinstance(v, str):
                continue
            if v.strip().lower() in SENTINEL_LABELS:
                label_counts[c] = label_counts.get(c, 0) + 1

    if not label_counts:
        return None, None

    label_c = max(label_counts, key=label_counts.get)

    # Expand to ALL label-bearing rows in label_c (any non-empty, non-formula
    # string), not just sentinel matches — covers form-specific labels like
    # "Is the Ship-to the same as the Sold-to address?" that aren't in SENTINEL_LABELS.
    label_rows: set[int] = set()
    for r in range(1, rows_to_scan + 1):
        v = ws.cell(row=r, column=label_c).value
        if isinstance(v, str) and v.strip() and not v.startswith("="):
            label_rows.add(r)

    # 2. Answer column — column-right-of-label with the most merge anchors
    #    landing on label rows. This catches the U:W / U:AD input-box pattern.
    #    Tiebreaker: prefer the LEFTMOST candidate (forms put inputs closest to
    #    labels; rightmost columns tend to be remarks/translation/notes panes).
    merge_anchor_counts: dict[int, int] = {}
    for merge in ws.merged_cells.ranges:
        if merge.min_col <= label_c:
            continue
        if merge.min_row in label_rows:
            merge_anchor_counts[merge.min_col] = merge_anchor_counts.get(merge.min_col, 0) + 1

    answer_c = None
    if merge_anchor_counts:
        max_count = max(merge_anchor_counts.values())
        # Treat anything within ~70% of the top score as effectively tied — pick leftmost.
        candidates = [c for c, n in merge_anchor_counts.items() if n >= max_count * 0.7]
        answer_c = min(candidates)

    # Fallback: first column > label_c with any pre-filled non-formula value on
    # a label row (catches templates with example answers like "Yes"/"No")
    if answer_c is None:
        for c in range(label_c + 1, cols_to_scan + 1):
            for r in label_rows:
                v = ws.cell(row=r, column=c).value
                if v is None or (isinstance(v, str) and (v.startswith("=") or v.strip() == "")):
                    continue
                answer_c = c
                break
            if answer_c is not None:
                break

    # Last resort fallback — label_c + 14 (vendor forms tend to be wide)
    if answer_c is None:
        answer_c = min(label_c + 14, cols_to_scan)

    from openpyxl.utils import get_column_letter
    return get_column_letter(label_c), get_column_letter(answer_c)


# ---- filling -----------------------------------------------------------------

def fill_xlsx(raw: bytes, operations: list[dict], keep_vba: bool = False) -> tuple[bytes, list[dict]]:
    """Apply each fill operation. Returns (filled_bytes, per-op report).

    Uses TWO workbook loads:
      - wb_data:  data_only=True  — formula labels resolved to text, for after_label lookups
      - wb:       data_only=False — formulas preserved, this is what we write/save
    """
    wb = load_workbook(io.BytesIO(raw), keep_vba=keep_vba, data_only=False)
    wb_data = load_workbook(io.BytesIO(raw), keep_vba=keep_vba, data_only=True)
    report: list[dict] = []

    for op in operations:
        locator = op.get("locator") or {}
        value = op.get("value", "")
        note = op.get("note")
        loc_type = locator.get("type")

        try:
            if loc_type == "skip":
                report.append({
                    "locator": locator,
                    "value": value,
                    "status": "skipped",
                    "detail": note or "intentionally skipped",
                })

            elif loc_type == "cell_address":
                _fill_cell_address(wb, locator, value)
                report.append({"locator": locator, "value": value, "status": "filled", "detail": note})

            elif loc_type == "after_label":
                ok, detail = _fill_after_label(wb, locator, value, wb_data=wb_data)
                report.append({
                    "locator": locator,
                    "value": value,
                    "status": "filled" if ok else "failed",
                    "detail": note if ok else detail,
                })

            elif loc_type == "named_range":
                ok, detail = _fill_named_range(wb, locator, value)
                report.append({
                    "locator": locator,
                    "value": value,
                    "status": "filled" if ok else "failed",
                    "detail": note if ok else detail,
                })

            else:
                report.append({
                    "locator": locator,
                    "value": value,
                    "status": "failed",
                    "detail": f"unknown locator type: {loc_type!r}",
                })

        except Exception as e:
            log.exception("op failed: %s", op)
            report.append({"locator": locator, "value": value, "status": "failed", "detail": str(e)})

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue(), report


# ---- low-level helpers -------------------------------------------------------

def _fill_cell_address(wb, locator: dict, value: Any) -> None:
    sheet = locator.get("sheet")
    cell_ref = locator.get("cell")
    if not sheet or not cell_ref:
        raise ValueError("cell_address locator requires 'sheet' and 'cell'")
    if sheet not in wb.sheetnames:
        raise ValueError(f"sheet not found: {sheet!r}")
    ws = wb[sheet]
    # Resolve merged-range top-left so writes hit the anchor (openpyxl rule)
    coord = _anchor_cell(ws, cell_ref)
    ws[coord] = value


def _fill_after_label(wb, locator: dict, value: Any, wb_data=None) -> tuple[bool, str]:
    """Find a row whose label-column cell equals `label` (case-insensitive, trimmed),
    then write `value` to the answer-column cell on the same row.

    Label lookups go through wb_data (data_only=True) so formula-resolved labels
    work; writes happen on wb (data_only=False) so formulas in other cells survive.
    """
    target_sheet = locator.get("sheet")
    label = (locator.get("label") or "").strip().lower()
    if not label:
        return False, "after_label locator requires 'label'"

    lookup_wb = wb_data or wb

    sheets = [target_sheet] if target_sheet else [
        sn for sn in wb.sheetnames if not any(h in sn.lower() for h in HELPER_SHEET_HINTS)
    ]

    for sn in sheets:
        if sn not in wb.sheetnames:
            continue
        ws_write = wb[sn]
        ws_lookup = lookup_wb[sn]
        label_col_letter = locator.get("label_col")
        answer_col_letter = locator.get("answer_col")
        if not label_col_letter or not answer_col_letter:
            detected = _detect_label_answer_cols(ws_lookup)
            label_col_letter = label_col_letter or detected[0]
            answer_col_letter = answer_col_letter or detected[1]
        if not label_col_letter or not answer_col_letter:
            continue

        l_idx = column_index_from_string(label_col_letter)
        for r in range(1, ws_lookup.max_row + 1):
            cell_val = ws_lookup.cell(row=r, column=l_idx).value
            if not isinstance(cell_val, str):
                continue
            if cell_val.strip().lower() == label:
                coord = _anchor_cell(ws_write, f"{answer_col_letter}{r}")
                ws_write[coord] = value
                return True, ""
    return False, f"label not found: {locator.get('label')!r}"


def _fill_named_range(wb, locator: dict, value: Any) -> tuple[bool, str]:
    name = locator.get("name")
    if not name:
        return False, "named_range locator requires 'name'"
    dn = wb.defined_names.get(name) if hasattr(wb.defined_names, "get") else wb.defined_names.get(name)
    if dn is None:
        return False, f"named range not defined: {name!r}"
    # named range destinations is a generator of (sheet, range)
    for sheet_name, range_str in dn.destinations:
        if sheet_name not in wb.sheetnames:
            continue
        ws = wb[sheet_name]
        # Use the first cell of the range
        first_cell = range_str.split(":")[0].replace("$", "")
        coord = _anchor_cell(ws, first_cell)
        ws[coord] = value
        return True, ""
    return False, f"named range {name!r} has no resolvable destinations"


def _anchor_cell(ws, cell_ref: str) -> str:
    """If cell_ref falls inside a merged range, return the merge anchor (top-left).

    openpyxl raises when you try to write a non-anchor merged cell, so we resolve
    here. If not merged, returns cell_ref unchanged.
    """
    cell_ref = cell_ref.replace("$", "").upper()
    col_letter, row_num = coordinate_from_string(cell_ref)
    col_idx = column_index_from_string(col_letter)
    for merge in ws.merged_cells.ranges:
        if (merge.min_row <= row_num <= merge.max_row
                and merge.min_col <= col_idx <= merge.max_col):
            from openpyxl.utils import get_column_letter
            return f"{get_column_letter(merge.min_col)}{merge.min_row}"
    return cell_ref
