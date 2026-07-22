import csv
import sys
import os

def main():
    queue_file = 'data/manual_locus_coding_queue.csv'
    draft_file = 'data/registry_locus_mapping_draft.csv'
    
    if not os.path.exists(queue_file) or not os.path.exists(draft_file):
        print("Run this from the project root (where data/ folder is).")
        sys.exit(1)
        
    with open(queue_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        queue_docs = list(reader)
        
    with open(draft_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        draft_fields = reader.fieldnames
        draft_rows = list(reader)
        
    # Build draft lookup by doc_id
    draft_lookup = {r['doc_id']: r for r in draft_rows}
    
    pending_docs = [d for d in queue_docs if not draft_lookup.get(d['doc_id'], {}).get('locus_primary')]
    
    if not pending_docs:
        print("All documents in the queue have been coded in the draft mapping!")
        return

    print(f"Found {len(pending_docs)} documents pending manual coding.\n")
    
    updated = False
    for doc in pending_docs:
        doc_id = doc['doc_id']
        tier = doc['tier']
        hypothesis = doc.get('dominant_real_topic', '')
        
        print(f"{'='*60}")
        print(f"Doc ID: {doc_id}  |  Tier: {tier}")
        print(f"Source: {doc.get('source_name_instrument_body', '')}")
        print(f"Reason: {doc.get('reason', '')}")
        if hypothesis:
            print(f"Algorithmic Hypothesis (Real Topic): {hypothesis}")
            
        print("\nPress Enter to skip for now, or 'q' to quit and save.")
        loc_pri = input("Enter locus_primary: ").strip()
        
        if loc_pri.lower() == 'q':
            break
        elif loc_pri:
            loc_sec = input("Enter locus_secondary (optional): ").strip()
            
            if doc_id in draft_lookup:
                draft_lookup[doc_id]['locus_primary'] = loc_pri
                draft_lookup[doc_id]['locus_secondary'] = loc_sec
                updated = True
            
    if updated:
        with open(draft_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=draft_fields)
            writer.writeheader()
            writer.writerows(draft_rows)
        print(f"\nSaved updates to {draft_file}")
    else:
        print("\nNo updates made.")

if __name__ == '__main__':
    main()
