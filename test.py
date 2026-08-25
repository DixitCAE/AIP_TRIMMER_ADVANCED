import fitz, re
doc = fitz.open(r"C:\Users\divyn\Downloads\BAHAMAS 02_26 - AIRAC AIP AMDT WEF 29OCT26.pdf")

def compact_spaces(t): return re.sub(r"\s+"," ",str(t).upper()).strip()

def get_zone_lines(page, top_limit=150, bottom_limit=120):
    lines=[]; H=page.rect.height
    for b in page.get_text("blocks"):
        x0,y0,x1,y1,txt=b[:5]
        if not (y0<top_limit or y1>H-bottom_limit): continue
        for off,rl in enumerate(str(txt).splitlines()):
            lt=compact_spaces(rl)
            if lt: lines.append((y0+off*0.01,x0,lt))
    lines.sort(key=lambda i:(i[0],i[1]))
    return [t for _,_,t in lines]

pat = r"\bAD\s*2\s+(MY[A-Z]{2})\s+\d+\s*-\s*\d+\b"

for pi in range(1, len(doc)):          # SKIP page 1 (the checklist)
    page = doc[pi]
    body = compact_spaces(page.get_text())
    if "AD 2" not in body:
        continue
    zone = get_zone_lines(page)
    zjoin = compact_spaces(" ".join(zone))
    body_hit = re.search(pat, body)
    zone_hit = re.search(pat, zjoin)
    print(f"PAGE {pi+1}")
    print(f"  matcher finds ICAO in BODY? {body_hit.group(1) if body_hit else 'NO'}")
    print(f"  matcher finds ICAO in ZONE? {zone_hit.group(1) if zone_hit else 'NO'}")
    print(f"  zone top 2 lines: {zone[:2]}")
    print("-"*60)