"""Fill flat PDFs: forms with no fillable fields, just printed "Label: ______" lines, drawn lines and boxes.

  find_blanks(raw, words=None) -> [{"label", "section", "loc"}]    loc: {"type": "flat", "page", "rect"}
                                                                  or {"type": "flat_choice", "page", "options": [...]}
  fill_flat(raw, ops)          -> (filled_bytes, results)          text written at each blank, then read back to verify

Blanks come from three places on each page:
  1. runs of underscores in the text ("Company Legal Name:_______"), label = the text before the run on that line;
  2. drawn horizontal lines with nothing written on them, label = the text just left of the line, else just above;
  3. empty drawn boxes (bigger than a checkbox), label = text left of the box, else above it.
"□ Option" glyph groups become one multiple-choice blank ("Ownership: □ Partnership □ Corporation ...").
Scanned pages have no text layer: pass `words` from a text recognizer (see ocr.py) in PyMuPDF's
get_text("words") shape per page, and the same rules apply.
"""
import io, re
import pymupdf

UNDERSCORES = re.compile(r"_{3,}")
BOX_GLYPHS = "□☐❑❒◻▢"
HEADING = re.compile(r"^[A-Z][\w ,/&().'-]{2,70}:?$")
MIN_LINE, MIN_BOX_W = 40, 30

def _lines(page):
    """Text lines with per-character boxes: [{"text", "chars": [(c, rect)], "rect", "bold"}] in reading order."""
    out = []
    for b in page.get_text("rawdict")["blocks"]:
        for ln in b.get("lines", []):
            chars, bold = [], False
            for sp in ln["spans"]:
                bold |= bool(sp["flags"] & 16) or "Bold" in sp.get("font", "")
                chars += [(c["c"], pymupdf.Rect(c["bbox"])) for c in sp["chars"]]
            if chars:
                out.append({"text": "".join(c for c, _ in chars), "chars": chars,
                            "rect": pymupdf.Rect(ln["bbox"]), "bold": bold})
    out.sort(key=lambda l: (round(l["rect"].y1 / 3), l["rect"].x0))
    return out

def _lines_from_words(words):
    """OCR words [(x0, y0, x1, y1, text, ...)] -> the same line shape (characters spread evenly over each word)."""
    rows = {}
    for w in words:
        x0, y0, x1, y1, t = w[:5]
        rows.setdefault(round((y0 + y1) / 2 / 6), []).append((x0, y0, x1, y1, t))
    out = []
    for _, ws in sorted(rows.items()):
        ws.sort(); chars = []
        for i, (x0, y0, x1, y1, t) in enumerate(ws):
            step = (x1 - x0) / max(len(t), 1)
            chars += [(c, pymupdf.Rect(x0 + k * step, y0, x0 + (k + 1) * step, y1)) for k, c in enumerate(t)]
            if i < len(ws) - 1:
                chars.append((" ", pymupdf.Rect(x1, y0, ws[i + 1][0], y1)))
        r = pymupdf.Rect(ws[0][0], min(w[1] for w in ws), ws[-1][2], max(w[3] for w in ws))
        out.append({"text": "".join(c for c, _ in chars), "chars": chars, "rect": r, "bold": False})
    return out

def _clean_label(s):
    s = re.sub(r"[_]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip(" :#.-\t")
    return s

def _is_heading(line):
    t = line["text"].strip()
    return bool(t) and "_" not in t and not any(g in t for g in BOX_GLYPHS) and len(t) <= 70 and \
        (HEADING.match(t) and (t.endswith(":") or line["bold"] or t.isupper()))

def _text_left_of(lines, rect, max_gap=220, after_x=-1):
    """Text on the same row, ending just left of rect (and starting after after_x: the previous blank on the row)."""
    best = None
    for l in lines:
        if abs((l["rect"].y0 + l["rect"].y1) / 2 - (rect.y0 + rect.y1) / 2) > max(6, rect.height):
            continue
        left = "".join(c for c, r in l["chars"] if r.x1 <= rect.x0 + 1 and r.x0 >= after_x)
        if left.strip() and rect.x0 - max(r.x1 for c, r in l["chars"] if r.x1 <= rect.x0 + 1) < max_gap:
            seg = re.split(r"_{3,}", left)[-1]
            if seg.strip():
                best = seg
    return _clean_label(best or "")

def _line_above(lines, rect, max_gap=16):
    cands = [l for l in lines if 0 <= rect.y0 - l["rect"].y1 <= max_gap and l["rect"].x0 < rect.x1 and l["rect"].x1 > rect.x0]
    return max(cands, key=lambda l: l["rect"].y1) if cands else None

def _text_above(lines, rect, max_gap=16):
    l = _line_above(lines, rect, max_gap)
    return _clean_label(l["text"]) if l else ""

def _plain_caption(line):
    """A short caption that can label the line below it (not a sentence, not another blank, not checkboxes)."""
    t = line["text"].strip()
    return bool(t) and "_" not in t and not any(g in t for g in BOX_GLYPHS) and len(t) <= 45 and not t.endswith(".")

def _written_on(lines, rect):
    """Is there already text sitting on this line/box (then it isn't blank)?"""
    for l in lines:
        for c, r in l["chars"]:
            if c.strip() and c != "_" and r.intersects(rect) and r.y1 <= rect.y1 + 2 and r.y0 >= rect.y0 - 14:
                return True
    return False

def find_blanks(raw, words=None):
    doc = pymupdf.open(stream=raw, filetype="pdf")
    out, carry = [], ""
    for pno, page in enumerate(doc):
        lines = _lines_from_words(words[pno]) if words is not None else _lines(page)
        taken = []
        ocr = words is not None
        if ocr:   # on a scan: headings end with ":" and have no blank line on their row
            rows = [r for r in _image_lines(page)]
            def blank_on_row(l):
                my = (l["rect"].y0 + l["rect"].y1) / 2
                return any(abs((r.y1 - 6) - my) < 8 and r.x0 > l["rect"].x0 - 5 for r in rows)
            heads = [(l["rect"].y1, _clean_label(l["text"])) for l in lines
                     if l["text"].strip().endswith(":") and len(l["text"].strip()) <= 50 and not blank_on_row(l)]
            hs = sorted(l["rect"].height for l in lines) or [10]
            med = hs[len(hs) // 2]
            def big_row(r):
                my = r.y1 - 6
                return any(l["rect"].height > 1.5 * med and l["rect"].y0 - 2 <= my <= l["rect"].y1 + 2 for l in lines)
        else:
            heads = [(l["rect"].y1, _clean_label(l["text"])) for l in lines if _is_heading(l)]
        def section_at(y, heads=heads, carry=carry):
            prev = [h for hy, h in heads if hy <= y + 1]
            return prev[-1] if prev else carry         # a section continues onto the next page
        for l in lines:
            text = l["text"]
            # 1. underscore runs
            for m in UNDERSCORES.finditer(text):
                rs = [r for _, r in l["chars"][m.start():m.end()]]
                rect = pymupdf.Rect(rs[0].x0, rs[0].y0, rs[-1].x1, rs[-1].y1)
                before = re.split(r"_{3,}", text[:m.start()])[-1]
                label = _clean_label(before) or _text_above(lines, rect, 24)
                if not label:
                    continue
                taken.append(rect)
                out.append({"label": label, "section": section_at(rect.y0),
                            "loc": {"type": "flat", "page": pno, "rect": [round(v, 2) for v in rect]}})
            # "□ Option" groups -> one choice
            if any(g in text for g in BOX_GLYPHS):
                opts = []
                for i, (c, r) in enumerate(l["chars"]):
                    if c in BOX_GLYPHS:
                        rest = text[i + 1:]
                        name = re.split(r"\s{3,}|[" + BOX_GLYPHS + "]", rest.strip())[0].strip()
                        if name:
                            opts.append({"text": name, "rect": [round(v, 2) for v in r]})
                if opts:
                    before = text[:text.index(next(g for g in text if g in BOX_GLYPHS))]
                    label = _clean_label(before) or _text_left_of(lines, pymupdf.Rect(opts[0]["rect"]))
                    grp = next((b for b in out if b["loc"]["type"] == "flat_choice" and b["loc"]["page"] == pno
                                and abs(b["loc"]["options"][-1]["rect"][0] - opts[0]["rect"][0]) < 8
                                and 0 < opts[0]["rect"][1] - b["loc"]["options"][-1]["rect"][3] < 30), None)
                    if grp and not _clean_label(before):
                        grp["loc"]["options"] += opts          # a vertical list of options continues the group
                    elif label:
                        out.append({"label": label, "section": section_at(l["rect"].y0),
                                    "loc": {"type": "flat_choice", "page": pno, "options": opts}})
        # 2 + 3. drawn lines and boxes (vector drawings; on scans, lines found in the page image)
        for rect in sorted(rows if ocr else _vector_lines(page), key=lambda r: (round(r.y1 / 4), r.x0)):
                    if any(rect.intersects(t) for t in taken) or _written_on(lines, rect) or rect.width > page.rect.width * 0.9:
                        continue
                    prev = [t.x1 for t in taken if abs(t.y1 - rect.y1) < 4 and t.x1 <= rect.x0 + 1]
                    if ocr and big_row(rect):
                        continue                # a title's thick letters, not a blank
                    label = _text_left_of(lines, rect, after_x=max(prev) if prev else -1)
                    if not label:
                        above = _line_above(lines, rect)
                        if not above or not _plain_caption(above) or (ocr and blank_on_row(above)):
                            continue            # a rule under a row of text, not a blank
                        label = _clean_label(above["text"])
                    if not label:
                        continue
                    taken.append(rect)
                    out.append({"label": label, "section": section_at(rect.y0),
                                "loc": {"type": "flat", "page": pno, "rect": [round(v, 2) for v in rect]}})
        carry = heads[-1][1] if heads else carry
    # checkbox options stacked in a column belong to one question even when other text sits between them
    merged = []
    for b in out:
        if b["loc"]["type"] == "flat_choice":
            m = next((g for g in merged if g["loc"]["type"] == "flat_choice" and g["loc"]["page"] == b["loc"]["page"]
                      and g["label"] == b["label"] and min(abs(o["rect"][0] - b["loc"]["options"][0]["rect"][0]) for o in g["loc"]["options"]) < 8
                      and abs(g["loc"]["options"][-1]["rect"][1] - b["loc"]["options"][0]["rect"][1]) < 80), None)
            if m:
                m["loc"]["options"] = sorted(m["loc"]["options"] + b["loc"]["options"], key=lambda o: o["rect"][1]); continue
        merged.append(b)
    return merged

def _vector_lines(page):
    for d in page.get_drawings():
        for it in d["items"]:
            if it[0] == "l":
                p1, p2 = it[1], it[2]
                if abs(p1.y - p2.y) <= 1 and abs(p2.x - p1.x) >= MIN_LINE:
                    yield pymupdf.Rect(min(p1.x, p2.x), p1.y - 12, max(p1.x, p2.x), p1.y)
            elif it[0] == "re":
                r = it[1]
                if r.height < 2 and r.width >= MIN_LINE:              # a thin rectangle drawn as a line
                    yield pymupdf.Rect(r.x0, r.y0 - 12, r.x1, r.y0)
                elif 10 <= r.height <= 40 and r.width >= MIN_BOX_W:   # an empty box
                    yield pymupdf.Rect(r)

def _image_lines(page, dpi=100):
    """Horizontal lines in a scanned page's picture: long thin runs of dark pixels (underscores print as these)."""
    import numpy as np
    pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.stride)[:, :pix.width]
    dark = img < 140
    k, minpx = 72.0 / dpi, int(MIN_LINE * dpi / 72)
    segs = []                                   # (y, x0, x1) per pixel row
    for y in range(dark.shape[0]):
        row = dark[y]
        if row.sum() < minpx * 0.6:
            continue
        d = np.diff(np.concatenate(([0], row.astype(np.int8), [0])))
        runs = []
        for x0, x1 in zip(np.where(d == 1)[0], np.where(d == -1)[0]):
            if runs and x0 - runs[-1][1] <= 3:        # underscores print with hairline gaps between them
                runs[-1][1] = x1
            else:
                runs.append([x0, x1])
        segs += [(y, x0, x1) for x0, x1 in runs if x1 - x0 >= minpx]
    lines = []                                  # merge the same line across adjacent rows
    for y, x0, x1 in segs:
        m = next((l for l in lines if y - l[1] <= 2 and min(x1, l[3]) - max(x0, l[2]) > 0.8 * (x1 - x0)), None)
        if m:
            m[1] = y; m[2] = min(m[2], x0); m[3] = max(m[3], x1)
        else:
            lines.append([y, y, x0, x1])
    for y0, y1, x0, x1 in lines:
        if y1 - y0 <= 4:                        # thin: a line, not a filled bar or a box edge run
            yield pymupdf.Rect(x0 * k, y0 * k - 12, x1 * k, y0 * k)

def _fit(text, width, height):
    size = min(10.0, max(6.0, height * 0.85))
    while size > 5 and pymupdf.get_text_length(text, "helv", size) > width - 4:
        size -= 0.5
    return size

def words_in(page, rect):
    """The words whose centre lies inside rect (underscores dropped): what a reader sees written in that blank."""
    r = pymupdf.Rect(rect)
    out = [w[4] for w in page.get_text("words", sort=True)
           if r.x0 - 2 <= (w[0] + w[2]) / 2 <= r.x1 + 2 and r.y0 - 3 <= (w[1] + w[3]) / 2 <= r.y1 + 2]
    return " ".join(x for x in (w.replace("_", "") for w in out) if x)

def _norm(s):
    return re.sub(r"[^a-z0-9@]", "", (s or "").lower())

def fill_flat(raw, ops):
    doc = pymupdf.open(stream=raw, filetype="pdf")
    results, placed = [], []
    for op in ops:
        loc, val = op["locator"], str(op["value"])
        page = doc[loc["page"]]
        if loc["type"] == "flat_choice":
            v = _norm(val)
            pick = next((o for o in loc["options"] if _norm(o["text"]) and (_norm(o["text"]) in v or v in _norm(o["text"]))), None)
            if not pick:
                results.append({"locator": loc, "status": "failed", "why": "no option matches"}); continue
            r = pymupdf.Rect(pick["rect"])
            page.insert_text((r.x0 + r.width * 0.15, r.y1 - r.height * 0.15), "X", fontsize=max(6, r.height * 0.9), fontname="helv")
            results.append({"locator": loc, "status": "ok", "choice": pick["text"]}); continue
        r = pymupdf.Rect(loc["rect"])
        size = _fit(val, r.width, r.height)
        page.insert_text((r.x0 + 2, r.y1 - max(1.5, r.height * 0.18)), val, fontsize=size, fontname="helv", color=(0, 0, 0.35))
        placed.append((op, r))
    out = doc.tobytes(garbage=3, deflate=True)
    check = pymupdf.open(stream=out, filetype="pdf")
    for op, r in placed:     # read each value back from where it was written
        got = words_in(check[op["locator"]["page"]], r)
        ok = _norm(str(op["value"])) in _norm(got)
        results.append({"locator": op["locator"], "status": "ok" if ok else "failed", "why": "" if ok else "not readable where written"})
    return out, results
