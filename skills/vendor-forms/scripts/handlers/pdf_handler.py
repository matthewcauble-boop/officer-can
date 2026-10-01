"""
PDF extraction and filling.

Extraction uses pypdf (read-only, no appearance-stream work needed).
Filling uses PyMuPDF (fitz) — it generates proper appearance streams so the
filled values render correctly in EVERY PDF viewer (Adobe Reader, Chrome,
Gmail preview, Mac Preview, mobile apps, etc.).

Note on history: an earlier version of this file used pypdf for fill +
NeedAppearances=True flag. That works in Adobe Reader but produces blank-
looking fields in many other viewers because they don't regenerate
appearances from raw field data. PyMuPDF fixes this by writing real
appearance streams at fill time. Confirmed against a real supplier's new
customer form and the Texas 01-339 resale certificate.

ONLY handles PDFs with AcroForm fields (named fillable form fields).
Flattened or scanned PDFs return fillable=False — the caller should drop
those into manual-review/.

EXTRACTION format:
{
    "fields": [
        {"name": "company_name", "type": "/Tx", "current_value": "", "hint": "Company Name"},
        ...
    ],
    "page_count": 3
}

FILL OPERATION locator:
    {"type": "field", "name": "company_name"} → set field value to op["value"]
    {"type": "skip", "field": "signature"}    → intentionally not filled
"""

from __future__ import annotations

import io
import logging

import fitz  # PyMuPDF
from pypdf import PdfReader

log = logging.getLogger("form-fill.pdf")


def extract_pdf_structure(raw: bytes) -> tuple[dict, bool, list[str]]:
    reader = PdfReader(io.BytesIO(raw))
    notes: list[str] = []

    fields_dict = reader.get_fields() or {}
    fields: list[dict] = []
    for name, info in fields_dict.items():
        fields.append({
            "name": name,
            "type": str(info.get("/FT", "")),
            "current_value": str(info.get("/V", "")),
            "hint": str(info.get("/TU", "")) or name,
        })

    fillable = len(fields) > 0
    if not fillable:
        notes.append(
            "PDF has no AcroForm fields — likely flattened or scanned. "
            "Cannot auto-fill. Send to manual-review/."
        )

    structure = {"fields": fields, "page_count": len(reader.pages)}
    return structure, fillable, notes


def _fit_text(widget, value) -> None:
    """Shrink a single-line text field's font so the value fits its box (a 10pt date in a narrow box got clipped).
    Leaves auto-size (0) fields, multi-line fields and anything already fitting alone; never below 6pt."""
    try:
        if widget.field_type != fitz.PDF_WIDGET_TYPE_TEXT or not isinstance(value, str) or not value:
            return
        if widget.field_flags & fitz.PDF_TX_FIELD_IS_MULTILINE:
            return
        size = widget.text_fontsize or 0
        if size <= 0:
            return
        room = widget.rect.width - 4          # PDF viewers pad text fields ~2pt each side
        width = fitz.get_text_length(value, fontname="helv", fontsize=size)
        if width > room > 0:
            widget.text_fontsize = max(6.0, round(size * room / width, 1))
    except Exception:
        log.debug("could not size %r", getattr(widget, "field_name", "?"))


def fill_pdf(raw: bytes, operations: list[dict]) -> tuple[bytes, list[dict]]:
    """Fill an AcroForm PDF using PyMuPDF.

    PyMuPDF generates real appearance streams when widget.update() is called,
    so filled values render in every PDF viewer (not just Adobe).
    """
    report: list[dict] = []

    # Build a field_name -> value map and capture skip ops
    field_updates: dict[str, str] = {}
    for op in operations:
        locator = op.get("locator") or {}
        value = op.get("value", "")
        note = op.get("note")
        loc_type = locator.get("type")

        if loc_type == "skip":
            report.append({
                "locator": locator,
                "value": value,
                "status": "skipped",
                "detail": note or "intentionally skipped",
            })
        elif loc_type == "field":
            name = locator.get("name")
            if not name:
                report.append({"locator": locator, "value": value, "status": "failed", "detail": "missing field name"})
                continue
            field_updates[name] = str(value)
            # Tentative success — flipped to failed below if the field doesn't exist in the PDF
            report.append({"locator": locator, "value": value, "status": "filled", "detail": note})
        else:
            report.append({"locator": locator, "value": value, "status": "failed", "detail": f"unknown locator type: {loc_type!r}"})

    doc = fitz.open(stream=raw, filetype="pdf")
    seen_fields: set[str] = set()

    try:
        for page in doc:
            for widget in page.widgets():
                fname = widget.field_name
                if fname in field_updates:
                    try:
                        widget.field_value = field_updates[fname]
                        _fit_text(widget, field_updates[fname])
                        widget.update()  # this generates the appearance stream
                        seen_fields.add(fname)
                    except Exception as e:
                        log.exception("failed to update widget %r", fname)
                        # Mark the matching report entry as failed
                        for entry in report:
                            if entry["locator"].get("name") == fname and entry["status"] == "filled":
                                entry["status"] = "failed"
                                entry["detail"] = f"widget update error: {e}"

        # Any requested fields that weren't found on any page → mark as failed
        missing = set(field_updates) - seen_fields
        for missing_name in missing:
            for entry in report:
                if entry["locator"].get("name") == missing_name and entry["status"] == "filled":
                    entry["status"] = "failed"
                    entry["detail"] = f"field not present in PDF: {missing_name!r}"

        out = io.BytesIO()
        doc.save(out, garbage=4, deflate=True)
        return out.getvalue(), report
    finally:
        doc.close()
