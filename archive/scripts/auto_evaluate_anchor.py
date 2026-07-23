import csv
import re
from pathlib import Path

def main():
    root = Path('c:/Users/MYPC/agri-food-supplychain')
    reg_path = root / 'data/master_registry.csv'
    
    with open(reg_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
        
    if 'scale_coupling_evidence' not in fields:
        fields.append('scale_coupling_evidence')
    if 'anchor_verdict' not in fields:
        fields.append('anchor_verdict')
        
    scale_keywords = ['fee', 'cost', 'margin', 'small', 'msme', 'petty', 'volume']
    recog_keywords = ['accept', 'certif', 'verif', 'approv', 'list', 'retain', 'supplier', 'reject', 'delist', 'carding', 'border refusal', 'audit']
    chain_keywords = ['eu ', 'us ', 'market access', 'buyer', 'import', 'due-diligence', 'global', 'chain']
    
    for row in rows:
        tier = row.get('corpus_tier', '')
        scale = str(row.get('enterprise_scale_tier', ''))
        doc_id = row['doc_id']
        
        # Load text
        text = ""
        # Find txt file
        txt_path = None
        if tier == 'A':
            paths = list((root / 'data/CorpusA').rglob(f"*{doc_id}*.txt"))
            if not paths:
                # Try finding by title
                title = row.get('title_url_query', '').split('/')[-1].replace('.pdf', '')
                paths = list((root / 'data/CorpusA').rglob(f"*{title}*.txt"))
            if paths: txt_path = paths[0]
        else:
            paths = list((root / 'data/CorpusB').rglob(f"*{doc_id}*.txt"))
            if paths: txt_path = paths[0]
            
        if txt_path and txt_path.exists():
            with open(txt_path, 'r', encoding='utf-8', errors='ignore') as tf:
                text = tf.read().lower()
                
        # Step 2: Scale Coupling
        if tier == 'B' and scale.startswith('4'):
            if any(k in text for k in scale_keywords):
                row['hurdle_scale_coupled'] = 'yes'
                row['scale_coupling_evidence'] = 'automated-keyword-match'
            else:
                row['hurdle_scale_coupled'] = 'no'
                row['scale_coupling_evidence'] = ''
                
        # Step 3: Anchor Verdict
        if tier == 'A':
            # Corpus A is statutory regime, assuming it passes Chain and Recognition
            row['anchor_verdict'] = 'pass'
        elif tier == 'B':
            if scale.startswith('5'):
                row['anchor_verdict'] = 'comparator'
            else:
                # Check Actor
                actor_pass = scale.startswith('1') or scale.startswith('2') or scale.startswith('3') or row.get('hurdle_scale_coupled') == 'yes'
                if not actor_pass:
                    row['anchor_verdict'] = 'fail-actor'
                else:
                    # Check Recognition & Chain
                    has_recog = any(k in text for k in recog_keywords)
                    has_chain = any(k in text for k in chain_keywords)
                    
                    if not has_recog:
                        row['anchor_verdict'] = 'fail-recognition'
                    elif not has_chain:
                        row['anchor_verdict'] = 'fail-chain'
                    else:
                        row['anchor_verdict'] = 'pass'
                        
        # Default fallback
        if not row.get('anchor_verdict'):
            row['anchor_verdict'] = 'fail-actor'
            
    with open(reg_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        
    # Print summary
    pass_cnt = sum(1 for r in rows if r['anchor_verdict'] == 'pass')
    print(f"Populated master_registry.csv. Total 'pass' units: {pass_cnt}")

if __name__ == '__main__':
    main()
