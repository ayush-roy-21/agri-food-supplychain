import pandas as pd
from pathlib import Path
import re
import csv

def evaluate_tier(text):
    text_lower = text.lower()
    
    # Tier 5: excluded-large
    tier_5_keywords = ['bse', 'nse', 'star export house', 'limited company', 'pvt ltd', 'corporate']
    if any(kw in text_lower for kw in tier_5_keywords):
        for kw in tier_5_keywords:
            if kw in text_lower:
                return 'Tier 5 (excluded-large)', kw
                
    # Tier 1: register-verified
    tier_1_keywords = ['udyam registration number', 'iec code', 'cres code', 'rcmc code']
    if any(kw in text_lower for kw in tier_1_keywords):
        for kw in tier_1_keywords:
            if kw in text_lower:
                return 'Tier 1 (register-verified)', kw
                
    # Tier 2: strongly indicated
    tier_2_keywords = ['udyam', 'proprietorship', 'single unit', 'first consignment', 'small exporter']
    if any(kw in text_lower for kw in tier_2_keywords):
        for kw in tier_2_keywords:
            if kw in text_lower:
                return 'Tier 2 (strongly indicated)', kw
                
    # Tier 3: weakly indicated
    tier_3_keywords = ['fpo', 'cooperative', 'smallholder', 'new exporter']
    if any(kw in text_lower for kw in tier_3_keywords):
        for kw in tier_3_keywords:
            if kw in text_lower:
                return 'Tier 3 (weakly indicated)', kw

    return 'Tier 4 (indeterminate)', 'None'

def main():
    root = Path(".")
    reg_path = root / "data" / "master_registry.csv"
    df = pd.read_csv(reg_path)
    
    # ensure columns exist
    if 'scale_tier_v2' not in df.columns:
        df['scale_tier_v2'] = ''
    if 'scale_evidence' not in df.columns:
        df['scale_evidence'] = ''
        
    for idx, row in df.iterrows():
        if row['corpus_tier'] == 'B':
            # find the text file
            doc_id = row['doc_id']
            txt_path = None
            for p in (root / "CorpusB").rglob(f"{doc_id}.txt"):
                txt_path = p
                break
                
            if txt_path and txt_path.is_file():
                try:
                    with open(txt_path, 'r', encoding='utf-8', errors='replace') as f:
                        lines = f.readlines()
                        # skip first 12 header lines
                        body_text = "".join(lines[12:])
                        tier, evidence = evaluate_tier(body_text)
                        df.at[idx, 'scale_tier_v2'] = tier
                        df.at[idx, 'scale_evidence'] = evidence
                except Exception as e:
                    print(f"Error reading {txt_path}: {e}")
                    df.at[idx, 'scale_tier_v2'] = 'Tier 4 (indeterminate)'
                    df.at[idx, 'scale_evidence'] = 'File Error'
            else:
                df.at[idx, 'scale_tier_v2'] = 'Tier 4 (indeterminate)'
                df.at[idx, 'scale_evidence'] = 'File Missing'
        else:
            df.at[idx, 'scale_tier_v2'] = 'N/A (Corpus A)'
            df.at[idx, 'scale_evidence'] = 'N/A'
            
    # Retire keyword-plausible-unverified
    if 'enterprise_scale_tier' in df.columns:
        df['enterprise_scale_tier'] = df['enterprise_scale_tier'].replace('keyword-plausible-unverified', 'retired')
        
    df.to_csv(reg_path, index=False)
    print("Updated master_registry.csv with scale_tier_v2 and scale_evidence.")
    
    # Save coverage
    coverage = df[df['corpus_tier'] == 'B']['scale_tier_v2'].value_counts().reset_index()
    coverage.columns = ['scale_tier_v2', 'count']
    out_dir = root / "data" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    coverage.to_csv(out_dir / "scale_tier_coverage.csv", index=False)
    print("Saved scale_tier_coverage.csv")

if __name__ == "__main__":
    main()
