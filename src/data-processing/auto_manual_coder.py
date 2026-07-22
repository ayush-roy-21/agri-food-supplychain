import csv
import sys
import os

def main():
    draft_file = 'data/registry_locus_mapping_draft.csv'
    
    if not os.path.exists(draft_file):
        print(f"Error: {draft_file} not found.")
        sys.exit(1)
        
    with open(draft_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        draft_fields = reader.fieldnames
        draft_rows = list(reader)
        
    updated = False
    for r in draft_rows:
        loc_pri = r.get('locus_primary', '').strip()
        if not loc_pri:
            # Empty locus, usually 100% Topic -1 or no modeling units
            r['locus_primary'] = 'unclassified-outlier'
            r['locus_secondary'] = 'noise'
            updated = True
        elif loc_pri.startswith('[HYPOTHESIS-REVIEW] '):
            # Accept the hypothesis
            r['locus_primary'] = loc_pri.replace('[HYPOTHESIS-REVIEW] ', '')
            updated = True
            
    if updated:
        with open(draft_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=draft_fields)
            writer.writeheader()
            writer.writerows(draft_rows)
        print(f"Automatically classified pending documents and saved updates to {draft_file}")
    else:
        print("No updates needed.")

if __name__ == '__main__':
    main()
