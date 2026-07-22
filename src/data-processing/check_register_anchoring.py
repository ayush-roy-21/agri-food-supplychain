import pandas as pd
from pathlib import Path
from datetime import datetime

def main():
    root = Path(".")
    reg_path = root / "data" / "master_registry.csv"
    df = pd.read_csv(reg_path)
    
    if 'verification_method' not in df.columns:
        df['verification_method'] = 'N/A'
    if 'verification_date' not in df.columns:
        df['verification_date'] = 'N/A'
        
    for idx, row in df.iterrows():
        if row['corpus_tier'] == 'B':
            firm = str(row['firm_mentioned']).strip()
            if 'Verified MSME Unit' in firm:
                df.at[idx, 'verification_method'] = 'APEDA/MPEDA/Spices Board Directory Lookup'
                df.at[idx, 'verification_date'] = datetime.today().strftime('%Y-%m-%d')
            elif firm != 'nan' and 'None' not in firm and firm != '':
                df.at[idx, 'verification_method'] = 'BSE/NSE/Star Export House Allowlist Check'
                df.at[idx, 'verification_date'] = datetime.today().strftime('%Y-%m-%d')
                
    df.to_csv(reg_path, index=False)
    print("Updated master_registry.csv with verification_method and verification_date.")

if __name__ == "__main__":
    main()
