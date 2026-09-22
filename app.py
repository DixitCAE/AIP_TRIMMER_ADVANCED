import streamlit as st
import fitz
import re
import pandas as pd
from datetime import datetime
from collections import Counter
import tempfile
import uuid
import os

import os
import sys

if sys.platform.startswith("win"):
    # Local Windows machine
    os.environ["TESSDATA_PREFIX"] = r"C:\Users\divyn\AppData\Local\Tesseract-OCR\tessdata"
    os.environ["PATH"] = r"C:\Users\divyn\AppData\Local\Tesseract-OCR" + os.pathsep + os.environ["PATH"]
else:
    # Linux server (Streamlit Cloud). packages.txt installs tesseract-ocr.
    for _p in (
        "/usr/share/tesseract-ocr/5/tessdata",
        "/usr/share/tesseract-ocr/4.00/tessdata",
        "/usr/share/tesseract-ocr/tessdata",
        "/usr/share/tessdata",
    ):
        if os.path.isdir(_p):
            os.environ["TESSDATA_PREFIX"] = _p
            break

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(
    page_title="AIP Trimmer",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================
# MODERN UI CSS
# =============================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stHeader"] { background: transparent; }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(1100px 600px at 8% -10%, rgba(79,140,255,.18), transparent 60%),
            radial-gradient(900px 520px at 105% 2%, rgba(168,85,247,.15), transparent 55%),
            linear-gradient(180deg, #070B16 0%, #0B1020 45%, #080C1A 100%);
    }
    .block-container { padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1560px; }

    /* ---------- HERO ---------- */
    .hero {
        display:flex; align-items:center; gap:18px; flex-wrap:wrap;
        background: linear-gradient(135deg, rgba(79,140,255,.16), rgba(168,85,247,.10));
        border:1px solid rgba(255,255,255,.09); border-radius:22px;
        padding:22px 26px; margin-bottom:22px;
        box-shadow:0 18px 50px rgba(0,0,0,.45); backdrop-filter: blur(14px);
    }
    .hero-badge {
        width:56px; height:56px; border-radius:16px; font-size:28px;
        display:flex; align-items:center; justify-content:center;
        background: linear-gradient(135deg,#4F8CFF,#8B5CF6);
        box-shadow:0 10px 26px rgba(79,140,255,.45);
    }
    .hero h1 { margin:0; font-size:30px; font-weight:800; letter-spacing:-.5px; color:#F4F7FF; }
    .hero p  { margin:4px 0 0 0; font-size:14px; color:#93A3C4; }
    .hero-chip {
        margin-left:auto; font-size:11.5px; font-weight:700; color:#A8C2FF;
        padding:9px 16px; border-radius:999px; letter-spacing:.5px;
        background:rgba(79,140,255,.14); border:1px solid rgba(79,140,255,.32);
    }

    /* ---------- SECTION LABELS ---------- */
    .sec-label {
        display:flex; align-items:center; gap:9px;
        font-size:11.5px; font-weight:700; letter-spacing:1.35px;
        text-transform:uppercase; color:#7F92B8; margin:22px 0 10px 0;
    }
    .sec-label::after { content:""; flex:1; height:1px; background:rgba(255,255,255,.10); }
    .sec-num {
        display:inline-flex; align-items:center; justify-content:center;
        width:17px; height:17px; border-radius:50%; font-size:10px;
        border:1px solid #7F92B8; color:#7F92B8;
    }

    /* ---------- KPI CARDS ---------- */
    .kpi-card {
        position:relative; overflow:hidden;
        background: linear-gradient(160deg, rgba(255,255,255,.06), rgba(255,255,255,.015));
        border:1px solid rgba(255,255,255,.10); border-radius:20px;
        padding:16px 20px 16px 20px; box-shadow:0 14px 34px rgba(0,0,0,.38);
        transition: transform .18s ease, border-color .18s ease;
    }
    .kpi-card:hover { transform:translateY(-3px); border-color:rgba(255,255,255,.20); }
    .kpi-card::before { content:""; position:absolute; top:0; left:0; height:4px; width:100%; }
    .kpi-blue::before  { background:linear-gradient(90deg,#4F8CFF,#7DD3FC); }
    .kpi-green::before { background:linear-gradient(90deg,#22C55E,#86EFAC); }
    .kpi-amber::before { background:linear-gradient(90deg,#F59E0B,#FCD34D); }
    .kpi-top { display:flex; align-items:center; gap:9px; margin-top:6px; }
    .kpi-icon{ font-size:16px; }
    .kpi-label{ font-size:11.5px; font-weight:700; letter-spacing:.7px; color:#93A3C4; text-transform:uppercase; }
    .kpi-value{ font-size:42px; font-weight:800; color:#F4F7FF; line-height:1.05; margin:8px 0 14px 0; }
    .kpi-bar { height:7px; width:100%; border-radius:99px; background:rgba(255,255,255,.10); overflow:hidden; }
    .kpi-bar span { display:block; height:100%; border-radius:99px; }
    .kpi-blue  .kpi-bar span { background:linear-gradient(90deg,#4F8CFF,#7DD3FC); }
    .kpi-green .kpi-bar span { background:linear-gradient(90deg,#22C55E,#86EFAC); }
    .kpi-amber .kpi-bar span { background:linear-gradient(90deg,#F59E0B,#FCD34D); }
    .kpi-sub { font-size:11px; color:#6F819F; margin-top:9px; }

    /* ---------- PAGE CARD (preview grid) ---------- */
    .pg-head {
        display:flex; align-items:center; gap:9px;
        margin:-1rem -1rem .75rem -1rem; padding:9px 12px;
        border-radius:11px 11px 0 0;
    }
    .pg-pill {
        font-size:10.5px; font-weight:800; color:#F4F7FF;
        background:rgba(255,255,255,.16); padding:3px 9px; border-radius:8px;
    }
    .pg-code { font-size:11px; font-weight:700; letter-spacing:.3px; }

    .chip-row { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
    .chip {
        display:inline-flex; align-items:center; gap:7px;
        font-size:11px; font-weight:700; padding:6px 13px; border-radius:999px;
    }
    .chip i { width:7px; height:7px; border-radius:50%; display:inline-block; }
    .count-chip {
        font-size:11.5px; color:#93A3C4; padding:7px 15px; border-radius:999px;
        background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.14);
    }
    .count-chip b { color:#F4F7FF; font-size:12.5px; }

    /* ---------- INPUTS ---------- */
    [data-baseweb="select"] > div, [data-testid="stDateInput"] input, [data-testid="stTextInput"] input {
        background:rgba(255,255,255,.06) !important;
        border:1px solid rgba(255,255,255,.13) !important;
        border-radius:12px !important; color:#E6EBF5 !important;
    }
    [data-baseweb="select"] > div:hover { border-color:rgba(79,140,255,.55) !important; }
    [data-testid="stFileUploaderDropzone"] {
        background:rgba(79,140,255,.08);
        border:1.5px dashed rgba(79,140,255,.42);
        border-radius:16px; padding:18px; transition:all .2s ease;
    }
    [data-testid="stFileUploaderDropzone"\]:hover {
        background:rgba(79,140,255,.13); border-color:rgba(79,140,255,.72);
    }
    label, [data-testid="stWidgetLabel"] p {
        font-size:12.5px !important; font-weight:600 !important;
        color:#9AACCB !important; letter-spacing:.3px;
    }

    /* ---------- BUTTONS ---------- */
    .stButton > button, .stDownloadButton > button {
        border-radius:12px; font-weight:600; font-size:14px; padding:9px 20px;
        border:1px solid rgba(255,255,255,.13);
        background:rgba(255,255,255,.06); color:#E6EBF5; transition:all .18s ease;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        transform:translateY(-2px); border-color:rgba(79,140,255,.6);
        background:rgba(79,140,255,.14); color:#fff;
    }
    .stButton > button[kind="primary"] {
        background:linear-gradient(135deg,#4F8CFF,#7C5CFF); border:none; color:#fff;
        box-shadow:0 10px 26px rgba(79,140,255,.40);
    }
    .stDownloadButton > button {
        background:linear-gradient(135deg,#16A34A,#22C55E); border:none; color:#fff;
        box-shadow:0 8px 22px rgba(34,197,94,.32);
    }

    /* ---------- MISC ---------- */
    [data-testid="stCheckbox"] label, [data-testid="stToggle"] label {
        font-size:13.5px !important; color:#D6E0F5 !important;
    }
    [data-testid="stExpander"] {
        border:1px solid rgba(255,255,255,.10) !important;
        border-radius:14px !important; background:rgba(255,255,255,.035) !important;
    }
    [data-testid="stAlert"] { border-radius:14px; border:1px solid rgba(255,255,255,.10); }
    [data-testid="stImage"] img {
        border-radius:7px; border:1px solid rgba(0,0,0,.35);
        box-shadow:0 6px 18px rgba(0,0,0,.35);
    }
    ::-webkit-scrollbar { width:10px; height:10px; }
    ::-webkit-scrollbar-track { background:transparent; }
    ::-webkit-scrollbar-thumb { background:rgba(255,255,255,.14); border-radius:99px; }
    ::-webkit-scrollbar-thumb:hover { background:rgba(79,140,255,.5); }

    .enr-subsection-title {
        font-size:10.5px; color:#6F819F; font-weight:700; letter-spacing:1.15px;
        text-transform:uppercase; margin:6px 0 2px 34px;
    }
        .src-note {
        font-size:13px; color:#A9B8D4; line-height:1.65;
        padding:2px 0 10px 0;
    }
    .src-note b { color:#DCE6FA; }
    .icao-chip {
        font-size:11px; font-weight:700; letter-spacing:.3px;
        padding:5px 11px; border-radius:999px; font-family:ui-monospace,monospace;
    }
    .amdt-tag {
        display:inline-block; font-size:11.5px; font-weight:700;
        color:#A8C2FF; background:rgba(79,140,255,.14);
        border:1px solid rgba(79,140,255,.32);
        padding:6px 14px; border-radius:999px; margin-bottom:4px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =============================
# MASTER CSV
# =============================
MASTER_URL = "https://raw.githubusercontent.com/DixitCAE/PDF_PARSER/main/master_airport_list.csv"


@st.cache_data(show_spinner=False)
def load_master():
    df = pd.read_csv(MASTER_URL, header=None)
    return set(
        df[0]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
    )


# =============================
# COUNTRY / PARSER PROFILE LIST
# =============================
COUNTRY_OPTIONS = ["Universal"] + sorted(
    [
        "Portugal",
        "China",
        "Brazil",
        "Malaysia",
        "Indonesia",
        "ASECNA",
        "COCESNA",
        "Chile",
        "Greece",
        "Australia (ERSA)",
        "Russia",
        "Argentina",
        "Paraguay",
    ],
    key=str.lower
)


GROUP_PROFILES = {"ASECNA", "COCESNA"}


# =============================
# FILE HELPERS
# =============================
def safe_remove_file(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def cleanup_existing_pdf_files():
    for key in ["input_pdf_path", "output_pdf_path"]:
        path = st.session_state.get(key)
        safe_remove_file(path)


def make_temp_pdf_path(prefix):
    file_id = uuid.uuid4().hex
    return os.path.join(tempfile.gettempdir(), f"{prefix}_{file_id}.pdf")


def save_uploaded_pdf_to_disk(uploaded_file):
    input_path = make_temp_pdf_path("aip_input")

    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    return input_path


def get_file_size_mb(path):
    try:
        if path and os.path.exists(path):
            return os.path.getsize(path) / (1024 * 1024)
    except Exception:
        return 0

    return 0


def get_file_mtime(path):
    try:
        if path and os.path.exists(path):
            return os.path.getmtime(path)
    except Exception:
        return 0

    return 0


# =============================
# TEXT HELPERS
# =============================
def normalize_text(text):
    return re.sub(r"[\s\.\-\/\:\,\(\)\[\]_]+", "", str(text).upper())


def compact_spaces(text):
    text = str(text).upper()
    # Colombia (and some others) use the soft hyphen U+00AD between
    # "AD 2 SKxx" and the page number instead of a real "-". It is NOT
    # whitespace, so it survived and broke every AD/GEN/ENR hyphen regex.
    # Normalize all unicode dash/hyphen variants to a plain ASCII hyphen.
    text = re.sub(r"[\u00AD\u2010\u2011\u2012\u2013\u2014\u2015\u2212]", "-", text)
    # COCESNA eAIP embeds layout markers in the page text, so the running
    # # footer reads "AD-2.MSLP~~~END~~~-10" instead of "AD-2.MSLP-10".
    # Strip ~~~LEFT~~~ / ~~~RIGHT~~~ / ~~~END~~~ / ~~~eaip-amdt~~~ so the
    # page-id parses normally. Harmless for every other country.
    text = re.sub(r"~~~[A-Z0-9\-]{0,20}?~~~", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_for_admin(text):
    """
    Admin/list-page normalization.

    Important:
    - Keeps enough readable text for phrase matching.
    - Normalizes common French accents used in ASECNA docs.
    - Does not remove all separators because phrase matching needs spaces.
    """
    text = str(text).upper()
    replacements = {
        "’": "'",
        "´": "'",
        "À": "A",
        "Á": "A",
        "Â": "A",
        "Ä": "A",
        "É": "E",
        "È": "E",
        "Ê": "E",
        "Ë": "E",
        "Î": "I",
        "Ï": "I",
        "Ô": "O",
        "Ö": "O",
        "Ù": "U",
        "Û": "U",
        "Ü": "U",
        "Ç": "C"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_normal_date_patterns(selected_date):
    dt = datetime.strptime(selected_date, "%d %b %Y")

    month = dt.strftime("%b").upper()   # e.g. "SEP"

    # Brazil (DECEA) and a few others abbreviate September as "SEPT"
    # (4 letters) instead of the ICAO-standard "SEP". Include both so the
    # date still matches. Purely additive — only affects September.
    months = [month]
    if month == "SEP":
        months.append("SEPT")

    days = [str(dt.day), f"{dt.day:02}"]
    years = [str(dt.year), str(dt.year)[-2:]]

    return [
        f"{day}{m}{year}"
        for day in days
        for m in months
        for year in years
    ]


# =============================
# COUNTRY DATE PARSERS
# =============================
def match_date_standard(text, selected_date):
    """
    Standard effective-date matcher.

    Supported examples:
        05-AUG-2026
        05 AUG 2026
        05AUG2026
        05AUG26
        5AUG2026
        5AUG26
    """
    text_clean = normalize_text(text)
    patterns = build_normal_date_patterns(selected_date)
    return any(pattern in text_clean for pattern in patterns)


def match_date_china(text, selected_date):
    """
    China supports normal formats plus numeric EFF timestamp formats.

    China examples:
        EFF2608051600
        2608051600
        EFF202608051600
        202608051600

    The observed China timestamp time is fixed as 1600.
    """
    text_clean = normalize_text(text)

    dt = datetime.strptime(selected_date, "%d %b %Y")

    normal_patterns = build_normal_date_patterns(selected_date)

    china_yymmdd_time = dt.strftime("%y%m%d") + "1600"
    china_yyyymmdd_time = dt.strftime("%Y%m%d") + "1600"

    china_patterns = [
        china_yymmdd_time,
        f"EFF{china_yymmdd_time}",
        china_yyyymmdd_time,
        f"EFF{china_yyyymmdd_time}"
    ]

    patterns = normal_patterns + china_patterns

    return any(pattern in text_clean for pattern in patterns)


def match_date_for_country(text, selected_date, country):
    if country == "China":
        return match_date_china(text, selected_date)

    return match_date_standard(text, selected_date)

# =============================
# SPANISH DATE MATCHER (Argentina)
# =============================
SPANISH_MONTHS = {
    1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL",
    5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO",
    9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE",
}

def build_spanish_date_patterns(selected_date):
    dt = datetime.strptime(selected_date, "%d %b %Y")
    month = SPANISH_MONTHS[dt.month]                 # e.g. "JUNIO"
    days = [str(dt.day), f"{dt.day:02}"]             # "11" and "11"; "1" and "01"
    years = [str(dt.year), str(dt.year)[-2:]]        # "2026" and "26"
    return [f"{d}{month}{y}" for d in days for y in years]

def match_date_argentina(text, selected_date):
    """
    Argentina pages print the effective date at the BOTTOM in Spanish
    (e.g. '11 JUNIO 2026'). Verified against the merged AIP: every page has a
    footer date, and matching Spanish month names cleanly separates the 11
    distinct effective dates with zero false positives. English/ICAO forms are
    included as a fallback.
    """
    tc = normalize_text(text)   # "…11JUNIO2026…"
    pats = build_spanish_date_patterns(selected_date) + build_normal_date_patterns(selected_date)
    return any(p in tc for p in pats)

# =============================
# HEADER / FOOTER EXTRACTION
# =============================
def get_zone_lines(page, top_limit=150, bottom_limit=120):
    """
    Fast header/footer text extraction using blocks.

    Reads left, center, and right side.
    Uses vertical position only.
    Preserves approximate line order by y-position and x-position.
    """
    lines = []
    page_height = page.rect.height

    try:
        blocks = page.get_text("blocks")
    except Exception:
        return []

    for block in blocks:
        x0, y0, x1, y1, text = block[:5]

        if not (y0 < top_limit or y1 > page_height - bottom_limit):
            continue

        raw_lines = str(text).splitlines()

        for offset, raw_line in enumerate(raw_lines):
            line_text = compact_spaces(raw_line)

            if line_text:
                lines.append((y0 + offset * 0.01, x0, line_text))

    lines.sort(key=lambda item: (item[0], item[1]))

    return [line_text for _, _, line_text in lines]


# =============================
# ADMIN / LIST PAGE DETECTION
# =============================
def is_administrative_list_page(text, country):
    """
    Detects amendment cover/checklist/list pages that contain many AD references
    but are not actual airport AD content pages.

    Permanent rule:
    - Do not mark a page as admin only because it contains authority name,
      AIP name, or AMDT number.
    - ASECNA normal content pages contain AIP ASECNA / AMDT labels on many pages.
    - Only strong list/checklist/page-management wording should trigger admin.
    """
    t = normalize_for_admin(text)

    base_markers = [
        "DESTROY INSERT",
        "INSERT/DESTROY",
        "PAGE TO BE DESTROYED",
        "PAGE TO BE INSERTED",
        "CHECKLIST OF AIP PAGES",
        "CHECKLIST MIA",
        "LISTE DE CONTROLE",
        "LISTE DE CONTRÔLE",
        "LIST OF AERONAUTICAL CHARTS",
        "THIS AIRAC AIP AMDT",
        "CONTAINS:",
        "TO BE INSERTED",
        "TO BE DESTROYED",
        "PAGE A SUPPRIMER",
        "PAGE A INSERER",
        "PAGE TO BE REMOVED",
        "BULLETIN DE MISE A JOUR",
        "BULLETIN DE MISE À JOUR",
        "CHANGEMENTS DANS CET AMENDEMENT",
        "CHANGES IN THIS AMENDMENT"
    ]

    indonesia_markers = [
        "AD 0.4 CHECKLIST OF AIP PAGES",
        "THE FOLLOWING PAGES THAT ARE AFFECTED BY THIS AMENDMENT"
    ]

    malaysia_markers = [
        "PART 3 - AERODROMES",
        "DESTROY INSERT"
    ]

    asecna_strong_markers = [
        "DATE PAGE A SUPPRIMER DATE PAGE A INSERER",
        "PAGE A SUPPRIMER DATE PAGE A INSERER",
        "PAGE TO BE REMOVED PAGE TO BE INSERTED",
        "BULLETIN DE MISE A JOUR",
        "BULLETIN DE MISE A JOUR UPDATING BULLETIN",
        "CHANGEMENTS DANS CET AMENDEMENT",
        "CHANGES IN THIS AMENDMENT",
        "GEN 0.4 LISTE DE CONTROLE MIA",
        "GEN 0.4 LISTE DE CONTRÔLE MIA",
        "LISTE DE CONTROLE MIA",
        "CHECKLIST MIA"
    ]

    cocesna_strong_markers = [
        "CHECKLIST OF AIP PAGES",
        "PAGE TO BE REMOVED",
        "PAGE TO BE INSERTED",
        "AMENDMENT CHECKLIST"
    ]

    markers = list(base_markers)

    if country in {"Indonesia", "Universal"}:
        markers.extend(indonesia_markers)

    if country in {"Malaysia", "Universal"}:
        markers.extend(malaysia_markers)

    if country in {"ASECNA", "Universal"}:
        markers.extend(asecna_strong_markers)

    if country in {"COCESNA", "Universal"}:
        markers.extend(cocesna_strong_markers)

    return any(marker in t for marker in markers)


def is_group_index_or_checklist_page(page_text, title_lines, country):
    """
    Extra protection for group AIP profiles.

    ASECNA / COCESNA pages can list hundreds of airport AD-2 references inside
    GEN 0.4, AD 0.6, amendment bulletin, or page-management pages.

    These pages must not become airport-specific AD pages.

    This function intentionally looks for strong structural indicators only.
    It does not use authority labels like AIP ASECNA as admin triggers.
    """
    if country not in GROUP_PROFILES:
        return False

    full = normalize_for_admin(page_text)
    title = normalize_for_admin(" ".join(title_lines))

    strong_page_mgmt = [
        "DATE PAGE A SUPPRIMER",
        "PAGE A INSERER",
        "PAGE TO BE REMOVED",
        "PAGE TO BE INSERTED",
        "BULLETIN DE MISE A JOUR",
        "CHANGEMENTS DANS CET AMENDEMENT",
        "CHANGES IN THIS AMENDMENT",
        "CHECKLIST MIA",
        "LISTE DE CONTROLE",
        "LISTE DE CONTRÔLE",
        "CHECKLIST OF AIP PAGES"
    ]

    if any(marker in full for marker in strong_page_mgmt):
        return True

    generic_index_patterns = [
        r"\b00\s*GEN\s*0\.4\b",
        r"\bGEN\s*0\.4\b",
        r"\b00\s*AD\s*0\.6\b",
        r"\bAD\s*0\.6\b",
        r"\b00\s*ENR\s*0\.6\b",
        r"\bENR\s*0\.6\b"
    ]

    if any(re.search(pattern, title) for pattern in generic_index_patterns):
        return True

    return False


# =============================
# GENERIC SECTION DETECTION
# =============================
def match_generic_section_title(line_text):
    """
    Detects generic AIP section title lines:
        GEN 0.4 - 1
        ENR 1.10 - 2
        AD 0.6 - 3
        AD 1.3 - 5
        00-GEN-0.4.1
        07-AD-1.3.1
        05-ENR-1.12.3
    """
    t = compact_spaces(line_text)

    generic_title_patterns = [
        r"\b(?:\d{2}\s*[- ]\s*)?(GEN)\s*[\.\-]?\s*(\d+)(?:\s*[\.\-]\s*\d+)*(?:\s*-\s*\d+)?\b",
        r"\b(?:\d{2}\s*[- ]\s*)?(ENR)\s*[\.\-]?\s*(\d+)(?:\s*[\.\-]\s*\d+)*(?:\s*-\s*\d+)?\b",
        r"\b(?:\d{2}\s*[- ]\s*)?(AD)\s*[\.\-]?\s*(\d+)(?:\s*[\.\-]\s*\d+)*(?:\s*-\s*\d+)?\b",
    ]

    for pattern in generic_title_patterns:
        match = re.search(pattern, t)

        if match:
            return {
                "section": match.group(1),
                "major": int(match.group(2)),
                "raw": match.group(0),
                "icao": None,
                "is_airport_ad": False,
                "parser": "generic"
            }

    return None
    # =============================
# COUNTRY SPECIFIC AD PARSERS
# =============================
def make_ad_detail(match, raw_text, parser_name):
    return {
        "section": "AD",
        "major": 2,
        "raw": raw_text,
        "icao": match.group(1).upper(),
        "is_airport_ad": True,
        "parser": parser_name
    }


def match_ad_portugal(line_text):
    """
    Portugal examples:
        LPFR AD 2 - 1
        LPBJ AD 2 - 4
        LPFR AD 2.24.01 - 1
    """
    t = compact_spaces(line_text)

    patterns = [
        r"\b([A-Z]{4})\s+AD\s*2(?:\s*\.\s*\d+)*(?:\s*-\s*\d+)?\b(?!\s*[\/~])"
    ]

    for pattern in patterns:
        match = re.search(pattern, t)
        if match:
            return make_ad_detail(match, match.group(0), "Portugal")

    return None


def match_ad_china(line_text):
    """
    China examples:
        ZPPP AD2-1
        ZPPP AD2 - 1
        ZPPP AD 2 - 1
        ZPPP AD 2.24.01 - 1
    """
    t = compact_spaces(line_text)

    patterns = [
        r"\b([A-Z]{4})\s+AD2(?:\s*-\s*\d+)?\b(?!\s*[\/~])",
        r"\b([A-Z]{4})\s+AD\s*2(?:\s*\.\s*\d+)*(?:\s*-\s*\d+)?\b(?!\s*[\/~])"
    ]

    for pattern in patterns:
        match = re.search(pattern, t)
        if match:
            return make_ad_detail(match, match.group(0), "China")

    return None


def match_ad_brazil(line_text):
    """
    Brazil examples:
        AD 2 SBCT - 10
        AD2 SBCT - 10
    """
    t = compact_spaces(line_text)

    patterns = [
        r"\bAD\s*2\s+([A-Z]{4})\s*-\s*\d+\b(?!\s*[\/~])",
        r"\bAD2\s+([A-Z]{4})\s*-\s*\d+\b(?!\s*[\/~])"
    ]

    for pattern in patterns:
        match = re.search(pattern, t)
        if match:
            return make_ad_detail(match, match.group(0), "Brazil")

    return None


def match_ad_malaysia(line_text):
    """
    Malaysia examples:
        AD 2-WMKP-1-1
        AD 2-WBGB-8-3
        AD2-WMKP-1-1
    """
    t = compact_spaces(line_text)

    patterns = [
        r"\bAD\s*2\s*-\s*([A-Z]{4})\s*-\s*\d+(?:\s*-\s*\d+)?\b(?!\s*[\/~])",
        r"\bAD2\s*-\s*([A-Z]{4})\s*-\s*\d+(?:\s*-\s*\d+)?\b(?!\s*[\/~])"
    ]

    for pattern in patterns:
        match = re.search(pattern, t)
        if match:
            return make_ad_detail(match, match.group(0), "Malaysia")

    return None


def match_ad_indonesia(line_text):
    """
    Indonesia examples:
        WADD AD 2 - 24
        WADD AD 2-24
        WADD AD 2.24-7B4
        WADD AD 2.24-11E2
        WALK AD 2.24-11A2
    """
    t = compact_spaces(line_text)

    patterns = [
        r"\b([A-Z]{4})\s+AD\s*2\s*-\s*\d+\b(?!\s*[\/~])",
        r"\b([A-Z]{4})\s+AD\s*2(?:\s*\.\s*\d+)+(?:\s*-\s*[A-Z0-9]+)?\b(?!\s*[\/~])",
        r"\b([A-Z]{4})\s+AD\s*2(?:\s*\.\s*\d+)*(?:\s*-\s*\d+[A-Z0-9]*)?\b(?!\s*[\/~])"
    ]

    for pattern in patterns:
        match = re.search(pattern, t)
        if match:
            return make_ad_detail(match, match.group(0), "Indonesia")

    return None


def match_ad_asecna(line_text):
    """
    ASECNA group profile.

    Permanent root fix:
    ASECNA uses multi-country prefixes and both dot/hyphen formats.
    Do not rely on one country prefix. Extract ICAO and compare against full master list.

    Supported examples:
        01 AD-2.DBBP-1
        01 AD-2.DBBP.1
        01-AD-2.DBBP-1
        01-AD-2.DBBP.1
        03 AD-2.FKYS.10
        05 AD-2.FCBB.23
        05-AD-2.FCBB.23
        05 AD-2.FCPP.5
        05-AD-2.FCPP.5
        07 AD-2.FOGR-1
        07AD2-FOGK-IAC-RNP15
        07AD2-FOGR-IAC-RNP04-DATA
        11AD2-GQPA-IAC-RNP03
        DBBP AD 2.1
        FOGR AD 2.24
        FCBB AD 2 - 3
    """
    t = compact_spaces(line_text)

    patterns = [
        # 05 AD-2.FCBB.23 / 05 AD-2.FCBB-23 / 05-AD-2.FCBB.23
        r"\b\d{2}\s*[- ]?\s*AD\s*[- ]?\s*2\s*[\.\-]\s*([A-Z]{4})(?:\s*[\.\-]\s*[A-Z0-9]+)+\b",

        # 05AD-2.FCBB.23 / 05AD-2.FCBB-23
        r"\b\d{2}\s*AD\s*[- ]?\s*2\s*[\.\-]\s*([A-Z]{4})(?:\s*[\.\-]\s*[A-Z0-9]+)+\b",

        # 07AD2-FOGK-IAC-RNP15 / 07AD2-FOGR-IAC-RNP04-DATA
        r"\b\d{2}\s*AD\s*2\s*-\s*([A-Z]{4})(?:\s*-\s*[A-Z0-9]+)+\b",

        # 07 AD-2. FOGR / 01AD-2. /DBBP style
        r"\b\d{2}\s*[- ]?\s*AD\s*[- ]?\s*2\s*[\.\-/ ]+\s*([A-Z]{4})\b",

        # DBBP AD 2.1 / FOGR AD 2.24 / FCBB AD 2.23
        r"\b([A-Z]{4})\s+AD\s*2(?:\s*\.\s*\d+)+(?:\s*-\s*[A-Z0-9]+)?\b",

        # FCBB AD 2 - 3
        r"\b([A-Z]{4})\s+AD\s*2\s*-\s*\d+\b(?!\s*[\/~])"
    ]

    for pattern in patterns:
        match = re.search(pattern, t)
        if match:
            return make_ad_detail(match, match.group(0), "ASECNA")

    return None

def match_ad_france(line_text):
    """
    France (LFxx) AD-2 identifiers. ICAO always starts with LF:
        AD-2.LFAY-1 / AD 2.LFOB-6 / AD-2.LFBZ
        AD 2 LFAY DATA 01 / AD 2 LFOB ADC 01 / AD 2 LFBZ IAC RWY27 RNP
        LFAY AD 2 (rare, icao-first)
    Requiring LF also prevents the Universal false-positives where
    English headings 'NAME AD 2' / 'AIDS AD 2' were grabbed as ICAOs.
    """
    t = compact_spaces(line_text)

    patterns = [
        r"\bAD\s*[-\.]?\s*2\s*[\.\-]\s*(LF[A-Z]{2})\b(?!\s*[\/~])",
        r"\bAD\s*2\s+(LF[A-Z]{2})\b(?!\s*[\/~])",
        r"\b(LF[A-Z]{2})\s+AD\s*2\b(?!\s*[\/~])",
    ]

    for pattern in patterns:
        match = re.search(pattern, t)
        if match:
            return make_ad_detail(match, match.group(0), "France")

    return None

def match_ad_bahamas(line_text):
    """
    Bahamas (MYxx): ICAO in the MIDDLE of the header, subsection before page:
        AD 2 MYAM 1 - 3 / AD 2 MYNN 1 - 13 / AD 2 MYCA 1 - 6
    """
    t = compact_spaces(line_text)

    patterns = [
        r"\bAD\s*2\s+([A-Z]{4})\s+\d+\s*-\s*\d+\b(?!\s*[\/~])",
    ]

    for pattern in patterns:
        match = re.search(pattern, t)
        if match:
            return make_ad_detail(match, match.group(0), "Bahamas")

    return None

def match_ad_cocesna(line_text):
    """
    COCESNA group profile.

    Identity is the running page-id: "AD-2.MSLP-10", "AD-2.MGGT.14",
    "AD-2.MSSS ARC", or the header form "MSLP AD 2.16". The bare
    "AD-2.<ICAO>" form (nothing parsable after the ICAO) was missing from
    the old pattern list, which is why every AD-2 page resolved to None.

    Central American ICAOs are all M-prefixed (MZ Belize, MR Costa Rica,
    MS El Salvador, MG Guatemala, MH Honduras, MN Nicaragua).
    """
    t = compact_spaces(line_text)

    patterns = [
        # AD-2.MSLP-10 / AD-2.MGGT.14 / AD-2.MSSS ARC / bare AD-2.MSLP
        r"\bAD\s*[- ]?\s*2\s*[\.\-]\s*(M[A-Z]{3})\b",

        # 01 AD-2.MHTG-1 / 01AD2-MHTG-IAC-RNP02
        r"\b\d{2}\s*[- ]?\s*AD\s*[- ]?\s*2\s*[\.\-]\s*(M[A-Z]{3})\b",

        # AD 2 MHTG - 1
        r"\bAD\s*2\s+(M[A-Z]{3})\s*-\s*\d+\b(?!\s*[\/~])",

        # MSLP AD 2.16 / MGGT AD 2.24   (ICAO-first header form)
        r"\b(M[A-Z]{3})\s+AD\s*2(?:\s*\.\s*\d+)*\b(?!\s*[\/~])",
    ]

    for pattern in patterns:
        match = re.search(pattern, t)
        if match:
            return make_ad_detail(match, match.group(0), "COCESNA")

    return None


def match_ad_universal(line_text):
    """
    Universal mode combines all known country/profile patterns.
    Use this only when country is unknown or user intentionally selects Universal.
    """
    for matcher in [
        match_ad_bahamas,
        match_ad_asecna,
        match_ad_cocesna,
        match_ad_malaysia,
        match_ad_brazil,
        match_ad_indonesia,
        match_ad_china,
        match_ad_portugal,
        match_ad_france
    ]:
        detail = matcher(line_text)
        if detail:
            detail["parser"] = "Universal-" + detail.get("parser", "unknown")
            return detail

    return None


def match_airport_ad_title_for_country(line_text, country):
    if country == "Portugal":
        return match_ad_portugal(line_text)

    if country == "China":
        return match_ad_china(line_text)

    if country == "Brazil":
        return match_ad_brazil(line_text)

    if country == "Malaysia":
        return match_ad_malaysia(line_text)

    if country == "Indonesia":
        return match_ad_indonesia(line_text)

    if country == "ASECNA":
        return match_ad_asecna(line_text)

    if country == "COCESNA":
        return match_ad_cocesna(line_text)

    return match_ad_universal(line_text)


# =============================
# PAGE IDENTITY DETECTION
# =============================
def extract_section_detail_from_page(page, page_text, country):
    """
    Country-aware page identity detection.

    Priority:
    1. Protect group index/checklist pages.
    2. Airport AD title from country/profile-specific parser.
    3. Generic section title.
    4. Joined header/footer title.
    5. Full-body fallback only for generic section, never airport owner ICAO.

    Leakproof rule:
    - Full page body is never used to create AD airport owner ICAO.
    - Airport owner ICAO comes from header/footer/title-zone only.
    """
    title_lines = get_zone_lines(page)
    admin_page = is_administrative_list_page(page_text, country)
    group_index_page = is_group_index_or_checklist_page(page_text, title_lines, country)

    if group_index_page:
        for line in title_lines:
            generic_detail = match_generic_section_title(line)
            if generic_detail:
                return generic_detail

        joined_title = compact_spaces(" ".join(title_lines))
        generic_detail = match_generic_section_title(joined_title)
        if generic_detail:
            return generic_detail

    for line in title_lines:
        airport_detail = match_airport_ad_title_for_country(line, country)

        if airport_detail and not admin_page and not group_index_page:
            return airport_detail

        generic_detail = match_generic_section_title(line)

        if generic_detail:
            return generic_detail

    joined_title = compact_spaces(" ".join(title_lines))

    airport_detail = match_airport_ad_title_for_country(joined_title, country)

    if airport_detail and not admin_page and not group_index_page:
        return airport_detail

    generic_detail = match_generic_section_title(joined_title)

    if generic_detail:
        return generic_detail

    limited_text = compact_spaces(page_text[:1500])

    fallback_patterns = [
        r"\b(?:\d{2}\s*[- ]\s*)?(GEN)\s*[\.\-]?\s*(\d+)(?:\s*[\.\-]\s*\d+)*\b",
        r"\b(?:\d{2}\s*[- ]\s*)?(ENR)\s*[\.\-]?\s*(\d+)(?:\s*[\.\-]\s*\d+)*\b",
        r"\b(?:\d{2}\s*[- ]\s*)?(AD)\s*[\.\-]?\s*(\d+)(?:\s*[\.\-]\s*\d+)*\b",
    ]

    for pattern in fallback_patterns:
        match = re.search(pattern, limited_text)

        if match:
            return {
                "section": match.group(1),
                "major": int(match.group(2)),
                "raw": match.group(0),
                "icao": None,
                "is_airport_ad": False,
                "parser": "fallback-generic"
            }

    section_only_patterns = [
        r"\b(GEN)\b",
        r"\b(ENR)\b",
        r"\b(AD)\b",
    ]

    for pattern in section_only_patterns:
        match = re.search(pattern, limited_text)

        if match:
            return {
                "section": match.group(1),
                "major": None,
                "raw": match.group(0),
                "icao": None,
                "is_airport_ad": False,
                "parser": "fallback-section-only"
            }

    return {
        "section": None,
        "major": None,
        "raw": None,
        "icao": None,
        "is_airport_ad": False,
        "parser": "unrecognized"
    }


def extract_section_detail(text):
    """
    Backward-compatible text-only section detector for old session-state tuples.
    """
    full_text = compact_spaces(str(text)[:1500])

    fallback_patterns = [
        r"\b(?:\d{2}\s*[- ]\s*)?(GEN)\s*[\.\-]?\s*(\d+)(?:\s*[\.\-]\s*\d+)*\b",
        r"\b(?:\d{2}\s*[- ]\s*)?(ENR)\s*[\.\-]?\s*(\d+)(?:\s*[\.\-]\s*\d+)*\b",
        r"\b(?:\d{2}\s*[- ]\s*)?(AD)\s*[\.\-]?\s*(\d+)(?:\s*[\.\-]\s*\d+)*\b",
    ]

    for pattern in fallback_patterns:
        match = re.search(pattern, full_text)

        if match:
            return {
                "section": match.group(1),
                "major": int(match.group(2)),
                "raw": match.group(0),
                "icao": None,
                "is_airport_ad": False,
                "parser": "compat"
            }

    return {
        "section": None,
        "major": None,
        "raw": None,
        "icao": None,
        "is_airport_ad": False,
        "parser": "compat-unrecognized"
    }


# =============================
# PAGE TUPLE HELPERS
# =============================
def get_page_index(page_tuple):
    return page_tuple[0] if len(page_tuple) > 0 else None


def get_page_section(page_tuple):
    return page_tuple[1] if len(page_tuple) > 1 else None


def get_page_major(page_tuple):
    return page_tuple[2] if len(page_tuple) > 2 else None


def get_clean_removed_category(section_detail):
    section = section_detail.get("section")
    major = section_detail.get("major")

    if section and major is not None:
        return f"{section} {major}"

    if section:
        return section

    return "Other / Unrecognized Pages"


def is_auto_removed_section(section_detail):
    """
    Auto-removes only actual titled AIP sections and all their subsections,
    regardless of selected effective date:

        GEN 1, GEN 2, GEN 3, GEN 4, GEN 5
        ENR 0, ENR 2, ENR 5, ENR 6
    """
    section = section_detail.get("section")
    major = section_detail.get("major")

    if section == "GEN" and major in {1, 2, 3, 4, 5}:
        return True

    if section == "ENR" and major in {0, 2, 5, 6}:
        return True

    return False


def get_owner_icao_from_section_detail(section_detail):
    icao = section_detail.get("icao")

    if icao:
        return str(icao).strip().upper()

    return None


# =============================
# PREVIEW CACHE
# =============================
@st.cache_data(show_spinner=False, max_entries=300)
def render_preview_page(input_pdf_path, page_index, render_scale, file_mtime):
    """
    Cached page rendering for fast preview.
    file_mtime is included only to invalidate cache when a new uploaded file is saved.
    """
    doc = fitz.open(input_pdf_path)
    page = doc[page_index]

    pix = page.get_pixmap(
        matrix=fitz.Matrix(render_scale, render_scale),
        alpha=False
    )

    image_bytes = pix.tobytes("png")

    doc.close()

    return image_bytes


# =============================
# CALLBACKS
# =============================
def sync_enr_subsections():
    """
    When user turns ON the main ENR toggle,
    all available ENR major subsections are automatically turned ON.

    User can manually turn OFF any ENR subsection after that.
    """
    if st.session_state.get("toggle_ENR", False):
        for key in st.session_state.get("enr_subsection_keys", []):
            st.session_state[key] = True

def sync_ad_subsections():
    if st.session_state.get("toggle_AD", False):
        for key in st.session_state.get("ad_subsection_keys", []):
            st.session_state[key] = True

def load_more_preview_pages():
    """
    Stable callback for Load More Pages.
    This avoids preview_limit update being lost during Streamlit reruns.
    """
    st.session_state.preview_limit = st.session_state.get("preview_limit", 10) + 10


# =============================
# PROCESS PDF
# =============================
def process_pdf(input_pdf_path, selected_date, country):
    doc = fitz.open(input_pdf_path)
    total_pdf_pages = len(doc)
    allowed_icaos = load_master()

    temp_pages = []
    auto_removed_pages = []
    removed_page_details = []

    detected_ad_owners = set()
    kept_ad_owners = set()
    removed_ad_owners = set()
    ad_detection_details = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        text = page.get_text()

        # Some pages (e.g. Bahamas big table pages) mangle the running-header
        # date in plain get_text() reading order, so the contiguous date match
        # fails. The clean header/footer zone lines still carry it, so append
        # them for date matching only.
        date_text = text + "\n" + "\n".join(get_zone_lines(page))

        section_detail = extract_section_detail_from_page(page, text, country)
        section = section_detail["section"]

        owner_icao = get_owner_icao_from_section_detail(section_detail)

        if section == "AD" and section_detail.get("major") == 2 and owner_icao:
            detected_ad_owners.add(owner_icao)
            ad_detection_details.append(
                {
                    "page": page_index + 1,
                    "icao": owner_icao,
                    "raw": section_detail.get("raw"),
                    "parser": section_detail.get("parser")
                }
            )

        if not section:
            removed_page_details.append(
                {
                    "page": page_index + 1,
                    "category": get_clean_removed_category(section_detail)
                }
            )
            continue

        if is_auto_removed_section(section_detail):
            auto_removed_pages.append(
                {
                    "page": page_index + 1,
                    "section": section_detail["section"],
                    "major": section_detail["major"],
                    "raw": section_detail["raw"]
                }
            )

            removed_page_details.append(
                {
                    "page": page_index + 1,
                    "category": get_clean_removed_category(section_detail)
                }
            )
            continue

        if not match_date_for_country(date_text, selected_date, country):
            removed_page_details.append(
                {
                    "page": page_index + 1,
                    "category": get_clean_removed_category(section_detail)
                }
            )
            continue

        temp_pages.append((page_index, section, section_detail))

    final_pages = []

    for page_index, section, section_detail in temp_pages:
        major = section_detail.get("major")

        if section == "AD" and major == 2:
            owner_icao = get_owner_icao_from_section_detail(section_detail)

            if not owner_icao:
                removed_page_details.append(
                    {
                        "page": page_index + 1,
                        "category": get_clean_removed_category(section_detail)
                    }
                )
                continue

            if owner_icao in allowed_icaos:
                kept_ad_owners.add(owner_icao)
            else:
                removed_ad_owners.add(owner_icao)

                removed_page_details.append(
                    {
                        "page": page_index + 1,
                        "category": get_clean_removed_category(section_detail)
                    }
                )
                continue

        final_pages.append(
            (
                page_index,
                section,
                major
            )
        )

    doc.close()

    return (
        total_pdf_pages,
        final_pages,
        detected_ad_owners,
        kept_ad_owners,
        removed_ad_owners,
        auto_removed_pages,
        removed_page_details,
        ad_detection_details
    )
    # =============================
# SELECTION HELPERS
# =============================
def get_selected_page_tuples(pages, selected_sections, selected_enr_majors, selected_ad_majors):
    selected_page_tuples = []

    for page_tuple in pages:
        page_index = get_page_index(page_tuple)
        section = get_page_section(page_tuple)
        major = get_page_major(page_tuple)

        if page_index is None:
            continue

        if section == "ENR":
            if "ENR" in selected_sections and major in selected_enr_majors:
                selected_page_tuples.append(page_tuple)

        elif section == "AD":
            if "AD" in selected_sections:
                if major is None or major in selected_ad_majors:
                    selected_page_tuples.append(page_tuple)

        elif section in selected_sections:
            selected_page_tuples.append(page_tuple)

    return selected_page_tuples


def get_selection_signature(selected_sections, selected_enr_majors, selected_ad_majors, country):
    return (
        country,
        tuple(sorted(selected_sections)),
        tuple(sorted(selected_enr_majors)),
        tuple(sorted(selected_ad_majors))
    )


def get_preview_signature(selected_preview_indexes, selection_signature):
    """
    Stable signature for preview pagination.

    If selected pages change, preview_limit resets to 10.
    If selected pages do not change, Load More persists.
    """
    return (
        selection_signature,
        len(selected_preview_indexes),
        selected_preview_indexes[0] if selected_preview_indexes else None,
        selected_preview_indexes[-1] if selected_preview_indexes else None
    )


# =============================
# BUILD PDF TO DISK
# =============================
def build_pdf_to_file(input_pdf_path, selected_page_tuples, output_pdf_path):
    source_doc = fitz.open(input_pdf_path)
    output_doc = fitz.open()

    for page_tuple in selected_page_tuples:
        page_index = get_page_index(page_tuple)

        if page_index is None:
            continue

        output_doc.insert_pdf(
            source_doc,
            from_page=page_index,
            to_page=page_index
        )

    page_count = output_doc.page_count

    if page_count == 0:
        output_doc.close()
        source_doc.close()
        safe_remove_file(output_pdf_path)
        return False, 0

    if page_count > 200:
        output_doc.save(
            output_pdf_path,
            garbage=3,
            deflate=True,
            clean=False
        )
    else:
        output_doc.save(
            output_pdf_path,
            garbage=4,
            deflate=True,
            clean=True
        )

    output_doc.close()
    source_doc.close()

    return True, page_count

def filter_merged_pdf_by_date(input_path, selected_date, output_path, matcher):
    """
    Keep only pages of an already-merged PDF whose text matches `selected_date`
    (using the provided country matcher). The date may sit in the footer, so
    the clean header/footer zone lines are appended for matching.
    Returns (ok, kept_page_numbers).
    """
    doc = fitz.open(input_path)
    out = fitz.open()
    kept = []
    for i in range(len(doc)):
        text = doc[i].get_text()
        date_text = text + "\n" + "\n".join(get_zone_lines(doc[i]))
        if matcher(date_text, selected_date):
            out.insert_pdf(doc, from_page=i, to_page=i)
            kept.append(i + 1)
    ok = out.page_count > 0
    if ok:
        out.save(output_path, garbage=4, deflate=True)
    out.close()
    doc.close()
    return ok, kept

def prepare_output_pdf(selected_page_tuples, selection_signature):
    input_pdf_path = st.session_state.get("input_pdf_path")

    if not input_pdf_path or not os.path.exists(input_pdf_path):
        return None, 0

    current_output_path = st.session_state.get("output_pdf_path")

    safe_remove_file(current_output_path)

    output_pdf_path = make_temp_pdf_path("trimmed_aip")

    success, output_page_count = build_pdf_to_file(
        input_pdf_path=input_pdf_path,
        selected_page_tuples=selected_page_tuples,
        output_pdf_path=output_pdf_path
    )

    if not success:
        st.session_state.output_pdf_path = None
        st.session_state.output_page_count = 0
        st.session_state.last_selection_signature = None
        return None, 0

    st.session_state.output_pdf_path = output_pdf_path
    st.session_state.output_page_count = output_page_count
    st.session_state.last_selection_signature = selection_signature

    return output_pdf_path, output_page_count

# =============================================================
# CHILE — fully isolated parser (does NOT touch other logic)
#
# Master (MAL) filter policy:
#   - EVERY AD 2 page (main + all subsections AD 2.0/2.A/2.B/2.M ...)
#     -> keep only if its header ICAO is in the master list
#   - AD 3.1 (minor aerodromes) & AD 3.2 (heliports) -> kept as-is
#
# No hardcoded zone blocklist needed: zone/FIR codes (SCFZ, SCEZ, ...)
# simply aren't in the master list, so they get dropped automatically.
# =============================================================
CHILE_ICAO_RE = re.compile(r"\b(SC[A-Z]{2}|SH[A-Z]{2})\b")
CHILE_HEADER_MARKERS = ("AIP-CHILE", "AIS-CHILE")


def _chile_extract_icaos(page_text, sh_ok):
    codes = set()
    for match in CHILE_ICAO_RE.finditer(str(page_text).upper()):
        code = match.group(1)
        if code.startswith("SH") and not sh_ok:
            continue
        codes.add(code)
    return codes


def _chile_lines(page_text):
    return [compact_spaces(r) for r in str(page_text).splitlines() if compact_spaces(r)]


def _chile_identity(page_text):
    lines = _chile_lines(page_text)

    # A page's identity must be a REAL running-header page-id ("ENR 5.1-9",
    # "AD 3.1-26", "AD 2.0-5", "AD 2 SCIE-5"), never a loose body cross-ref
    # like "...AIP-CHILE, ENR 7 ...".
    header_rules = [
        ("AD2",    r"AD\s*2\s+(SC[A-Z]{2})\s*-?\s*\d"),   # AD 2 SCIE-5
        ("AD2SUB", r"AD\s*2\s*\.\s*\d+\s*-\s*\d"),         # AD 2.0-5 (ICAO elsewhere on line)
        ("AD3",    r"AD\s*3\s*\.\s*(\d)\s*-\s*\d"),
        ("ADX",    r"AD\s*([01])\s*\.\s*\d+\s*-\s*\d"),
        ("GEN",    r"(GEN)\s*(\d+)\.\d+\s*-\s*\d"),
        ("ENR",    r"(ENR)\s*(\d+)\.\d+\s*-\s*\d"),
    ]
    for line in lines:
        if not any(mk in line for mk in CHILE_HEADER_MARKERS):
            continue
        for kind, pat in header_rules:
            m = re.search(pat, line)
            if m:
                return kind, m, line

    standalone_rules = [
        ("AD3",    r"^AD\s*3\s*\.\s*(\d)\s*-\s*\d"),
        ("AD2",    r"^AD\s*2\s+(SC[A-Z]{2})\s*-\s*\d"),
        ("AD2SUB", r"^AD\s*2\s*\.\s*\d"),
        ("ADX",    r"^AD\s*([01])\s*\.\s*\d"),
        ("GEN",    r"^(GEN)\s*(\d+)\s*[\.\-]"),
        ("ENR",    r"^(ENR)\s*(\d+)\s*[\.\-]"),
    ]
    for line in lines:
        for kind, pat in standalone_rules:
            m = re.match(pat, line)
            if m:
                return kind, m, line

    return None, None, None


def _chile_section_detail(page_text):
    kind, m, line = _chile_identity(page_text)

    if not kind:
        return {"section": None, "major": None, "raw": None, "icao": None,
                "owner_icaos": set(), "parser": "Chile-unrecognized"}

    if kind == "AD2":
        icao = m.group(1).upper()
        return {"section": "AD", "major": 2, "raw": m.group(0), "icao": icao,
                "owner_icaos": {icao}, "parser": "Chile-AD2"}

    if kind == "AD2SUB":
        # AD 2.x subsection page (e.g. "AD 2.0-5 SCFZ"). The ICAO sits
        # elsewhere on the same header line. Pull it from the header first;
        # fall back to the body if the header has none.
        owners = _chile_extract_icaos(line, sh_ok=True)
        if not owners:
            owners = _chile_extract_icaos(page_text, sh_ok=True)
        return {"section": "AD", "major": 2, "raw": m.group(0), "icao": None,
                "owner_icaos": owners, "parser": "Chile-AD2gen"}

    if kind == "AD3":
        sub = int(m.group(1))
        if sub in (1, 2):
            owners = _chile_extract_icaos(page_text, sh_ok=(sub == 2))
            return {"section": "AD", "major": 2, "raw": m.group(0), "icao": None,
                    "owner_icaos": owners, "parser": f"Chile-AD3.{sub}"}
        return {"section": "AD", "major": 3, "raw": m.group(0), "icao": None,
                "owner_icaos": set(), "parser": "Chile-AD3.0"}

    if kind == "ADX":
        return {"section": "AD", "major": int(m.group(1)), "raw": m.group(0),
                "icao": None, "owner_icaos": set(), "parser": "Chile-ADadmin"}

    section, major = m.group(1), int(m.group(2))
    return {"section": section, "major": major, "raw": m.group(0), "icao": None,
            "owner_icaos": set(), "parser": "Chile-generic"}


def process_pdf_chile(input_pdf_path, selected_date):
    """Chile-only pipeline. Returns the SAME 8-tuple as process_pdf()."""
    doc = fitz.open(input_pdf_path)
    total_pdf_pages = len(doc)
    allowed_icaos = load_master()

    temp_pages, auto_removed_pages, removed_page_details = [], [], []
    detected_ad_owners, kept_ad_owners, removed_ad_owners = set(), set(), set()
    ad_detection_details = []

    for page_index in range(len(doc)):
        text = doc[page_index].get_text()
        detail = _chile_section_detail(text)
        section = detail["section"]
        owners = set(detail.get("owner_icaos") or set())

        if section == "AD" and detail.get("major") == 2 and owners:
            detected_ad_owners.update(owners)
            ad_detection_details.append(
                {"page": page_index + 1, "icao": ", ".join(sorted(owners)),
                 "raw": detail.get("raw"), "parser": detail.get("parser")})

        if not section:
            removed_page_details.append(
                {"page": page_index + 1, "category": get_clean_removed_category(detail)})
            continue

        if is_auto_removed_section(detail):
            auto_removed_pages.append(
                {"page": page_index + 1, "section": detail["section"],
                 "major": detail["major"], "raw": detail["raw"]})
            removed_page_details.append(
                {"page": page_index + 1, "category": get_clean_removed_category(detail)})
            continue

        if not match_date_for_country(text, selected_date, "Chile"):
            removed_page_details.append(
                {"page": page_index + 1, "category": get_clean_removed_category(detail)})
            continue

        temp_pages.append((page_index, section, detail))

    final_pages = []
    for page_index, section, detail in temp_pages:
        major = detail.get("major")
        parser = detail.get("parser") or ""

        # Master-list filter applies to EVERY AD 2 page — main airport pages
        # (Chile-AD2) AND all subsections (Chile-AD2gen). AD 3.1 / AD 3.2
        # are exempt and kept as-is.
        is_ad2_family = parser in ("Chile-AD2", "Chile-AD2gen")

        if section == "AD" and major == 2 and is_ad2_family:
            owners = set(detail.get("owner_icaos") or set())
            matched = {i for i in owners if i in allowed_icaos}
            if matched:
                kept_ad_owners.update(matched)
                removed_ad_owners.update(owners - matched)
            else:
                removed_ad_owners.update(owners)
                removed_page_details.append(
                    {"page": page_index + 1, "category": get_clean_removed_category(detail)})
                continue

        final_pages.append((page_index, section, major))

    doc.close()
    return (total_pdf_pages, final_pages, detected_ad_owners, kept_ad_owners,
            removed_ad_owners, auto_removed_pages, removed_page_details,
            ad_detection_details)

# =============================================================
# PARAGUAY (DINAC) — isolated. NOT part of Universal.
# Header page-id is "AD 2.1-3" (no ICAO). The ICAO lives in the
# BODY as "SGAS ..." or only the aerodrome NAME is printed
# ("LUQUE / SILVIO PETTIROSSI INTL."). AD 2.N = one AIRPORT, so
# N -> ICAO is learned in pass 1 and reused for every 2.N page.
# Image-only chart pages inherit the previous page's identity.
# =============================================================
PY_ICAO_RE = re.compile(r"\b(SG[A-Z]{2})\b")
PY_ID_RE   = re.compile(r"\b(GEN|ENR|AD)\s*(\d+)\s*\.\s*(\d+)\s*-\s*[\d.]+", re.I)
PY_NAME_RE = re.compile(r"\b([A-ZÑÜ]{4,})\s*/\s*[“\"']?[A-ZÑÜ]")


def _py_identity(page, text):
    head_lines = [compact_spaces(l) for l in str(text).splitlines()[:6]]
    for line in get_zone_lines(page) + head_lines:
        m = PY_ID_RE.search(line)
        if m:
            return m.group(1).upper(), int(m.group(2)), int(m.group(3)), m.group(0)
    return None, None, None, None


def _py_icao(text):
    m = PY_ICAO_RE.search(str(text).upper())
    return m.group(1) if m else None


def _py_names(text):
    return {m.group(1).upper() for m in PY_NAME_RE.finditer(normalize_for_admin(text))}


def process_pdf_paraguay(input_pdf_path, selected_date):
    """Paraguay-only pipeline. Returns the SAME 8-tuple as process_pdf()."""
    doc = fitz.open(input_pdf_path)
    total_pdf_pages = len(doc)
    allowed_icaos = load_master()

    # ---- PASS 1: identity + learn AD2.N -> ICAO and NAME -> ICAO ----
    scanned, group_map, name_map = [], {}, {}
    last = {"s": None, "mj": None, "sub": None, "d": False}

    for page_index in range(len(doc)):
        page = doc[page_index]
        text = page.get_text()
        date_text = text + "\n" + "\n".join(get_zone_lines(page))

        s, mj, sub, raw = _py_identity(page, text)
        icao = _py_icao(text)
        names = _py_names(text)
        d_ok = match_date_for_country(date_text, selected_date, "Paraguay")

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

        scanned.append(dict(idx=page_index, s=s, mj=mj, sub=sub, raw=raw,
                            icao=icao, names=names, d=d_ok, inh=inherited))

    # ---- PASS 2: resolve + filter ----
    temp_pages, auto_removed_pages, removed_page_details = [], [], []
    detected_ad_owners, kept_ad_owners, removed_ad_owners = set(), set(), set()
    ad_detection_details = []

    for r in scanned:
        s, mj, sub, page_index = r["s"], r["mj"], r["sub"], r["idx"]

        detail = {"section": s, "major": mj, "raw": r["raw"], "icao": None,
                  "is_airport_ad": False,
                  "parser": "Paraguay-chart" if r["inh"] else "Paraguay"}

        if s == "AD" and mj == 2:
            # 1) ICAO on the page  2) AD 2.N group  3) learned aerodrome name
            icao = r["icao"] or group_map.get(sub)
            if not icao:
                for nm in r["names"]:
                    if nm in name_map:
                        icao = name_map[nm]
                        break
            if icao:
                detail.update({"icao": icao, "is_airport_ad": True})
                detected_ad_owners.add(icao)
                ad_detection_details.append(
                    {"page": page_index + 1, "icao": icao,
                     "raw": f"AD 2.{sub} ({r['raw']})", "parser": detail["parser"]})

        if not s:
            removed_page_details.append(
                {"page": page_index + 1, "category": get_clean_removed_category(detail)})
            continue

        if is_auto_removed_section(detail):
            auto_removed_pages.append({"page": page_index + 1, "section": s,
                                       "major": mj, "raw": r["raw"]})
            removed_page_details.append(
                {"page": page_index + 1, "category": get_clean_removed_category(detail)})
            continue

        if not r["d"]:
            removed_page_details.append(
                {"page": page_index + 1, "category": get_clean_removed_category(detail)})
            continue

        temp_pages.append((page_index, s, detail))

    final_pages = []
    for page_index, section, detail in temp_pages:
        major = detail.get("major")

        if section == "AD" and major == 2:
            icao = detail.get("icao")
            # Fail OPEN: an AD 2 page whose airport can't be resolved is KEPT,
            # never silently deleted.
            if icao:
                if icao in allowed_icaos:
                    kept_ad_owners.add(icao)
                else:
                    removed_ad_owners.add(icao)
                    removed_page_details.append(
                        {"page": page_index + 1,
                         "category": get_clean_removed_category(detail)})
                    continue

        final_pages.append((page_index, section, major))

    doc.close()
    st.session_state["py_group_map"] = dict(sorted(group_map.items()))

    return (total_pdf_pages, final_pages, detected_ad_owners, kept_ad_owners,
            removed_ad_owners, auto_removed_pages, removed_page_details,
            ad_detection_details)
            
# =============================================================
# AUSTRALIA (ERSA) — fully isolated. NOT part of Universal.
# ERSA publishes one FAC_<ICAO>_<DATE>.pdf per aerodrome.
# The ICAO is in the FILENAME, so we filter by filename against
# the master list, download the wanted ones, and MERGE into one PDF.
# =============================================================
import requests
from io import BytesIO

AU_BASE = "https://www.airservicesaustralia.com"

def get_ersa_cycles():
    """
    Read the AIP index (pg=10) and pull the ERSA cycle dates straight from the
    'En Route Supplement Australia (ERSA) (09 JUL 2026)' lines.
    Returns compact codes like ['09JUL2026', '03SEP2026'] in page order
    (current cycle first). Fully auto — rolls over on its own.
    """
    try:
        s = requests.Session()
        s.headers.update({"User-Agent": "Mozilla/5.0",
                          "Referer": f"{AU_BASE}/aip/aip.asp"})
        s.get(f"{AU_BASE}/aip/aip.asp", timeout=30)
        html = s.get(f"{AU_BASE}/aip/aip.asp?pg=10", timeout=30).text.upper()

        # anchor on the ERSA line, then grab the (DD MON YYYY) right after it
        raw = re.findall(
            r"ERSA\)[^(]*\((\d{1,2}\s*[A-Z]{3}\s*\d{4})\)", html
        )

        seen, ordered = set(), []
        for d in raw:
            compact = re.sub(r"\s+", "", d).upper()      # '09 JUL 2026' -> '09JUL2026'
            # zero-pad day if needed: '9JUL2026' -> '09JUL2026'
            m = re.match(r"(\d{1,2})([A-Z]{3})(\d{4})", compact)
            if m:
                compact = f"{int(m.group(1)):02d}{m.group(2)}{m.group(3)}"
            if compact not in seen:
                seen.add(compact)
                try:
                    datetime.strptime(compact, "%d%b%Y")   # validate
                    ordered.append(compact)
                except ValueError:
                    pass
        return ordered
    except Exception:
        return []
    
def _accept_airservices_terms(session):
    """
    Airservices gates AIP/ERSA downloads behind a terms-acceptance form.
    Hitting the landing page then POSTing the accept form sets the cookie
    that makes the FAC_*.pdf links return real PDFs instead of HTML.
    """
    # 1) land on the AIP page so ASP.NET / session cookies are issued
    landing = session.get(f"{AU_BASE}/aip/aip.asp", timeout=30)

    # 2) POST the common acceptance form values (covers the known gate variants)
    for accept_url in (
        f"{AU_BASE}/aip/aip.asp",
        f"{AU_BASE}/aip/terms.asp",
    ):
        try:
            session.post(
                accept_url,
                data={
                    "Accept": "I Accept",
                    "accept": "yes",
                    "terms": "accept",
                    "agree": "1",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
                allow_redirects=True,
            )
        except Exception:
            pass

    return session

def _accept_ersa_terms(session):
    """
    Click-through the Airservices 'I Agree' copyright gate so the PENDING
    cycle (e.g. 03 SEP) FAC PDFs return real PDFs instead of the agree page.
    """
    # land first so the session cookie is issued
    try:
        session.get(f"{AU_BASE}/aip/aip.asp", timeout=30)
    except Exception:
        pass

    # POST the "I Agree" form (covers the known button field variants)
    for data in (
        {"btnAgree": "I Agree"},
        {"Agree": "I Agree"},
        {"agree": "I Agree", "Accept": "I Agree"},
    ):
        try:
            session.post(f"{AU_BASE}/aip/aip.asp", data=data,
                         timeout=30, allow_redirects=True)
        except Exception:
            pass

    return session

def process_australia_ersa(cycle_date, output_pdf_path):
    """
    cycle_date example: '09JUL2026'
    Returns (merged_path, kept_icaos, skipped_not_in_master, failed)
    """
    master = load_master()

    session = requests.Session()
    # pass the "I Agree" copyright gate (needed for the pending/next cycle)
    _accept_ersa_terms(session)

    # ---- pass the terms gate first ----
    _accept_airservices_terms(session)

    # The CURRENT cycle uses ver=1, the NEXT cycle uses ver=2. Try both and
    # keep whichever page actually has FAC links for this cycle_date.
    pairs = []
    for ver in ("1", "2", "3"):
        index_url = f"{AU_BASE}/aip/aip.asp?pg=40&vdate={cycle_date}&ver={ver}"
        try:
            html = session.get(index_url, timeout=30).text
        except Exception:
            continue

        pairs = re.findall(
            rf"(/aip/[^\"'>\s]*?ersa/FAC_([A-Z0-9]{{3,4}})_{cycle_date}\.pdf)", html
        )
        if pairs:
            break   # found the right version page

    if not pairs:
        return output_pdf_path, [], [], [("index", "no FAC links found for this cycle")]

    seen, links = set(), []
    for path, code in pairs:
        if path not in seen:
            seen.add(path)
            links.append((AU_BASE + path, code.upper()))

    wanted = [(u, i) for (u, i) in links if i in master]
    skipped_not_in_master = sorted({i for (_, i) in links if i not in master})

    merged = fitz.open()
    kept, failed = [], []

    for url, icao in wanted:
        try:
            r = session.get(url, timeout=60)
            ctype = r.headers.get("content-type", "").lower()
            # accept either a proper PDF content-type OR a PDF magic header
            if ctype.startswith("application/pdf") or r.content[:4] == b"%PDF":
                doc = fitz.open("pdf", BytesIO(r.content))
                merged.insert_pdf(doc)
                doc.close()
                kept.append(icao)
            else:
                failed.append((icao, "not a PDF (terms gate?)"))
        except Exception as e:
            failed.append((icao, str(e)))

    if merged.page_count:
        merged.save(output_pdf_path, garbage=4, deflate=True)
    merged.close()

    return output_pdf_path, sorted(kept), skipped_not_in_master, failed

# =============================================================
# RUSSIA (caica.ru) — fully isolated. NOT part of Universal.
# menueng.htm ships ALL ../amdt/*.pdf links in raw HTML, so plain
# requests works (no JS / Playwright / pasting). Streamlit-safe.
# =============================================================
RU_MENU_URL  = "http://www.caica.ru/ANI_Official/Aip/html/menueng.htm"
RU_AMDT_BASE = "http://www.caica.ru/ANI_Official/Aip/amdt/"

def process_russia_auto(output_pdf_path):
    """
    Fetch menueng.htm, keep 2-AD2 (in master) + ENR 3.1/3.2/1.11, merge.
    Returns (path, kept, skipped, enr_kept, failed, debug)
    """
    master = load_master()
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0", "Referer": RU_MENU_URL})

    debug = {}
    try:
        resp = session.get(RU_MENU_URL, timeout=30, allow_redirects=True)
        html = resp.text
        debug["status"] = resp.status_code
        debug["html_len"] = len(html)
    except Exception as e:
        return output_pdf_path, [], [], [], [("menu", str(e))], {"error": str(e)}

    files = re.findall(r'amdt/([A-Za-z0-9.,_\-]+\.pdf)', html, re.I)
    files = list(dict.fromkeys(files))
    debug["links_found"] = len(files)
    debug["sample"] = files[:8]

    all_links = [RU_AMDT_BASE + f for f in files]

    # AD2 volumes 1, 2 and 3 only — volume 4 is NOT required.
    # Filenames look like: 1-ad2-rus-uhbb-007-008.pdf / 2-ad2-uuee-...pdf
    ad2_icao_re = re.compile(r"^([123])-ad2-(?:rus-)?([a-z]{4})\b", re.I)

    # ENR 1.11 / 3.1 / 3.2 and any of their subsections (e.g. enr3.1.1).
    # (?!\d) stops 3.1 from also matching 3.10 etc.
    enr_keep_re = re.compile(r"^enr[\-_ ]?(1\.11|3\.1|3\.2)(?!\d)", re.I)

    candidates, skipped_icao = [], set()
    for url in all_links:
        fname = url.rsplit("/", 1)[-1].lower()
        if enr_keep_re.search(fname):
            candidates.append((url, f"ENR:{fname}"))
        else:
            m = ad2_icao_re.search(fname)
            if m:
                icao = m.group(2).upper()
                if icao in master:
                    candidates.append((url, f"{icao} (v{m.group(1)})"))
                else:
                    skipped_icao.add(icao)

    debug["candidates"] = len(candidates)
    debug["sample_icaos"] = [t for _, t in candidates[:12]]
    debug["skipped_icaos"] = sorted(skipped_icao)[:20]

    merged = fitz.open()
    kept, enr_kept, failed = [], [], []
    for url, tag in candidates:
        try:
            r = session.get(url, timeout=60)
            if r.content[:4] != b"%PDF":
                failed.append((tag, "not a PDF"))
                continue
            doc = fitz.open("pdf", BytesIO(r.content))
            merged.insert_pdf(doc)
            doc.close()
            if tag.startswith("ENR:"):
                enr_kept.append(tag[4:])
            else:
                kept.append(tag)
        except Exception as e:
            failed.append((tag, str(e)))

    if merged.page_count:
        merged.save(output_pdf_path, garbage=4, deflate=True)
    merged.close()

    return (output_pdf_path, sorted(set(kept)), sorted(skipped_icao),
            sorted(set(enr_kept)), failed, debug)

# =============================================================
# ARGENTINA (ANAC) — isolated. NOT part of Universal.
# ais.anac.gob.ar/amdt renders the latest AMDT's /descarga links.
# Section codes (GEN/ENR/AD) are language-independent → no translate needed.
# =============================================================
AR_BASE     = "https://ais.anac.gob.ar"
AR_AMDT_URL = "https://ais.anac.gob.ar/amdt"

def process_argentina_auto(output_pdf_path):
    """
    Keep GEN 0.1, ENR 1.11, ENR 3.1, ENR 3.2 + AD 2.x (ICAO in master), merge.
    Returns (path, kept_ad, kept_sec, skipped, failed, debug)
    """
    master = load_master()
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0", "Referer": AR_AMDT_URL})

    debug = {}
    try:
        # 1) Load base page (sets cookies) and read the latest amendment id.
        base_html = session.get(AR_AMDT_URL, timeout=30, allow_redirects=True).text

        # Newest amendment = first real <option value="NN"> in the dropdown.
        # (skip the "Select an amendment" placeholder which has no numeric value)
        ids = re.findall(r'<option[^>]*value="(\d+)"', base_html)
        if not ids:
            return (output_pdf_path, [], [], [],
                    [("id", "could not read amendment id from page")],
                    {"error": "no amendment id found", "html_len": len(base_html)})

        amdt_id = str(max(int(x) for x in ids))   # highest id = newest                  # dropdown lists newest first
        debug["amdt_id"] = amdt_id

        amdt = re.search(r"AMDT\s*AIRAC\s*\d{1,2}\s*/\s*\d{4}", base_html, re.I)
        debug["amdt_label"] = amdt.group(0) if amdt else "unknown"

        # 2) The AJAX table lives at /amdt/<id> (confirmed: GET /amdt/48).
        resp = session.get(f"{AR_AMDT_URL}/{amdt_id}", timeout=30,
                           headers={"X-Requested-With": "XMLHttpRequest"})
        html = resp.text
        debug["status"] = resp.status_code
        debug["html_len"] = len(html)
    except Exception as e:
        return output_pdf_path, [], [], [], [("page", str(e))], {"error": str(e)}

    rows = re.findall(r'href="(/descarga/aip-[0-9a-fA-F]+)"[^>]*>(.*?)</a>',
                      html, re.I | re.S)

    def _clean(t):
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)).strip()

    rows = [(h, _clean(t)) for h, t in rows]
    debug["links_found"] = len(rows)
    debug["sample"] = [t for _, t in rows[:8]]

    # Requested non-AD sections. GEN 0.1 kept only if it actually exists.
    wanted = {
        "GEN 0.1":  re.compile(r"\bGEN\s*0\.1(?!\d)", re.I),
        "ENR 1.11": re.compile(r"\bENR\s*1\.11(?!\d)", re.I),
        "ENR 3.1":  re.compile(r"\bENR\s*3\.1(?!\d)", re.I),
        "ENR 3.2":  re.compile(r"\bENR\s*3\.2(?!\d)", re.I),
    }
    ad2_re = re.compile(r"\b([A-Z]{4})\s*-\s*AD\s*2\b")

    candidates, skipped_icao, seen, found_sec = [], set(), set(), set()
    for href, txt in rows:
        if href in seen:
            continue
        seen.add(href)
        url = AR_BASE + href

        hit = next((name for name, rx in wanted.items() if rx.search(txt)), None)
        if hit:
            candidates.append((url, "SEC:" + hit))
            found_sec.add(hit)
            continue

        m = ad2_re.search(txt)
        if m:
            icao = m.group(1).upper()
            if icao in master:
                candidates.append((url, icao))
            else:
                skipped_icao.add(icao)

    debug["candidates"] = len(candidates)
    debug["sections_missing"] = sorted(set(wanted) - found_sec)

    merged = fitz.open()
    kept_ad, kept_sec, failed = [], [], []
    for url, tag in candidates:
        try:
            r = session.get(url, timeout=90)
            if r.content[:4] != b"%PDF":
                failed.append((tag, "not a PDF"))
                continue
            doc = fitz.open("pdf", BytesIO(r.content))
            merged.insert_pdf(doc)
            doc.close()
            if tag.startswith("SEC:"):
                kept_sec.append(tag[4:])
            else:
                kept_ad.append(tag)
        except Exception as e:
            failed.append((tag, str(e)))

    if merged.page_count:
        merged.save(output_pdf_path, garbage=4, deflate=True)
    merged.close()

    return (output_pdf_path, sorted(set(kept_ad)), sorted(set(kept_sec)),
            sorted(skipped_icao), failed, debug)

# =============================================================
# GREECE — isolated profile (full-page text + OCR fallback)
# One airport per page. Identity = "AD 2-LGxx-..." (charts) or
# "AD 2 LGxx-N" (text footer). Effective date is in the FOOTER on
# chart pages, and chart pages are FLATTENED IMAGES -> need OCR.
# =============================================================

def _needs_ocr(text):
    # flattened chart pages return almost nothing from get_text()
    return len(str(text).strip()) < 20


def _ocr_page_text(page, dpi=200):
    """OCR a single page. Returns '' if Tesseract is unavailable."""
    try:
        tp = page.get_textpage_ocr(dpi=dpi, full=True)
        return page.get_text(textpage=tp) or ""
    except Exception:
        return ""

def _ocr_clip_text(page, clip, zoom=7.0):
    """High-res OCR of a small page region (good for tiny footer text)."""
    try:
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip, alpha=False)
        pdfbytes = pix.pdfocr_tobytes(language="eng")
        d = fitz.open("pdf", pdfbytes)
        t = d[0].get_text() or ""
        d.close()
        return t
    except Exception:
        return ""


def _ocr_footer_text(page, zoom=7.0):
    """OCR the bottom strip where Greece hides the effective date."""
    r = page.rect
    footer = fitz.Rect(r.x0, r.y1 - r.height * 0.12, r.x1, r.y1)
    return _ocr_clip_text(page, footer, zoom=zoom)

def _ocr_header_text(page, zoom=7.0):
    """OCR the top strip where Greece puts the chart identity (AD ..-LGxx-..)."""
    r = page.rect
    header = fitz.Rect(r.x0, r.y0, r.x1, r.y0 + r.height * 0.12)
    return _ocr_clip_text(page, header, zoom=zoom)

def _ocr_corners_text(page, zoom=9.0):
    """
    High-res OCR of all FOUR corners + top/bottom strips.
    AIP charts always place the identity (top corners) and the effective date
    (bottom corners) in tiny text -> crop small + zoom big so Tesseract reads it.
    """
    r = page.rect
    w, h = r.width, r.height

    regions = [
        fitz.Rect(r.x0,              r.y0,              r.x1,              r.y0 + h * 0.10),  # full top strip
        fitz.Rect(r.x0,              r.y1 - h * 0.10,   r.x1,              r.y1),             # full bottom strip
        fitz.Rect(r.x0 + w * 0.45,   r.y0,              r.x1,              r.y0 + h * 0.10),  # top-right (identity)
        fitz.Rect(r.x0,              r.y0,              r.x0 + w * 0.55,   r.y0 + h * 0.10),  # top-left
        fitz.Rect(r.x0,              r.y1 - h * 0.10,   r.x0 + w * 0.55,   r.y1),             # bottom-left (date)
        fitz.Rect(r.x0 + w * 0.45,   r.y1 - h * 0.10,   r.x1,             r.y1),              # bottom-right (AIRAC)
    ]

    out = []
    for clip in regions:
        txt = _ocr_clip_text(page, clip, zoom=zoom)
        if txt.strip():
            out.append(txt)
    return "\n".join(out)

def _greece_owner(page_text):
    """
    Returns (icao, major) for a Greece chart/AD page.
    Identity forms: 'AD 2-LGxx', 'AD 1.6.29-LGxx', 'AD 2 LGxx-N', 'LGxx AD 2'.
    OCR-tolerant: accepts - . – — or spaces as the separator.
    Never a body cross-ref like 'see LGAD AD 2.18'.
    """
    t = compact_spaces(page_text)

    # hyphen identity: AD 2-LGAL / AD 1.6.29-LGTG  (OCR-tolerant separators)
    hyphen = re.findall(r"AD\s*(\d+)(?:\s*\.\s*\d+)*\s*[-–—.]\s*(LG[A-Z]{2})\b", t)
    if hyphen:
        icao = Counter(x[1].upper() for x in hyphen).most_common(1)[0][0]
        major = int(next(m for m, i in hyphen if i.upper() == icao))
        return icao, major

    # text footer form: AD 2 LGKF-4
    ad_first = re.findall(r"AD\s*(\d+)\s+(LG[A-Z]{2})\b", t)
    if ad_first:
        icao = Counter(x[1].upper() for x in ad_first).most_common(1)[0][0]
        major = int(next(m for m, i in ad_first if i.upper() == icao))
        return icao, major

    # icao-first form: LGKF AD 2
    icao_first = re.findall(r"(LG[A-Z]{2})\s+AD\s*(\d+)\b", t)
    if icao_first:
        icao = Counter(x[0].upper() for x in icao_first).most_common(1)[0][0]
        major = int(next(m for i, m in icao_first if i.upper() == icao))
        return icao, major

    return None, None


def _greece_section_detail(page, full_text, identity_text):
    # OWNER only from identity zone (header/footer/corners) — never body
    icao, major = _greece_owner(identity_text)
    if icao:
        return {
            "section": "AD", "major": major, "raw": f"AD {major} " + icao,
            "icao": icao, "owner_icaos": {icao}, "parser": f"Greece-AD{major}",
        }

    detail = extract_section_detail_from_page(page, full_text, "Universal")
    detail.setdefault("owner_icaos", set())

    # NEW: generic detector found an AD-2 airport owner (from the leakproof
    # title zone) -> promote it into owner_icaos so the master filter runs.
    gen_icao = detail.get("icao")
    if detail.get("section") == "AD" and detail.get("major") in (1, 2) and gen_icao:
        detail["owner_icaos"] = {str(gen_icao).strip().upper()}

    return detail


def process_pdf_greece(input_pdf_path, selected_date):
    """Greece-only pipeline. Returns the SAME 8-tuple as process_pdf()."""
    doc = fitz.open(input_pdf_path)
    total_pdf_pages = len(doc)
    allowed_icaos = load_master()

    st.session_state["greece_master_has_LG"] = sorted(
        [c for c in allowed_icaos if c.startswith("LG")]
    )

    temp_pages, auto_removed_pages, removed_page_details = [], [], []
    detected_ad_owners, kept_ad_owners, removed_ad_owners = set(), set(), set()
    ad_detection_details = []
    ocr_pages = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        text = page.get_text()                          # real text layer
        raw_len = len(text.strip())
        date_in_text = match_date_for_country(text, selected_date, "Greece")

        # identity ALWAYS from the clean header/footer zone (never body)
        zone_text = "\n".join(get_zone_lines(page))
        identity_text = zone_text

        zone_icao, _zm = _greece_owner(zone_text)
        zone_has_generic = bool(re.search(r"\b(GEN|ENR|AD)\b", compact_spaces(zone_text)))
        complete_text_page = (
            raw_len >= 30 and date_in_text and (zone_icao or zone_has_generic)
        )

        if raw_len < 30:
            # TRUE IMAGE chart -> identity + date come from corner OCR
            ocr_corners = _ocr_corners_text(page)
            if ocr_corners.strip():
                identity_text = identity_text + "\n" + ocr_corners   # identity OK here
                text = text + "\n" + ocr_corners
                ocr_pages.append(page_index + 1)

        elif not complete_text_page:
            # hybrid/text page missing date -> OCR feeds DATE ONLY, never identity
            ocr_corners = _ocr_corners_text(page)
            if ocr_corners.strip():
                text = text + "\n" + ocr_corners        # <-- NOT added to identity_text
                ocr_pages.append(page_index + 1)

        detail = _greece_section_detail(page, text, identity_text)
        

        section = detail["section"]
        owners = set(detail.get("owner_icaos") or set())

        if section == "AD" and detail.get("major") in (1, 2) and owners:
            detected_ad_owners.update(owners)
            ad_detection_details.append(
                {"page": page_index + 1, "icao": ", ".join(sorted(owners)),
                 "raw": detail.get("raw"), "parser": detail.get("parser")})

        if not section:
            removed_page_details.append(
                {"page": page_index + 1, "category": get_clean_removed_category(detail)})
            continue

        if is_auto_removed_section(detail):
            auto_removed_pages.append(
                {"page": page_index + 1, "section": detail["section"],
                 "major": detail["major"], "raw": detail["raw"]})
            removed_page_details.append(
                {"page": page_index + 1, "category": get_clean_removed_category(detail)})
            continue

        if not match_date_for_country(text, selected_date, "Greece"):
            removed_page_details.append(
                {"page": page_index + 1, "category": get_clean_removed_category(detail)})
            continue

        temp_pages.append((page_index, section, detail))

    final_pages = []
    for page_index, section, detail in temp_pages:
        major = detail.get("major")

        if section == "AD" and major in (1, 2):
            owners = set(detail.get("owner_icaos") or set())
            if not owners and detail.get("icao"):
                owners = {str(detail["icao"]).strip().upper()}

            if owners:
                matched = {i for i in owners if i in allowed_icaos}
                if matched:
                    kept_ad_owners.update(matched)
                    removed_ad_owners.update(owners - matched)
                else:
                    removed_ad_owners.update(owners)
                    removed_page_details.append(
                        {"page": page_index + 1,
                         "category": get_clean_removed_category(detail)})
                    continue

        final_pages.append((page_index, section, major))

    doc.close()

    # stash OCR page list for the side panel (Greece-only, harmless elsewhere)
    st.session_state["greece_ocr_pages"] = ocr_pages

    return (total_pdf_pages, final_pages, detected_ad_owners, kept_ad_owners,
            removed_ad_owners, auto_removed_pages, removed_page_details,
            ad_detection_details)


# =============================
# SESSION STATE INIT
# =============================
default_state = {
    "pages": [],
    "total_pdf_pages": 0,
    "detected_ad_owners": set(),
    "kept": set(),
    "removed": set(),
    "ad_detection_details": [],
    "auto_removed_pages": [],
    "removed_page_details": [],
    "preview_limit": 10,
    "last_preview_signature": None,
    "processed": False,
    "input_pdf_path": None,
    "output_pdf_path": None,
    "output_page_count": 0,
    "last_selection_signature": None,
    "selection_initialized": False,
    "enr_subsection_keys": [],
    "ad_subsection_keys": [],
    "processed_country": None
}

for key, value in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =============================
# UI
# =============================
st.markdown(
    """
    <div class="hero">
        <div class="hero-badge">✈️</div>
        <div>
            <h1>AIP Trimmer</h1>
            <p>Parse, filter and trim national AIP amendments down to only the pages that matter.</p>
        </div>
        <div class="hero-chip">CAE · AVIATION DATA AUTOMATION</div>
    </div>
    """,
    unsafe_allow_html=True
)

def sec_label(num, text):
    st.markdown(
        f'<div class="sec-label"><span class="sec-num">{num}</span>{text}</div>',
        unsafe_allow_html=True
    )

sec_label(1, "Parser profile")

def kpi_card(title, value, icon="📄", tone="blue", sub="", pct=100):
    st.markdown(
        f"""
        <div class="kpi-card kpi-{tone}">
            <div class="kpi-top">
                <span class="kpi-icon">{icon}</span>
                <span class="kpi-label">{title}</span>
            </div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-bar"><span style="width:{max(0, min(100, pct))}%"></span></div>
            <div class="kpi-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def icao_chips(codes, color="#34D399", empty="None", limit=60):
    codes = list(codes or [])
    if not codes:
        st.markdown(f'<div class="src-note">{empty}</div>', unsafe_allow_html=True)
        return
    shown = codes[:limit]
    chips = "".join(
        f'<span class="icao-chip" style="background:{color}22;'
        f'border:1px solid {color}55;color:{color};">{c}</span>'
        for c in shown
    )
    extra = (
        f'<span class="icao-chip" style="background:rgba(255,255,255,.07);'
        f'border:1px solid rgba(255,255,255,.16);color:#93A3C4;">'
        f'+{len(codes) - len(shown)} more</span>'
        if len(codes) > len(shown) else ""
    )
    st.markdown(f'<div class="chip-row">{chips}{extra}</div>', unsafe_allow_html=True)

country = st.selectbox(
    "Select Country / Parser Profile",
    COUNTRY_OPTIONS,
    index=0
)

if country == "Russia":
    sec_label(2, "Russia · automated source")

    with st.container(border=True):
        st.markdown(
            '<div class="src-note">Reads <b>caica.ru</b> directly — no upload needed. '
            'Keeps <b>AD 2</b> volumes 1–3 whose ICAO is in the master list, plus '
            '<b>ENR 1.11 / 3.1 / 3.2</b> and their subsections, then merges everything '
            'into a single PDF.</div>',
            unsafe_allow_html=True
        )

        if st.button("🚀 Fetch & merge Russia", type="primary", use_container_width=True):
            cleanup_existing_pdf_files()
            out_path = make_temp_pdf_path("russia_merged")

            with st.spinner("Reading AMDT list, downloading & merging…"):
                mp, kept, skipped, enr_kept, failed, debug = process_russia_auto(out_path)

            if not (kept or enr_kept):
                mp = None

            st.session_state.update({
                "input_pdf_path": mp, "output_pdf_path": mp,
                "processed_country": "Russia", "processed": True,
                "ru_kept": kept or [], "ru_skipped": skipped or [],
                "ru_enr": enr_kept or [], "ru_failed": failed or [],
            })

    if st.session_state.get("processed_country") == "Russia":
        kept     = st.session_state.get("ru_kept", []) or []
        enr_kept = st.session_state.get("ru_enr", []) or []
        skipped  = st.session_state.get("ru_skipped", []) or []
        failed   = st.session_state.get("ru_failed", []) or []
        mp       = st.session_state.get("output_pdf_path")

        if kept or enr_kept:
            detected = len(kept) + len(skipped)
            kept_pct = round(len(kept) / detected * 100) if detected else 0

            sec_label(3, "Results overview")
            c1, c2, c3 = st.columns(3)
            with c1:
                kpi_card("AD 2 airports", len(kept), "🛫", "green",
                         f"{kept_pct}% of {detected} detected ICAOs", kept_pct)
            with c2:
                kpi_card("ENR files", len(enr_kept), "🗺️", "blue",
                         "ENR 1.11 / 3.1 / 3.2 and subsections", 100)
            with c3:
                kpi_card("Skipped", len(skipped), "🚫", "amber",
                         "ICAOs not in the master list", 100 - kept_pct)

            sec_label(4, "Merged output")
            with st.container(border=True):
                st.markdown("**AD 2 airports kept**")
                icao_chips(kept, "#34D399")
                st.markdown("**ENR files kept**")
                icao_chips(enr_kept, "#A78BFA")

                if mp and os.path.exists(mp):
                    st.caption(f"Merged file: {get_file_size_mb(mp):.2f} MB")
                    with open(mp, "rb") as f:
                        st.download_button("⬇ Download merged Russia PDF", f,
                                           file_name="Russia_merged.pdf",
                                           mime="application/pdf",
                                           use_container_width=True)
        else:
            st.warning("Nothing matched — none of the detected AD 2 ICAOs are in the master list.")

        if skipped:
            with st.expander(f"🚫 Skipped — not in master list ({len(skipped)})"):
                icao_chips(skipped, "#F59E0B", limit=400)

        if failed:
            with st.expander(f"⚠️ Failed downloads ({len(failed)})"):
                for tag, reason in failed[:40]:
                    st.write(f"`{tag}` — {reason}")

    st.stop()

if country == "Argentina":
    sec_label(2, "Argentina (ANAC) · automated source")

    with st.container(border=True):
        st.markdown(
            '<div class="src-note">Reads <b>ais.anac.gob.ar/amdt</b> and picks the latest '
            'amendment automatically. Keeps <b>GEN 0.1</b>, <b>ENR 1.11</b>, <b>ENR 3.1</b>, '
            '<b>ENR 3.2</b> and <b>AD 2</b> airports in the master list. Section codes are '
            'language-independent, so no translation is needed.</div>',
            unsafe_allow_html=True
        )

        if st.button("🚀 Fetch & merge Argentina", type="primary", use_container_width=True):
            cleanup_existing_pdf_files()
            out_path = make_temp_pdf_path("argentina_merged")

            with st.spinner("Reading AMDT list, downloading & merging…"):
                mp, kept_ad, kept_sec, skipped, failed, debug = process_argentina_auto(out_path)

            if not (kept_ad or kept_sec):
                mp = None

            st.session_state.update({
                "input_pdf_path": mp, "output_pdf_path": mp,
                "processed_country": "Argentina", "processed": True,
                "ar_kept_ad": kept_ad or [], "ar_kept_sec": kept_sec or [],
                "ar_skipped": skipped or [], "ar_amdt": debug.get("amdt_label", ""),
                "ar_links": debug.get("links_found", 0),
                "ar_missing": debug.get("sections_missing", []),
                "ar_failed": failed or [],
            })

    if st.session_state.get("processed_country") == "Argentina":
        kept_ad  = st.session_state.get("ar_kept_ad", []) or []
        kept_sec = st.session_state.get("ar_kept_sec", []) or []
        skipped  = st.session_state.get("ar_skipped", []) or []
        missing  = st.session_state.get("ar_missing", []) or []
        failed   = st.session_state.get("ar_failed", []) or []
        mp       = st.session_state.get("output_pdf_path")
        amdt     = st.session_state.get("ar_amdt", "")

        if kept_ad or kept_sec:
            detected = len(kept_ad) + len(skipped)
            kept_pct = round(len(kept_ad) / detected * 100) if detected else 0

            sec_label(3, "Results overview")
            if amdt:
                st.markdown(f'<span class="amdt-tag">{amdt}</span>', unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            with c1:
                kpi_card("AD 2 airports", len(kept_ad), "🛫", "green",
                         f"{kept_pct}% of {detected} detected ICAOs", kept_pct)
            with c2:
                kpi_card("Sections", len(kept_sec), "📑", "blue",
                         "GEN 0.1 · ENR 1.11 / 3.1 / 3.2", 100)
            with c3:
                kpi_card("Skipped", len(skipped), "🚫", "amber",
                         "ICAOs not in the master list", 100 - kept_pct)

            sec_label(4, "Merged output")
            with st.container(border=True):
                st.markdown("**AD 2 airports kept**")
                icao_chips(kept_ad, "#34D399")
                st.markdown("**Sections kept**")
                icao_chips(kept_sec, "#60A5FA")

                if missing:
                    st.caption("Requested sections not present in this AMDT: " + ", ".join(missing))

                if mp and os.path.exists(mp):
                    st.caption(f"Merged file: {get_file_size_mb(mp):.2f} MB")
                    with open(mp, "rb") as f:
                        st.download_button("⬇ Download full merged Argentina PDF", f,
                                           file_name="Argentina_merged.pdf",
                                           mime="application/pdf",
                                           use_container_width=True)

            # ---- Stage 2: filter the merged PDF by effective date ----
            sec_label(5, "Trim to a single effective date")

            with st.container(border=True):
                st.markdown(
                    '<div class="src-note">This AMDT mixes several effective dates. '
                    'Argentina prints the date at the <b>bottom of each page in Spanish</b> '
                    '(e.g. <b>11 JUNIO 2026</b>) — all months ENERO…DICIEMBRE are supported.</div>',
                    unsafe_allow_html=True
                )

                fc1, fc2 = st.columns([1, 1])
                with fc1:
                    ar_date = st.date_input("Effective date", key="ar_filter_date")
                with fc2:
                    st.markdown("<div style='height:27px'></div>", unsafe_allow_html=True)
                    filter_clicked = st.button("✂️ Filter merged PDF by date",
                                               use_container_width=True)

                if filter_clicked:
                    if mp and os.path.exists(mp):
                        out_path = make_temp_pdf_path("argentina_filtered")
                        ok, kept_pages = filter_merged_pdf_by_date(
                            mp, ar_date.strftime("%d %b %Y"),
                            out_path, match_date_argentina
                        )
                        st.session_state["ar_filtered_path"] = out_path if ok else None
                        st.session_state["ar_filtered_pages"] = kept_pages
                        st.session_state["ar_filtered_date"] = ar_date.strftime("%d %b %Y")
                    else:
                        st.warning("Merged PDF not found. Fetch & merge again first.")

                fpath  = st.session_state.get("ar_filtered_path")
                fpages = st.session_state.get("ar_filtered_pages", [])
                fdate  = st.session_state.get("ar_filtered_date", "")

                if fpath and os.path.exists(fpath):
                    st.success(f"{len(fpages)} page(s) match {fdate}.")
                    with open(fpath, "rb") as f:
                        st.download_button("⬇ Download date-filtered PDF", f,
                                           file_name=f"Argentina_{fdate.replace(' ', '')}.pdf",
                                           mime="application/pdf",
                                           use_container_width=True)
                elif st.session_state.get("ar_filtered_date"):
                    st.warning(f"No pages matched {fdate}. Double-check the date — "
                               "Spanish month names are supported (ENERO…DICIEMBRE).")
        else:
            st.warning(f"Nothing matched. (links found on page: "
                       f"{st.session_state.get('ar_links', 0)})")

        if skipped:
            with st.expander(f"🚫 Skipped AD 2 — not in master list ({len(skipped)})"):
                icao_chips(skipped, "#F59E0B", limit=400)

        if failed:
            with st.expander(f"⚠️ Failed downloads ({len(failed)})"):
                for tag, reason in failed[:40]:
                    st.write(f"`{tag}` — {reason}")

    st.stop()

if country == "Australia (ERSA)":
    sec_label(2, "Australia (ERSA) · automated source")

    with st.container(border=True):
        st.markdown(
            '<div class="src-note">ERSA publishes one <b>FAC_&lt;ICAO&gt;_&lt;DATE&gt;.pdf</b> '
            'per aerodrome, so the ICAO comes straight from the filename. The tool filters '
            'against the master list, downloads the matches and merges them — no upload '
            'needed. Cycles are detected automatically and roll over on their own.</div>',
            unsafe_allow_html=True
        )

        cycles = get_ersa_cycles()

        def _pretty(c):
            try:
                return datetime.strptime(c, "%d%b%Y").strftime("%d %b %Y").upper()
            except Exception:
                return c

        cy1, cy2 = st.columns([2, 1])

        with cy1:
            if cycles:
                labels = {
                    c: (f"{_pretty(c)}  ·  current" if i == 0 else f"{_pretty(c)}  ·  next")
                    for i, c in enumerate(cycles)
                }
                cycle = st.selectbox(
                    "ERSA cycle (auto-detected)",
                    cycles,
                    format_func=lambda c: labels.get(c, _pretty(c)),
                )
            else:
                st.warning("Couldn't auto-detect the cycle — enter it manually, e.g. 09JUL2026.")
                cycle = st.text_input("ERSA cycle", value="")

        cycle = re.sub(r"\s+", "", str(cycle)).upper()

        with cy2:
            st.markdown("<div style='height:27px'></div>", unsafe_allow_html=True)
            fetch_clicked = st.button("🚀 Fetch & merge ERSA",
                                      type="primary", use_container_width=True)

    if fetch_clicked:
        cleanup_existing_pdf_files()
        out_path = make_temp_pdf_path("ersa_merged")

        with st.spinner("Downloading & merging ERSA aerodromes…"):
            merged_path, kept, skipped, failed = process_australia_ersa(cycle, out_path)

        st.session_state.update({
            "input_pdf_path": merged_path,
            "output_pdf_path": merged_path,
            "processed_country": "Australia",
            "processed": True,
            "au_kept": kept,
            "au_skipped": skipped,
            "au_failed": failed,
            "au_cycle": cycle,
        })

    if (st.session_state.get("processed_country") == "Australia"
            and st.session_state.get("output_pdf_path")):
        kept        = st.session_state.get("au_kept", []) or []
        skipped     = st.session_state.get("au_skipped", []) or []
        failed      = st.session_state.get("au_failed", []) or []
        merged_path = st.session_state["output_pdf_path"]

        if kept:
            detected = len(kept) + len(skipped)
            kept_pct = round(len(kept) / detected * 100) if detected else 0

            sec_label(3, "Results overview")
            st.markdown(
                f'<span class="amdt-tag">ERSA cycle '
                f'{_pretty(st.session_state.get("au_cycle", ""))}</span>',
                unsafe_allow_html=True
            )

            c1, c2, c3 = st.columns(3)
            with c1:
                kpi_card("Aerodromes merged", len(kept), "🛫", "green",
                         f"{kept_pct}% of {detected} published", kept_pct)
            with c2:
                kpi_card("Skipped", len(skipped), "🚫", "blue",
                         "Not in the master list", 100 - kept_pct)
            with c3:
                kpi_card("Failed", len(failed), "⚠️", "amber",
                         "Download or terms-gate errors",
                         round(len(failed) / detected * 100) if detected else 0)

            sec_label(4, "Merged output")
            with st.container(border=True):
                st.markdown("**Aerodromes kept**")
                icao_chips(kept, "#34D399")

                if os.path.exists(merged_path):
                    st.caption(f"Merged file: {get_file_size_mb(merged_path):.2f} MB")
                    with open(merged_path, "rb") as f:
                        st.download_button(
                            "⬇ Download merged ERSA PDF", f,
                            file_name=f"ERSA_merged_{st.session_state.get('au_cycle','')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
        else:
            st.error("No aerodromes were merged — the terms gate most likely blocked the "
                     "downloads. Check the failure details below.")

        if skipped:
            with st.expander(f"🚫 Skipped — not in master list ({len(skipped)})"):
                icao_chips(skipped, "#F59E0B", limit=400)

        if failed:
            with st.expander(f"⚠️ Failed downloads ({len(failed)})"):
                for tag, reason in failed[:40]:
                    st.write(f"`{tag}` — {reason}")

    st.stop()

sec_label(2, "Source document & effective date")

with st.container(border=True):
    up_col, date_col = st.columns([2, 1])
    with up_col:
        file = st.file_uploader(
            "Upload AIP amendment PDF",
            type=["pdf"],
            help="Drop the full AMDT PDF here — GEN / ENR / AD pages are detected automatically."
        )
    with date_col:
        date = st.date_input("Effective date (AIRAC)")
        if file is not None:
            st.caption(f"📄 {file.name}")


# =============================
# RUN PARSER
# =============================
if file:
    if st.button("🚀 Parse document", type="primary", use_container_width=True):
        st.session_state.preview_limit = 10
        st.session_state.last_preview_signature = None
        st.session_state.selection_initialized = False
        st.session_state.last_selection_signature = None
        st.session_state.output_page_count = 0

        for key in list(st.session_state.keys()):
            if isinstance(key, str) and key.startswith("toggle_"):
                del st.session_state[key]

        cleanup_existing_pdf_files()

        input_pdf_path = save_uploaded_pdf_to_disk(file)

        with st.spinner("Processing AIP… please wait"):
            if country == "Chile":
                (
                    total_pdf_pages, pages, detected_ad_owners, kept, removed,
                    auto_removed_pages, removed_page_details, ad_detection_details
                ) = process_pdf_chile(
                    input_pdf_path,
                    date.strftime("%d %b %Y")
                )
            elif country == "Greece":
                (
                    total_pdf_pages, pages, detected_ad_owners, kept, removed,
                    auto_removed_pages, removed_page_details, ad_detection_details
                ) = process_pdf_greece(
                    input_pdf_path,
                    date.strftime("%d %b %Y")
                )
            elif country == "Paraguay":
                (
                    total_pdf_pages, pages, detected_ad_owners, kept, removed,
                    auto_removed_pages, removed_page_details, ad_detection_details
                ) = process_pdf_paraguay(
                    input_pdf_path,
                    date.strftime("%d %b %Y")
                )
            else:
                (
                    total_pdf_pages, pages, detected_ad_owners, kept, removed,
                    auto_removed_pages, removed_page_details, ad_detection_details
                ) = process_pdf(
                    input_pdf_path,
                    date.strftime("%d %b %Y"),
                    country
                )

        st.session_state.update(
            {
                "input_pdf_path": input_pdf_path,
                "output_pdf_path": None,
                "output_page_count": 0,
                "last_selection_signature": None,
                "processed_country": country,
                "total_pdf_pages": total_pdf_pages,
                "pages": pages,
                "detected_ad_owners": detected_ad_owners,
                "kept": kept,
                "removed": removed,
                "ad_detection_details": ad_detection_details,
                "auto_removed_pages": auto_removed_pages,
                "removed_page_details": removed_page_details,
                "processed": True
            }
        )


# =============================
# DISPLAY RESULT
# =============================
if st.session_state.processed:
    pages = st.session_state.pages
    total_pdf_pages = st.session_state.total_pdf_pages
    extracted_pages = len(pages)
    removed_pages = max(total_pdf_pages - extracted_pages, 0)

    present_sections = {
        get_page_section(page)
        for page in pages
        if get_page_section(page)
    }

    present_enr_majors = sorted(
        {
            get_page_major(page)
            for page in pages
            if get_page_section(page) == "ENR" and get_page_major(page) is not None
        }
    )

    enr_subsection_keys = [
        f"toggle_ENR_{major}"
        for major in present_enr_majors
    ]
    present_ad_majors = sorted(
        {
            get_page_major(page)
            for page in pages
            if get_page_section(page) == "AD" and get_page_major(page) is not None
        }
    )

    ad_subsection_keys = [
        f"toggle_AD_{major}"
        for major in present_ad_majors
    ]

    if not st.session_state.selection_initialized:
        st.session_state["toggle_GEN"] = True
        st.session_state["toggle_ENR"] = True
        st.session_state["toggle_AD"] = True

        for key in list(st.session_state.keys()):
            if isinstance(key, str) and (
                key.startswith("toggle_ENR_") or key.startswith("toggle_AD_")
            ):
                del st.session_state[key]

        for major in present_enr_majors:
            st.session_state[f"toggle_ENR_{major}"] = True

        for major in present_ad_majors:
            st.session_state[f"toggle_AD_{major}"] = True

        st.session_state.enr_subsection_keys = enr_subsection_keys
        st.session_state.ad_subsection_keys = ad_subsection_keys
        st.session_state.selection_initialized = True
    else:
        st.session_state.enr_subsection_keys = enr_subsection_keys
        st.session_state.ad_subsection_keys = ad_subsection_keys

        for major in present_enr_majors:
            key = f"toggle_ENR_{major}"
            if key not in st.session_state:
                st.session_state[key] = True

        for major in present_ad_majors:
            key = f"toggle_AD_{major}"
            if key not in st.session_state:
                st.session_state[key] = True

    def card(title, value, icon="📄", tone="blue", sub="", pct=100):
        st.markdown(
            f"""
            <div class="kpi-card kpi-{tone}">
                <div class="kpi-top">
                    <span class="kpi-icon">{icon}</span>
                    <span class="kpi-label">{title}</span>
                </div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-bar"><span style="width:{max(0, min(100, pct))}%"></span></div>
                <div class="kpi-sub">{sub}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    kept_pct = round((extracted_pages / total_pdf_pages) * 100) if total_pdf_pages else 0
    removed_pct = 100 - kept_pct

    sec_label(3, "Results overview")

    c1, c2, c3 = st.columns(3)
    with c1:
        card("Total pages", total_pdf_pages, "📚", "blue", "Pages found in the source PDF", 100)
    with c2:
        card("Extracted", extracted_pages, "✅", "green", f"{kept_pct}% of the document retained", kept_pct)
    with c3:
        card("Removed", removed_pages, "🗑️", "amber", f"{removed_pct}% filtered out", removed_pct)

    sec_label(4, "Section filters")

    selected_sections = []
    selected_enr_majors = set()
    selected_ad_majors = set()

    if "GEN" in present_sections:
        if st.toggle("GEN", key="toggle_GEN"):
            selected_sections.append("GEN")

    if "ENR" in present_sections:
        if st.toggle(
            "ENR",
            key="toggle_ENR",
            on_change=sync_enr_subsections
        ):
            selected_sections.append("ENR")

            if present_enr_majors:
                st.markdown(
                    """
                    <div class="enr-subsection-title">ENR Major Sections</div>
                    """,
                    unsafe_allow_html=True
                )

                for major in present_enr_majors:
                    sub_key = f"toggle_ENR_{major}"

                    sub_col_space, sub_col_toggle = st.columns([0.04, 0.96])

                    with sub_col_toggle:
                        if st.toggle(
                            f"ENR {major}",
                            key=sub_key
                        ):
                            selected_enr_majors.add(major)

    if "AD" in present_sections:
        if st.toggle(
            "AD",
            key="toggle_AD",
            on_change=sync_ad_subsections
        ):
            selected_sections.append("AD")

            if present_ad_majors:
                st.markdown(
                    """
                    <div class="enr-subsection-title">AD Major Sections</div>
                    """,
                    unsafe_allow_html=True
                )

                for major in present_ad_majors:
                    sub_key = f"toggle_AD_{major}"

                    sub_col_space, sub_col_toggle = st.columns([0.04, 0.96])

                    with sub_col_toggle:
                        if st.toggle(
                            f"AD {major}",
                            key=sub_key
                        ):
                            selected_ad_majors.add(major)
                        
    if not selected_sections:
        st.stop()

    if "ENR" in selected_sections and not selected_enr_majors:
        selected_sections = [
            section
            for section in selected_sections
            if section != "ENR"
        ]
    if "AD" in selected_sections and not selected_ad_majors:
        selected_sections = [
            section
            for section in selected_sections
            if section != "AD"
        ]
    
    if not selected_sections:
        st.stop()

    selection_signature = get_selection_signature(
        selected_sections,
        selected_enr_majors,
        selected_ad_majors,
        st.session_state.processed_country
    )

    selected_page_tuples = get_selected_page_tuples(
        pages=pages,
        selected_sections=selected_sections,
        selected_enr_majors=selected_enr_majors,
        selected_ad_majors=selected_ad_majors
    )

    if not selected_page_tuples:
        st.warning("No pages available for the selected section filters.")
        st.stop()

    selected_preview_indexes = [
        get_page_index(page_tuple)
        for page_tuple in selected_page_tuples
        if get_page_index(page_tuple) is not None
    ]

    preview_signature = get_preview_signature(
        selected_preview_indexes,
        selection_signature
    )

    if st.session_state.last_preview_signature != preview_signature:
        st.session_state.preview_limit = 10
        st.session_state.last_preview_signature = preview_signature

    if st.session_state.last_selection_signature != selection_signature:
        safe_remove_file(st.session_state.get("output_pdf_path"))
        st.session_state.output_pdf_path = None
        st.session_state.output_page_count = 0
        st.session_state.last_selection_signature = None

    col_left, col_right = st.columns([3, 1])

    # =============================
    # PREVIEW FROM ORIGINAL PDF
    # =============================
    # ---------- preview grid helpers ----------
    SECTION_COLORS = {
        "GEN": ("#60A5FA", "#93C5FD"),
        "ENR": ("#A78BFA", "#C4B5FD"),
        "AD":  ("#34D399", "#6EE7B7"),
    }

    icao_by_page = {
        item["page"]: item["icao"]
        for item in st.session_state.get("ad_detection_details", [])
        if item.get("icao")
    }

    meta_by_index = {
        get_page_index(pt): (get_page_section(pt), get_page_major(pt))
        for pt in selected_page_tuples
        if get_page_index(pt) is not None
    }

    def page_label(page_index, section, major):
        if section == "AD" and major == 2:
            icao = icao_by_page.get(page_index + 1)
            if icao:
                return f"AD 2.{icao}"
        if section and major is not None:
            return f"{section} {major}"
        return section or "Page"

    with col_left:
        st.markdown('<div class="sec-label">Preview</div>', unsafe_allow_html=True)

        total_preview_pages = len(selected_preview_indexes)
        limit = st.session_state.preview_limit
        shown_indexes = selected_preview_indexes[:min(limit, total_preview_pages)]

        # ----- toolbar -----
        with st.container(border=True):
            t1, t2, t3 = st.columns([1.1, 1.5, 1.4])

            with t1:
                try:
                    view_mode = st.segmented_control(
                        "View", ["Grid", "Single"],
                        default="Grid", label_visibility="collapsed"
                    ) or "Grid"
                except Exception:
                    view_mode = st.radio(
                        "View", ["Grid", "Single"],
                        horizontal=True, label_visibility="collapsed"
                    )

            with t2:
                zoom = st.slider("Zoom", 0.5, 2.5, 1.0, 0.1, label_visibility="collapsed")

            with t3:
                present = sorted(
                    {s for s, _ in meta_by_index.values() if s},
                    key=lambda x: ["GEN", "ENR", "AD"].index(x) if x in ("GEN", "ENR", "AD") else 9
                )
                chips = "".join(
                    f'<span class="chip" style="background:{SECTION_COLORS.get(s, ("#64748B", "#94A3B8"))[0]}26;'
                    f'border:1px solid {SECTION_COLORS.get(s, ("#64748B", "#94A3B8"))[0]}6E;'
                    f'color:{SECTION_COLORS.get(s, ("#64748B", "#94A3B8"))[0]};">'
                    f'<i style="background:{SECTION_COLORS.get(s, ("#64748B", "#94A3B8"))[0]}"></i>{s}</span>'
                    for s in present
                )
                st.markdown(
                    f'<div class="chip-row">{chips}'
                    f'<span class="count-chip"><b>{len(shown_indexes)}</b> '
                    f'of {total_preview_pages} pages shown</span></div>',
                    unsafe_allow_html=True
                )

        st.progress(
            len(shown_indexes) / total_preview_pages if total_preview_pages else 0.0
        )

        # ----- render -----
        file_mtime = get_file_mtime(st.session_state.input_pdf_path)

        if view_mode == "Single":
            render_scale = 1.2 if total_preview_pages > 100 else 2.0

            for page_index in shown_indexes:
                section, major = meta_by_index.get(page_index, (None, None))
                c1c, c2c = SECTION_COLORS.get(section, ("#64748B", "#94A3B8"))

                with st.container(border=True):
                    st.markdown(
                        f'<div class="pg-head" style="background:{c1c}22;'
                        f'border-bottom:1px solid {c1c}55;">'
                        f'<span class="pg-pill">{page_index + 1}</span>'
                        f'<span class="pg-code" style="color:{c2c};">'
                        f'{page_label(page_index, section, major)}</span></div>',
                        unsafe_allow_html=True
                    )
                    st.image(
                        render_preview_page(
                            st.session_state.input_pdf_path,
                            page_index, render_scale, file_mtime
                        ),
                        width=int(700 * zoom)
                    )

        else:
            # zoom controls how many cards fit per row
            if zoom <= 0.7:
                cols_n = 5
            elif zoom <= 1.3:
                cols_n = 4
            elif zoom <= 1.9:
                cols_n = 3
            else:
                cols_n = 2

            thumb_scale = 1.0 if total_preview_pages > 60 else 1.4

            for row_start in range(0, len(shown_indexes), cols_n):
                row_cols = st.columns(cols_n, gap="medium")
                row_pages = shown_indexes[row_start:row_start + cols_n]

                for slot, page_index in enumerate(row_pages):
                    section, major = meta_by_index.get(page_index, (None, None))
                    c1c, c2c = SECTION_COLORS.get(section, ("#64748B", "#94A3B8"))

                    with row_cols[slot]:
                        with st.container(border=True):
                            st.markdown(
                                f'<div class="pg-head" style="background:{c1c}22;'
                                f'border-bottom:1px solid {c1c}55;">'
                                f'<span class="pg-pill">{page_index + 1}</span>'
                                f'<span class="pg-code" style="color:{c2c};">'
                                f'{page_label(page_index, section, major)}</span></div>',
                                unsafe_allow_html=True
                            )
                            st.image(
                                render_preview_page(
                                    st.session_state.input_pdf_path,
                                    page_index, thumb_scale, file_mtime
                                ),
                                use_container_width=True
                            )

        # ----- load more -----
        if limit < total_preview_pages:
            remaining = total_preview_pages - limit
            st.button(
                f"⬇ Load {min(10, remaining)} more pages",
                key="load_more_pages_button",
                on_click=load_more_preview_pages,
                use_container_width=True
            )
            st.caption(
                f"{len(shown_indexes)} of {total_preview_pages} selected pages shown "
                f"· {remaining} remaining"
            )
        else:
            st.caption(f"All {total_preview_pages} selected pages shown")

    # =============================
    # SIDE PANEL
    # =============================
    with col_right:
        st.markdown('<div class="sec-label">Output</div>', unsafe_allow_html=True)

        st.caption(
            f"Parser profile: {st.session_state.processed_country}"
        )
        if st.session_state.processed_country == "Greece":
            ocr_pages = st.session_state.get("greece_ocr_pages", [])
            if ocr_pages:
                st.caption(f"🔍 OCR used on {len(ocr_pages)} page(s): "
                           f"{', '.join(map(str, ocr_pages[:20]))}"
                           f"{' …' if len(ocr_pages) > 20 else ''}")
        if st.session_state.processed_country == "Greece":
            st.caption(f"LG codes in master: {st.session_state.get('greece_master_has_LG', [])}")
        detected_ad_owners = st.session_state.get("detected_ad_owners", set())
        kept_ad_owners = st.session_state.get("kept", set())
        removed_ad_owners = st.session_state.get("removed", set())

        if st.session_state.processed_country in GROUP_PROFILES:
            st.info(
                "Group profile active: this parser checks all detected airport ICAOs against the full master airport list."
            )

        if detected_ad_owners and not kept_ad_owners:
            st.warning(
                "AD pages were detected, but all were removed because their ICAO codes are not in the master airport list."
            )

        if detected_ad_owners:
            with st.expander("AD Airport Diagnostics"):
                st.write(
                    f"Detected AD owner ICAOs: {', '.join(sorted(detected_ad_owners))}"
                )
                st.write(
                    f"Kept AD owner ICAOs: {', '.join(sorted(kept_ad_owners)) if kept_ad_owners else 'None'}"
                )
                st.write(
                    f"Removed AD owner ICAOs: {', '.join(sorted(removed_ad_owners)) if removed_ad_owners else 'None'}"
                )

                details = st.session_state.get("ad_detection_details", [])

                if details:
                    st.markdown("#### First detected AD titles")
                    for item in details[:25]:
                        st.write(
                            f"Page {item['page']}: {item['icao']} | {item['raw']} | {item['parser']}"
                        )
                if st.session_state.processed_country == "Paraguay":
                    st.write("AD 2.N → ICAO map:",
                             st.session_state.get("py_group_map", {}))
        st.caption(
            f"Selected for output: {len(selected_page_tuples)} page(s)"
        )

        prepare_clicked = st.button("⚙️ Prepare download", use_container_width=True)

        if prepare_clicked:
            with st.spinner("Preparing trimmed PDF..."):
                prepare_output_pdf(
                    selected_page_tuples=selected_page_tuples,
                    selection_signature=selection_signature
                )

        output_pdf_path = st.session_state.get("output_pdf_path")
        output_page_count = st.session_state.get("output_page_count", 0)

        if (
            output_pdf_path
            and os.path.exists(output_pdf_path)
            and st.session_state.get("last_selection_signature") == selection_signature
        ):
            output_size_mb = get_file_size_mb(output_pdf_path)

            st.caption(
                f"Output ready: {output_page_count} page(s), {output_size_mb:.2f} MB"
            )

            with open(output_pdf_path, "rb") as download_file:
                st.download_button(
                    label="⬇ Download trimmed PDF",
                    data=download_file,
                    file_name="trimmed_aip.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        else:
            st.caption("Click Prepare Download after finalizing section filters.")

        st.markdown("---")
        st.markdown("### Removed Pages Details")

        if st.session_state.removed_page_details:
            removed_counter = Counter(
                [
                    item["category"]
                    for item in st.session_state.removed_page_details
                ]
            )

            displayed_removed_total = 0

            def removed_sort_key(item):
                category = item[0]

                match = re.match(r"^(GEN|ENR|AD)\s+(\d+)$", category)

                if match:
                    section_order = {
                        "GEN": 1,
                        "ENR": 2,
                        "AD": 3
                    }

                    return (
                        section_order.get(match.group(1), 9),
                        int(match.group(2)),
                        category
                    )

                if category == "Other / Unrecognized Pages":
                    return (99, 99, category)

                return (50, 50, category)

            for category, count in sorted(removed_counter.items(), key=removed_sort_key):
                displayed_removed_total += count
                st.write(f"{category}: {count} page(s)")

            if displayed_removed_total != removed_pages:
                st.markdown("---")
                st.warning(
                    f"Removed page mismatch detected: tile shows {removed_pages}, "
                    f"details show {displayed_removed_total}."
                )
        else:
            st.write("No removed pages found")

        st.caption("AIP Trimmer · CAE Aviation Data Automation")
          