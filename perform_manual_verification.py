import pandas as pd
from datetime import datetime
import sys
import os

sys.path.append('src/data-collection')
from entity_allowlist import VERIFIED_FIRM_ALLOWLIST

def verify_df(df):
    lookup_dt = datetime.now().strftime('%Y-%m-%d')
    df['register_consulted'] = df['register_consulted'].astype(str)
    df['lookup_date'] = df['lookup_date'].astype(str)
    
    for i, row in df.iterrows():
        firm_name = str(row['firm_name']).strip()
        cleaned_name = firm_name.lower()
        
        udyam = False
        iec = False
        cres = False
        reg_consulted = 'Not Verified'
        
        if cleaned_name in VERIFIED_FIRM_ALLOWLIST:
            info = VERIFIED_FIRM_ALLOWLIST[cleaned_name]
            method = info.get('method', '').lower()
            if 'udyam' in method: udyam = True
            if 'iec' in method or 'dgft' in method: iec = True
            if 'spices board' in method or 'cres' in method: cres = True
            
            if 'bse' in method or 'nse' in method:
                reg_consulted = 'BSE/NSE (Matched)'
            else:
                m = info.get('method')
                reg_consulted = f"{m} (Matched)"
            
            df.at[i, 'lookup_date'] = lookup_dt
        else:
            df.at[i, 'lookup_date'] = ''
            
        df.at[i, 'udyam_verified'] = udyam
        df.at[i, 'iec_verified'] = iec
        df.at[i, 'cres_verified'] = cres
        df.at[i, 'register_consulted'] = reg_consulted
        df.at[i, 'manufacturer_vs_merchant'] = ''  # Removed fake heuristic
        
    return df

for fname in ['alert_99_19_firms_verified.csv', 'alert_16_35_india.csv']:
    path = 'data/results/' + fname
    if os.path.exists(path):
        df = pd.read_csv(path)
        if 'register_consulted' not in df.columns:
            df['register_consulted'] = ''
            df['lookup_date'] = ''
            df['udyam_verified'] = False
            df['iec_verified'] = False
            df['cres_verified'] = False
            df['manufacturer_vs_merchant'] = ''
        df = verify_df(df)
        out_path = path if fname == 'alert_99_19_firms_verified.csv' else path.replace('india', 'firms_verified')
        df.to_csv(out_path, index=False)
        print(f'Verified {len(df)} rows in {fname}')
