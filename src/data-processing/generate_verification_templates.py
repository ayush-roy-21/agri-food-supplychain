import pandas as pd
from pathlib import Path
import numpy as np

def generate_verification_templates():
    root = Path(".")
    results_dir = root / "data" / "results"
    
    # Read both generated CSVs
    df_16 = pd.read_csv(results_dir / "alert_16_35_india.csv")
    df_99 = pd.read_csv(results_dir / "alert_99_19_india.csv")
    
    # Add source tracking
    df_16['source_alert'] = '16-35'
    df_99['source_alert'] = '99-19'
    
    # Combine and deduplicate by firm name, aggregating sources and keeping the latest date
    combined = pd.concat([df_16, df_99])
    
    # Aggregate: if a firm is in both, join the sources. Keep max date just as a reference.
    agg_funcs = {
        'source_alert': lambda x: ', '.join(sorted(set(x))),
        'date_published': 'max'
    }
    
    unique_firms = combined.groupby(combined['firm_name'].str.upper().str.strip()).agg(
        firm_name=('firm_name', 'first'),
        source_alert=('source_alert', agg_funcs['source_alert']),
        date_published=('date_published', agg_funcs['date_published'])
    ).reset_index(drop=True)
    
    # Sort alphabetically by firm name
    unique_firms = unique_firms.sort_values(by='firm_name', key=lambda col: col.str.upper()).reset_index(drop=True)
    
    # Add required columns for manual verification
    unique_firms['register_consulted'] = ''
    unique_firms['lookup_date'] = ''
    unique_firms['firm_type_manufacturer_vs_merchant'] = ''
    unique_firms['tier_status'] = ''
    
    # Split alphabetically between two interns
    midpoint = len(unique_firms) // 2
    intern_1 = unique_firms.iloc[:midpoint].copy()
    intern_2 = unique_firms.iloc[midpoint:].copy()
    
    # Save the templates
    intern_1.to_csv(results_dir / "firm_verification_intern_1.csv", index=False)
    intern_2.to_csv(results_dir / "firm_verification_intern_2.csv", index=False)
    
    print(f"Total unique firms to verify: {len(unique_firms)}")
    print(f"Template 1 (Intern 1): {len(intern_1)} rows saved to firm_verification_intern_1.csv")
    print(f"Template 2 (Intern 2): {len(intern_2)} rows saved to firm_verification_intern_2.csv")

if __name__ == "__main__":
    generate_verification_templates()
