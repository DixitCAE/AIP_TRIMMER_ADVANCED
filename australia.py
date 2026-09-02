import re
import requests
import fitz  # PyMuPDF
import pandas as pd
from io import BytesIO

MASTER_URL = "https://raw.githubusercontent.com/DixitCAE/PDF_PARSER/main/master_airport_list.csv"
BASE = "https://www.airservicesaustralia.com"
CYCLE_DATE = "09JUL2026"            # or "03SEP2026"
INDEX_URL = f"{BASE}/aip/aip.asp?pg=40&vdate={CYCLE_DATE}&ver=1"

def load_master():
    df = pd.read_csv(MASTER_URL, header=None)
    return set(df[0].dropna().astype(str).str.strip().str.upper())

def get_fac_links(session, cycle_date):
    html = session.get(INDEX_URL, timeout=30).text
    # matches FAC_YABR_09JUL2026.pdf and FAC_BML_09JUL2026.pdf (3- or 4-char codes)
    rel = re.findall(rf'(/aip/current/ersa/FAC_([A-Z0-9]{{3,4}})_{cycle_date}\.pdf)', html)
    # de-dup, keep (url, icao)
    seen, out = set(), []
    for path, code in rel:
        if path not in seen:
            seen.add(path)
            out.append((BASE + path, code.upper()))
    return out

def build_australia_pdf(cycle_date=CYCLE_DATE, out_path="ERSA_merged.pdf"):
    master = load_master()
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0", "Referer": INDEX_URL})

    # 1) accept the terms gate once (sets the session cookie)
    s.get(f"{BASE}/aip/aip.asp", timeout=30)

    links = get_fac_links(s, cycle_date)
    wanted = [(u, i) for (u, i) in links if i in master]

    merged = fitz.open()
    kept, skipped_notmaster = [], [i for (_, i) in links if i not in master]
    failed = []

    for url, icao in wanted:
        try:
            r = s.get(url, timeout=60)
            if r.headers.get("content-type", "").lower().startswith("application/pdf"):
                doc = fitz.open("pdf", BytesIO(r.content))
                merged.insert_pdf(doc)
                doc.close()
                kept.append(icao)
            else:
                failed.append((icao, "not a PDF (terms gate?)"))
        except Exception as e:
            failed.append((icao, str(e)))

    if merged.page_count:
        merged.save(out_path, garbage=4, deflate=True)
    merged.close()

    print(f"Total FAC on page : {len(links)}")
    print(f"In master / kept  : {len(kept)} -> {sorted(kept)[:15]}...")
    print(f"Not in master     : {len(skipped_notmaster)} (correctly skipped)")
    print(f"Failed downloads  : {failed[:10]}")
    print(f"Merged PDF pages  : {out_path}")

if __name__ == "__main__":
    build_australia_pdf()