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
        
    if 'anchor_verdict' not in fields:
        fields.append('anchor_verdict')
        for row in rows:
            row['anchor_verdict'] = ''
            
    updated = False
    
    # 1. Auto-evaluate Actor test where possible
    for row in rows:
        if row.get('anchor_verdict'):
            continue # already processed
            
        tier = row.get('corpus_tier', '')
        scale = str(row.get('enterprise_scale_tier', ''))
        coupled = str(row.get('hurdle_scale_coupled', '')).lower()
        
        actor_pass = False
        verdict = None
        
        if tier == 'A':
            actor_pass = True
        elif tier == 'B':
            if scale.startswith('5'):
                verdict = 'comparator'
            elif scale.startswith('4'):
                if coupled == 'yes':
                    actor_pass = True
                else:
                    verdict = 'fail-actor'
            elif scale.startswith('1') or scale.startswith('2') or scale.startswith('3'):
                actor_pass = True
        
        # If a programmatic verdict was reached (e.g. comparator or fail-actor), assign it
        if verdict:
            row['anchor_verdict'] = verdict
            updated = True

    # 2. Iterative human review for Recognition & Chain tests
    pending = [r for r in rows if r.get('anchor_verdict') == '']
    
    print(f"Total pending manual anchor test review: {len(pending)}\n")
    
    for row in pending:
        doc_id = row['doc_id']
        title = row.get('title_url_query', '')
        source = row.get('source_name_instrument_body', '')
        
        print(f"{'='*60}")
        print(f"Doc ID: {doc_id} | Source: {source}")
        print(f"Title/Query: {title}")
        print("---")
        
        print("Q1: Does it pass the Recognition Test? (y/n)")
        rec = input("recognition_pass: ").strip().lower()
        if rec == 'q':
            break
        if rec != 'y':
            row['anchor_verdict'] = 'fail-recognition'
            updated = True
            continue
            
        print("Q2: Does it pass the Chain Test? (y/n)")
        chain = input("chain_pass: ").strip().lower()
        if chain == 'q':
            break
        if chain != 'y':
            row['anchor_verdict'] = 'fail-chain'
            updated = True
            continue
            
        row['anchor_verdict'] = 'pass'
        updated = True

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
