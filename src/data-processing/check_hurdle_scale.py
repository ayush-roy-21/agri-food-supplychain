import pandas as pd
from pathlib import Path

def is_scale_coupled(text):
    text_lower = text.lower()
    keywords = [
        'fixed certification fee',
        'crushing thin margin',
        'per-consignment',
        'testing cost',
        'minimum-volume',
        'economies of scale',
        'high cost of compliance',
        'cannot afford',
        'compliance cost',
        'small margin'
    ]
    return 'yes' if any(kw in text_lower for kw in keywords) else 'no'

def main():
    root = Path(".")
    reg_path = root / "data" / "master_registry.csv"
    df = pd.read_csv(reg_path)
    
    if 'hurdle_scale_coupled' not in df.columns:
        df['hurdle_scale_coupled'] = 'N/A'
        
    for idx, row in df.iterrows():
        if row['corpus_tier'] == 'B':
            doc_id = row['doc_id']
            txt_path = None
            for p in (root / "CorpusB").rglob(f"{doc_id}.txt"):
                txt_path = p
                break
                
            if txt_path and txt_path.is_file():
                try:
                    with open(txt_path, 'r', encoding='utf-8', errors='replace') as f:
                        lines = f.readlines()
                        body_text = "".join(lines[12:])
                        df.at[idx, 'hurdle_scale_coupled'] = is_scale_coupled(body_text)
                except Exception as e:
                    df.at[idx, 'hurdle_scale_coupled'] = 'error'
            else:
                df.at[idx, 'hurdle_scale_coupled'] = 'missing'
        else:
            df.at[idx, 'hurdle_scale_coupled'] = 'N/A'
            
    df.to_csv(reg_path, index=False)
    print("Updated master_registry.csv with hurdle_scale_coupled.")
    
    coverage = df[df['corpus_tier'] == 'B']['hurdle_scale_coupled'].value_counts().reset_index()
    coverage.columns = ['hurdle_scale_coupled', 'count']
    coverage.to_csv(root / "data" / "results" / "hurdle_scale_coupled_coverage.csv", index=False)
    print("Saved hurdle_scale_coupled_coverage.csv")

if __name__ == "__main__":
    main()
