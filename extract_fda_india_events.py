import csv
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Verified 2026-07-24 against https://www.accessdata.fda.gov/cms_ia/country_IN.html
# Candidate "relevant alerts" for this study's commodity scope. This list is a
# starting point grounded in what's actually on FDA's India page -- confirm
# the final six (or more) with your research mentor rather than treating this
# as authoritative.
RELEVANT_ALERTS = [
    ("28-02", "https://www.accessdata.fda.gov/cms_ia/importalert_90.html",
     "Black Pepper from India (DWPE)"),
    ("16-35", "https://www.accessdata.fda.gov/cms_ia/importalert_43.html",
     "Raw and Cooked Shrimp from India (DWPE)"),
    ("16-81", "https://www.accessdata.fda.gov/cms_ia/importalert_49.html",
     "Seafood Products - Salmonella (DWPE)"),
    ("16-127", "https://www.accessdata.fda.gov/cms_ia/importalert_29.html",
     "All Seafood - Chloramphenicol (DWPE)"),
    ("16-124", "https://www.accessdata.fda.gov/cms_ia/importalert_27.html",
     "Aquaculture Seafood - Unapproved Drugs (DWPE)"),
    ("16-129", "https://www.accessdata.fda.gov/cms_ia/importalert_31.html",
     "Seafood Products - Nitrofurans (DWPE)"),
    ("99-19", "https://www.accessdata.fda.gov/cms_ia/importalert_263.html",
     "Food Products - Salmonella, general (DWPE)"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

OUTPUT_PATH = Path("data/results/fda_india_events.csv")


def fetch(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def extract_india_section(html):
    """
    Return the raw HTML/text slice starting at the 'INDIA' country heading
    and ending at the next country heading (or end of the firm-list section).
    FDA's markup nests country headings and firm blocks inconsistently, so
    this uses a text-based split rather than assuming a clean DOM structure.
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n")

    # The country list section starts after "## Countries" (or similar) and
    # each country is its own heading in caps, e.g. "## INDIA".
    marker = re.search(r"\bINDIA\b", text)
    if not marker:
        return None, None

    start = marker.start()
    # Find the next all-caps country-looking heading after INDIA's own block
    # to bound the slice. This is heuristic -- verify manually.
    rest = text[start + 5:]
    next_country = re.search(r"\n([A-Z][A-Z .]{3,40})\n", rest)
    end = start + 5 + next_country.start() if next_country else len(text)

    return text[start:end], text


def parse_blanket_entries(section_text, alert_number, alert_name, url):
    """Parse the top blanket 'Countries > INDIA' product-code rows (no firm)."""
    events = []
    # Pattern like: (16 J - B 05) Shrimp & Prawns, Raw, Fresh, Ambient
    for m in re.finditer(
        r"\(([\w\s-]{6,20})\)\s*([^\n]+?)\n+\s*(?:Desc:\s*([^\n]+))?\n*\s*(?:Notes?:\s*([^\n]+))?",
        section_text,
    ):
        code, desc1, desc2, notes = m.groups()
        events.append({
            "alert_number": alert_number,
            "alert_name": alert_name,
            "list_type": "countrywide_blanket",
            "firm_name": "",
            "address_raw": "",
            "state": "",
            "country": "INDIA",
            "product_code": code.strip(),
            "product_desc": (desc1 or desc2 or "").strip(),
            "date_published": "",
            "notes": (notes or "").strip(),
            "source_url": url,
            "extraction_date": datetime.now(timezone.utc).date().isoformat(),
        })
    return events


def parse_firm_blocks(full_text, list_type, alert_number, alert_name, url):
    """
    Parse named-firm blocks under a Red List or Green List heading, of the form:

        FIRM NAME
        Date Published : MM/DD/YYYY
        <address lines...>
        , <City>,
        <State> INDIA
        <product code>  <product desc>
        Date Published: MM/DD/YYYY
        Desc: ...
        Notes: ...
        (repeated per product code)

    This is heuristic against legacy markup -- validate against a manual
    read of at least 5 firms per alert before trusting the row count.
    """
    events = []
    heading = "Green List" if list_type == "green" else "Red List"
    idx = full_text.find(heading)
    if idx == -1:
        return events
    block_text = full_text[idx:]

    firm_pattern = re.compile(
        r"\n([A-Z][A-Za-z0-9&.,()\-/ ]{2,80})\n\s*Date Published\s*:\s*([\d/]+)\n"
        r"([^\n]+(?:\n[^\n]+){0,3}?)\n\s*([A-Za-z ]+)\s+INDIA\n"
    )
    for m in firm_pattern.finditer(block_text):
        firm_name, date_pub, address_raw, state = m.groups()
        events.append({
            "alert_number": alert_number,
            "alert_name": alert_name,
            "list_type": list_type,
            "firm_name": firm_name.strip(),
            "address_raw": address_raw.strip().replace("\n", " "),
            "state": state.strip(),
            "country": "INDIA",
            "product_code": "",
            "product_desc": "",
            "date_published": date_pub.strip(),
            "notes": "",
            "source_url": url,
            "extraction_date": datetime.now(timezone.utc).date().isoformat(),
        })
    return events


def main():
    all_events = []
    for alert_number, url, alert_name in RELEVANT_ALERTS:
        print(f"Fetching {alert_number} ({alert_name})...")
        try:
            html = fetch(url)
        except Exception as e:
            print(f"  [FAIL] {alert_number}: {e}")
            continue

        india_section, full_text = extract_india_section(html)
        if india_section is None:
            print(f"  [WARN] No INDIA section found for {alert_number}")
            continue

        blanket = parse_blanket_entries(india_section, alert_number, alert_name, url)
        red = parse_firm_blocks(full_text, "red", alert_number, alert_name, url)
        green = parse_firm_blocks(full_text, "green", alert_number, alert_name, url)

        print(f"  blanket={len(blanket)} red_firms={len(red)} green_firms={len(green)}")
        all_events.extend(blanket + red + green)
        time.sleep(1)  # be polite to FDA's server

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "alert_number", "alert_name", "list_type", "firm_name",
            "address_raw", "state", "country", "product_code",
            "product_desc", "date_published", "notes", "source_url",
            "extraction_date",
        ])
        writer.writeheader()
        writer.writerows(all_events)

    named_firms = [e for e in all_events if e["firm_name"]]
    distinct_firms = {e["firm_name"].strip().lower() for e in named_firms}
    print(f"\nTotal rows: {len(all_events)}")
    print(f"Named-firm rows: {len(named_firms)} | Distinct firm names: {len(distinct_firms)}")
    print(f"Countrywide-blanket (no-firm) rows: {len(all_events) - len(named_firms)}")
    print(f"Written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
