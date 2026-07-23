import csv
import sys
import os

def main():
    registry_file = 'data/master_registry.csv'
    
    if not os.path.exists(registry_file):
        print("Run this from the project root (where data/ folder is).")
        sys.exit(1)
        
    with open(registry_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
        
    if 'scale_coupling_evidence' not in fields:
        fields.append('scale_coupling_evidence')
        for row in rows:
            row['scale_coupling_evidence'] = ''
            
    # Target: Corpus B, Tier 4 (indeterminate)
    # The exact string in the registry is usually "4-indeterminate" or similar.
    target_docs = [r for r in rows if r.get('corpus_tier') == 'B' and str(r.get('enterprise_scale_tier')).startswith('4')]
    
    # Filter to only those that haven't been completed yet (optional, but good for resuming)
    # The user wants to iterate all 91, so we'll just check if it's already coded.
    pending_docs = [r for r in target_docs if r.get('hurdle_scale_coupled') not in ['yes', 'no', 'unclear']]
    
    print(f"Found {len(target_docs)} Tier-4 Corpus B records.")
    print(f"{len(pending_docs)} records pending manual coding.\n")
    
    if not pending_docs:
        print("All target records have been coded!")
        return

    updated = False
    
    for doc in pending_docs:
        doc_id = doc['doc_id']
        title = doc.get('title_url_query', '')
        source = doc.get('source_name_instrument_body', '')
        
        print(f"{'='*60}")
        print(f"Doc ID: {doc_id} | Source: {source}")
        print(f"Title/Query: {title}")
        print("\nQ: Does this hurdle's own economics only bind at small scale?")
        print("Press Enter to skip, or 'q' to quit and save.")
        
        coupled = input("hurdle_scale_coupled (yes/no/unclear): ").strip().lower()
        
        if coupled == 'q':
            break
        elif coupled in ['yes', 'no', 'unclear']:
            evidence = input("scale_coupling_evidence (quote the trigger phrase): ").strip()
            
            # Update the actual object in the rows list
            doc['hurdle_scale_coupled'] = coupled
            doc['scale_coupling_evidence'] = evidence
            updated = True
        elif coupled != '':
            print("Invalid input, skipping...")

    if updated:
        with open(registry_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nSaved updates to {registry_file}")
    else:
        print("\nNo updates made.")

if __name__ == '__main__':
    main()
