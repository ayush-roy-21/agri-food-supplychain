import pandas as pd
from pathlib import Path

def main():
    root = Path(".")
    reg_path = root / "data" / "master_registry.csv"
    df = pd.read_csv(reg_path)
    
    if 'dqa_content_notes' not in df.columns:
        df['dqa_content_notes'] = ''
        
    for idx, row in df.iterrows():
        score = str(row['dqa_content_score']).strip()
        if len(score) > 15 and ',' not in score[:10]:
            # This is likely prose
            df.at[idx, 'dqa_content_notes'] = score
            df.at[idx, 'dqa_content_score'] = 'M,M,M,M,M,M'
        elif score == 'nan' or score == '':
            df.at[idx, 'dqa_content_score'] = 'M,M,M,M,M,M'
            
    df.to_csv(reg_path, index=False)
    print("Updated master_registry.csv with coded DQA scores and dqa_content_notes.")

if __name__ == "__main__":
    main()
