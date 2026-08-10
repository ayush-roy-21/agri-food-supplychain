
import csv
import re
import time
from datetime import datetime, timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup

RELEVANT_ALERTS = [
    ('28-02', 'https://www.accessdata.fda.gov/cms_ia/importalert_90.html', 'Black Pepper from India (DWPE)'),
    ('16-35', 'https://www.accessdata.fda.gov/cms_ia/importalert_43.html', 'Raw and Cooked Shrimp from India (DWPE)'),
    ('16-81', 'https://www.accessdata.fda.gov/cms_ia/importalert_49.html', 'Seafood Products - Salmonella (DWPE)'),
    ('16-127', 'https://www.accessdata.fda.gov/cms_ia/importalert_29.html', 'All Seafood - Chloramphenicol (DWPE)'),
    ('16-124', 'https://www.accessdata.fda.gov/cms_ia/importalert_27.html', 'Aquaculture Seafood - Unapproved Drugs (DWPE)'),
    ('16-129', 'https://www.accessdata.fda.gov/cms_ia/importalert_31.html', 'Seafood Products - Nitrofurans (DWPE)'),
    ('99-19', 'https://www.accessdata.fda.gov/cms_ia/importalert_263.html', 'Food Products - Salmonella, general (DWPE)'),
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}
OUTPUT_PATH = Path('data/results/fda_india_events.csv')

def fetch(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text

def parse_blanket_entries(text, alert_number, alert_name, url):
    events = []
    # Find the Countries section
    countries_idx = text.rfind('Countries')
    if countries_idx == -1: countries_idx = 0
    
    red_idx = text.rfind('Red List')
    green_idx = text.rfind('Green List')
    end_idx = len(text)
    if red_idx > countries_idx: end_idx = min(end_idx, red_idx)
    if green_idx > countries_idx: end_idx = min(end_idx, green_idx)

    countries_text = text[countries_idx:end_idx]
    
    india_marker = re.search(r'\n\s*INDIA\s*\n', countries_text)
    if not india_marker: return []
    start = india_marker.end()
    
    # In the blanket list, country headers are strictly \nCOUNTRY\n without firms, so this regex works here!
    next_country = re.search(r'\n\s*([A-Z][A-Z \-\']{3,40})\s*\n', countries_text[start:])
    if next_country:
        india_text = countries_text[start:start+next_country.start()]
    else:
        india_text = countries_text[start:]

    for m in re.finditer(
        r'\(([\w\s-]{6,20})\)\s*([^\n]+?)\n+\s*(?:Desc:\s*([^\n]+))?\n*\s*(?:Notes?:\s*([^\n]+))?',
        india_text,
    ):
        code, desc1, desc2, notes = m.groups()
        events.append({
            'alert_number': alert_number, 'alert_name': alert_name, 'list_type': 'countrywide_blanket',
            'firm_name': '', 'address_raw': '', 'state': '', 'country': 'INDIA',
            'product_code': code.strip(), 'product_desc': (desc1 or desc2 or '').strip(),
            'date_published': '', 'notes': (notes or '').strip(), 'source_url': url,
            'extraction_date': datetime.now(timezone.utc).date().isoformat(),
        })
    return events

def parse_firm_blocks(full_text, list_type, alert_number, alert_name, url):
    events = []
    heading = 'Green List' if list_type == 'green' else 'Red List'
    idx = full_text.rfind(heading)
    if idx == -1: return events
    
    # If looking for Red List, stop at Green List
    end_idx = len(full_text)
    if list_type == 'red':
        g_idx = full_text.find('Green List', idx)
        if g_idx != -1: end_idx = g_idx
        
    block_text = full_text[idx:end_idx]

    firm_pattern = re.compile(
        r'\n([A-Z][A-Za-z0-9&.,() \-]{2,80}?)\s*\n+\s*'
        r'Date Published\s*:\s*([\d/]+)\s*\n+'
        r'((?:(?!\n\s*Date Published).){1,250}?)\s*INDIA\b',
        re.DOTALL
    )
    for m in firm_pattern.finditer(block_text):
        firm_name, date_pub, address_raw = m.groups()
        address_clean = address_raw.strip().replace('\n', ' ')
        state = ''
        if ',' in address_clean:
            state = address_clean.split(',')[-1].strip()
        else:
            state = address_clean.split()[-1] if address_clean else ''
            
        events.append({
            'alert_number': alert_number, 'alert_name': alert_name, 'list_type': list_type,
            'firm_name': firm_name.strip(), 'address_raw': address_clean,
            'state': state, 'country': 'INDIA', 'product_code': '', 'product_desc': '',
            'date_published': date_pub.strip(), 'notes': '', 'source_url': url,
            'extraction_date': datetime.now(timezone.utc).date().isoformat(),
        })
    return events

def main():
    all_events = []
    for alert_number, url, alert_name in RELEVANT_ALERTS:
        print(f'Fetching {alert_number} ({alert_name})...')
        try: html = fetch(url)
        except Exception as e:
            print(f'  [FAIL] {alert_number}: {e}')
            continue
            
        soup = BeautifulSoup(html, 'html.parser')
        full_text = soup.get_text('\n')

        blanket = parse_blanket_entries(full_text, alert_number, alert_name, url)
        red = parse_firm_blocks(full_text, 'red', alert_number, alert_name, url)
        green = parse_firm_blocks(full_text, 'green', alert_number, alert_name, url)

        print(f'  blanket={len(blanket)} red_firms={len(red)} green_firms={len(green)}')
        all_events.extend(blanket + red + green)
        time.sleep(1)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'alert_number', 'alert_name', 'list_type', 'firm_name',
            'address_raw', 'state', 'country', 'product_code',
            'product_desc', 'date_published', 'notes', 'source_url',
            'extraction_date',
        ])
        writer.writeheader()
        writer.writerows(all_events)

    named_firms = [e for e in all_events if e['firm_name']]
    distinct_firms = {e['firm_name'].strip().lower() for e in named_firms}
    print(f'\nTotal rows: {len(all_events)}')
    print(f'Named-firm rows: {len(named_firms)} | Distinct firm names: {len(distinct_firms)}')
    print(f'Countrywide-blanket (no-firm) rows: {len(all_events) - len(named_firms)}')
    print(f'Written to {OUTPUT_PATH}')

if __name__ == '__main__': main()
