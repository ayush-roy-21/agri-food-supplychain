import csv
import sys

def main():
    dest_csv = 'topic_locus_mapping.csv'

    with open(dest_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    proposals = {
        '0': ('digital-traceability-system', 'sustainability-reporting'),
        '1': ('spices-consignment-inspection', 'marine-catch-verification'),
        '2': ('digital-export-services', 'dgft-exim-licensing-integration'),
        '3': ('phytosanitary-and-pesticide-mrl-screening', 'tea-export-governance'),
        '4': ('fresh-produce-hortinet', 'apeda-institutional-facilitation'),
        '5': ('cereals-export-protocol', 'single-window-clearance'),
        '6': ('organic-export-governance', 'npop-equivalence-and-coi-validation'),
        '7': ('marine-aquaculture-policy', 'seafood-value-addition'),
        '10': ('sustainability-reporting', 'corporate-sustainability-due-diligence'),
        '11': ('animal-products-governance', 'abattoir-haccp-and-ante-mortem-inspection'),
        '12': ('marine-export-performance', 'us-tariff-impact'),
    }

    for r in rows:
        topic = r['Topic']
        if topic in proposals:
            r['locus_primary'] = proposals[topic][0]
            r['locus_secondary'] = proposals[topic][1]

    with open(dest_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Topic', 'Top_Keywords', 'Notes', 'locus_primary', 'locus_secondary'])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated {dest_csv} with proposed locus tags.")

if __name__ == '__main__':
    main()
