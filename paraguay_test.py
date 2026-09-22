# paraguay_test.py  —  standalone Paraguay tester (does NOT touch app.py)
# run:  py -m streamlit run paraguay_test.py

import streamlit as st
import fitz, re, os, uuid, tempfile
import pandas as pd
from datetime import datetime
from collections import Counter

st.set_page_config(page_title="Paraguay Test", page_icon="🇵🇾", layout="wide")
st.title("🇵🇾 Paraguay AD-2 Parser — TEST BENCH")

MASTER_URL = "https://raw.githubusercontent.com/DixitCAE/PDF_PARSER/main/master_airport_list.csv"


@st.cache_data(show_spinner=False)
def load_master():
    df = pd.read_csv(MASTER_URL, header=None)
    return set(df[0].dropna().astype(str).str.strip().str.upper())


# ---------- helpers (self-contained copies) ----------
def normalize_text(t):
    return re.sub(r"[\s\.\-\/\:\,\(\)\[\]_]+", "", str(t).upper())


def compact_spaces(t):
    t = str(t).upper()
    t = re.sub(r"[\u00AD\u2010\u2011\u2012\u2013\u2014\u2015\u2212]", "-", t)
    return re.sub(r"\s+", " ", t).strip()


def normalize_for_admin(t):
    t = str(t).upper()
    for a, b in {"’": "'", "´": "'", "Á": "A", "É": "E", "Í": "I",
                 "Ó": "O", "Ú": "U", "Ñ": "N", "Ü": "U"}.items():
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t).strip()


def build_normal_date_patterns(sd):
    dt = datetime.strptime(sd, "%d %b %Y")
    months = [dt.strftime("%b").upper()]
    if months[0] == "SEP":
        months.append("SEPT")
    days = [str(dt.day), f"{dt.day:02}"]
    years = [str(dt.year), str(dt.year)[-2:]]
    return [f"{d}{m}{y}" for d in days for m in months for y in years]


def match_date(text, sd):
    tc = normalize_text(text)
    return any(p in tc for p in build_normal_date_patterns(sd))


def get_zone_lines(page, top=150, bottom=120):
    lines, H = [], page.rect.height
    try:
        blocks = page.get_text("blocks")
    except Exception:
        return []
    for b in blocks:
        x0, y0, x1, y1, txt = b[:5]
        if not (y0 < top or y1 > H - bottom):
            continue
        for off, raw in enumerate(str(txt).splitlines()):
            lt = compact_spaces(raw)
            if lt:
                lines.append((y0 + off * 0.01, x0, lt))
    lines.sort(key=lambda z: (z[0], z[1]))
    return [t for _, _, t in lines]


def is_auto_removed(section, major):
    if section == "GEN" and major in {1, 2, 3, 4, 5}:
        return True
    if section == "ENR" and major in {2, 5, 6}:
        return True
    return False


# ---------- Paraguay logic ----------
PY_ICAO_RE = re.compile(r"\b(SG[A-Z]{2})\b")
PY_ID_RE = re.compile(r"\b(GEN|ENR|AD)\s*(\d+)\s*\.\s*(\d+)\s*-\s*[\d.]+", re.I)
PY_NAME_RE = re.compile(r"\b([A-ZÑÜ]{4,})\s*/\s*[“\"']?[A-ZÑÜ]")


def py_identity(page, text):
    head_lines = [compact_spaces(l) for l in str(text).splitlines()[:6]]
    for line in get_zone_lines(page) + head_lines:
        m = PY_ID_RE.search(line)
        if m:
            return m.group(1).upper(), int(m.group(2)), int(m.group(3)), m.group(0)
    return None, None, None, None


def py_icao(text):
    m = PY_ICAO_RE.search(str(text).upper())
    return m.group(1) if m else None


def py_names(text):
    return {m.group(1).upper() for m in PY_NAME_RE.finditer(normalize_for_admin(text))}


def process_paraguay(pdf_path, selected_date):
    doc = fitz.open(pdf_path)
    master = load_master()

    # ---- PASS 1: identity + learn AD2.N -> ICAO and NAME -> ICAO ----
    scanned, group_map, name_map = [], {}, {}
    last = {"s": None, "mj": None, "sub": None, "d": False}

    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text()
        date_text = text + "\n" + "\n".join(get_zone_lines(page))
        s, mj, sub, raw = py_identity(page, text)
        icao = py_icao(text)
        names = py_names(text)
        d_ok = match_date(date_text, selected_date)

        inherited = False
        if s is None and len(text.strip()) < 30:      # image-only chart page
            s, mj, sub, d_ok = last["s"], last["mj"], last["sub"], last["d"]
            raw, inherited = "(chart - inherited)", True

        if s == "AD" and mj == 2 and sub is not None and icao:
            group_map.setdefault(sub, icao)
            for nm in names:
                name_map.setdefault(nm, icao)

        if s:
            last.update({"s": s, "mj": mj, "sub": sub, "d": d_ok})

        scanned.append(dict(idx=i, s=s, mj=mj, sub=sub, raw=raw, icao=icao,
                            names=names, d=d_ok, inh=inherited))

    # ---- PASS 2: resolve + filter ----
    keep, removed, rows = [], [], []
    detected, kept_ic, dropped_ic = set(), set(), set()

    for r in scanned:
        s, mj, sub = r["s"], r["mj"], r["sub"]
        icao, how = None, ""

        if s == "AD" and mj == 2:
            if r["icao"]:
                icao, how = r["icao"], "page-ICAO"
            elif group_map.get(sub):
                icao, how = group_map[sub], f"AD2.{sub}-group"
            else:
                for nm in r["names"]:
                    if nm in name_map:
                        icao, how = name_map[nm], f"name:{nm}"
                        break
            if icao:
                detected.add(icao)

        status = "KEPT"
        if not s:
            status = "DROP (no section)"
        elif is_auto_removed(s, mj):
            status = f"DROP (auto-remove {s} {mj})"
        elif not r["d"]:
            status = "DROP (date mismatch)"
        elif s == "AD" and mj == 2 and icao:
            if icao in master:
                kept_ic.add(icao)
            else:
                dropped_ic.add(icao)
                status = f"DROP (not in master: {icao})"

        (keep if status == "KEPT" else removed).append(r["idx"])
        rows.append({"page": r["idx"] + 1, "section": s, "major": mj, "sub": sub,
                     "id": r["raw"], "icao": icao or "", "resolved_by": how,
                     "chart": "yes" if r["inh"] else "", "status": status})

    doc.close()
    return keep, removed, rows, group_map, name_map, detected, kept_ic, dropped_ic


# ---------- UI ----------
f = st.file_uploader("Upload Paraguay AMDT PDF", type=["pdf"])
d = st.date_input("Effective Date")

if f and st.button("🚀 Test Paraguay"):
    p = os.path.join(tempfile.gettempdir(), f"py_{uuid.uuid4().hex}.pdf")
    with open(p, "wb") as fh:
        fh.write(f.read())

    with st.spinner("Parsing…"):
        keep, rem, rows, gmap, nmap, det, kic, dic = process_paraguay(
            p, d.strftime("%d %b %Y"))

    c1, c2, c3 = st.columns(3)
    c1.metric("Total pages", len(rows))
    c2.metric("Kept", len(keep))
    c3.metric("Removed", len(rem))

    st.subheader("🔑 AD 2.N → ICAO map (the key check)")
    st.write(dict(sorted(gmap.items())) or "— none found —")
    st.caption("Every AD 2.N group present in the PDF should have an ICAO here.")

    st.subheader("🏷️ Name → ICAO learned from the document")
    st.write(nmap or "— none —")

    st.subheader("📋 Airports")
    st.write("Detected:", ", ".join(sorted(det)) or "—")
    st.write("Kept (in master):", ", ".join(sorted(kic)) or "—")
    st.write("Dropped (not in master):", ", ".join(sorted(dic)) or "—")

    st.subheader("🧾 Page-by-page")
    df = pd.DataFrame(rows)
    only_ad2 = st.checkbox("Show only AD 2 pages", value=True)
    view = df[(df.section == "AD") & (df.major == 2)] if only_ad2 else df
    st.dataframe(view, use_container_width=True, height=460)

    st.subheader("🗑️ Removed breakdown")
    st.write(dict(Counter(r["status"] for r in rows if r["status"] != "KEPT")))

    # build trimmed PDF
    src = fitz.open(p)
    out = fitz.open()
    for i in keep:
        out.insert_pdf(src, from_page=i, to_page=i)
    if out.page_count:
        op = os.path.join(tempfile.gettempdir(), f"py_out_{uuid.uuid4().hex}.pdf")
        out.save(op, garbage=4, deflate=True)
        with open(op, "rb") as fh:
            st.download_button("⬇ Download trimmed Paraguay PDF", fh,
                               file_name="Paraguay_trimmed.pdf",
                               mime="application/pdf")
    out.close()
    src.close()