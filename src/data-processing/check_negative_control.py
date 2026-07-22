import pandas as pd
from pathlib import Path

def main():
    root = Path(".")
    
    units_df = pd.read_csv(root / "data" / "embeddings" / "modeling_units_with_topics.csv")
    meta_df = pd.read_csv(root / "data" / "master_registry.csv")
    rq1_df = pd.read_csv(root / "data" / "results" / "rq1_locus_distribution.csv")
    topic_mapping = pd.read_csv(root / "data" / "results" / "topic_locus_mapping.csv")
    
    # Merge scale_tier_v2 onto units
    df = pd.merge(units_df, meta_df[['doc_id', 'scale_tier_v2']], left_on='parent_doc_id', right_on='doc_id', how='left')
    
    if 'msme_specific_or_sector_wide' not in rq1_df.columns:
        rq1_df['msme_specific_or_sector_wide'] = ''
        
    for idx, row in rq1_df.iterrows():
        hurdle = row['hurdle']
        
        # find the topic(s) associated with this hurdle
        matched_topics = topic_mapping[topic_mapping['hurdle_name'] == hurdle]['Topic'].tolist()
        
        # find all units belonging to these topics
        hurdle_units = df[df['assigned_topic'].isin(matched_topics)]
        
        has_msme = len(hurdle_units[hurdle_units['scale_tier_v2'].str.contains('Tier 1|Tier 2|Tier 3', na=False)]) > 0
        has_large = len(hurdle_units[hurdle_units['scale_tier_v2'].str.contains('Tier 5', na=False)]) > 0
        
        if has_msme and not has_large:
            rq1_df.at[idx, 'msme_specific_or_sector_wide'] = 'Only-MSME'
        elif has_msme and has_large:
            rq1_df.at[idx, 'msme_specific_or_sector_wide'] = 'Sector-Wide'
        elif has_large and not has_msme:
            rq1_df.at[idx, 'msme_specific_or_sector_wide'] = 'Large-Firm-Only'
        else:
            rq1_df.at[idx, 'msme_specific_or_sector_wide'] = 'Indeterminate'
            
    rq1_df.to_csv(root / "data" / "results" / "rq1_locus_distribution.csv", index=False)
    print("Updated rq1_locus_distribution.csv with msme_specific_or_sector_wide.")

if __name__ == "__main__":
    main()
