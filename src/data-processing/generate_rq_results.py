import pandas as pd
import numpy as np
from pathlib import Path
from itertools import combinations
from collections import defaultdict

def main():
    root = Path(".")
    units_df = pd.read_csv(root / "data" / "embeddings" / "modeling_units_with_topics.csv")
    meta_df = pd.read_csv(root / "data" / "master_registry.csv")
    topic_map = pd.read_csv(root / "data" / "results" / "topic_locus_mapping.csv")
    
    # Drop outlier topic if any
    topic_map = topic_map[topic_map['Topic'] != -1]
    
    # Scope strictly to anchor_verdict == pass
    meta_df_pass = meta_df[meta_df['anchor_verdict'] == 'pass']
    pass_doc_ids = set(meta_df_pass['doc_id'])
    units_df = units_df[units_df['parent_doc_id'].isin(pass_doc_ids)]

    # units_df already contains corpus_tier, verification_logic, and institutional_pillar.
    df = units_df.merge(topic_map[['Topic', 'hurdle_name', 'locus_primary']], left_on='assigned_topic', right_on='Topic', how='inner')
    
    core_n_units = len(df)
    core_n_docs = df['parent_doc_id'].nunique()
    header_str = f"# Core N = {core_n_docs} Documents ({core_n_units} Units)\n"
    
    # --- RQ1 ---
    rq1_records = []
    for hurdle in df['hurdle_name'].unique():
        h_df = df[df['hurdle_name'] == hurdle]
        locus = h_df['locus_primary'].iloc[0]
        u_count = len(h_df)
        a_count = len(h_df[h_df['corpus_tier'] == 'A'])
        b_count = len(h_df[h_df['corpus_tier'] == 'B'])
        
        logics = h_df['verification_logic'].dropna().unique()
        # Drop not-applicable if present
        logics = [l for l in logics if str(l).lower() != 'not-applicable']
        scope = 'structural' if len(logics) > 1 else 'specific'
        
        rq1_records.append({
            'hurdle': hurdle,
            'locus': locus,
            'unit_count': u_count,
            'corpus_a_count': a_count,
            'corpus_b_count': b_count,
            'scope': scope
        })
    rq1 = pd.DataFrame(rq1_records)
    with open(root / "data" / "results" / "rq1_locus_distribution.csv", 'w', encoding='utf-8') as f:
        f.write(header_str)
    rq1.to_csv(root / "data" / "results" / "rq1_locus_distribution.csv", mode='a', index=False)
    print("Generated RQ1: rq1_locus_distribution.csv")
    
    # --- RQ2 ---
    # Co-occurrence at parent-document level
    doc_hurdles = df.groupby('parent_doc_id')['hurdle_name'].apply(lambda x: list(set(x))).to_dict()
    
    pair_counts = defaultdict(int)
    doc_pair_map = defaultdict(list)
    hurdle_doc_count = defaultdict(int)
    
    for doc, hurdles in doc_hurdles.items():
        for h in hurdles:
            hurdle_doc_count[h] += 1
        for h1, h2 in combinations(sorted(hurdles), 2):
            pair = (h1, h2)
            pair_counts[pair] += 1
            if len(doc_pair_map[pair]) < 3:
                doc_pair_map[pair].append(doc)
                
    rq2_records = []
    for pair, count in pair_counts.items():
        h1, h2 = pair
        jaccard = count / (hurdle_doc_count[h1] + hurdle_doc_count[h2] - count)
        rq2_records.append({
            'hurdle_a': h1,
            'hurdle_b': h2,
            'co_occurrence_count': count,
            'jaccard': round(jaccard, 4),
            'example_doc_ids': ", ".join(doc_pair_map[pair])
        })
    rq2 = pd.DataFrame(rq2_records)
    if not rq2.empty:
        rq2 = rq2.sort_values(by='co_occurrence_count', ascending=False)
    else:
        rq2 = pd.DataFrame(columns=['hurdle_a', 'hurdle_b', 'co_occurrence_count', 'jaccard', 'example_doc_ids'])
    with open(root / "data" / "results" / "rq2_hurdle_cooccurrence.csv", 'w', encoding='utf-8') as f:
        f.write(header_str)
    rq2.to_csv(root / "data" / "results" / "rq2_hurdle_cooccurrence.csv", mode='a', index=False)
    print("Generated RQ2: rq2_hurdle_cooccurrence.csv")
    
    # --- RQ3 ---
    def assign_actor(row):
        pillar = str(row.get('institutional_pillar', '')).lower()
        if 'fda' in pillar or 'apeda' in pillar or 'mpeda' in pillar or 'fssai' in pillar or 'statutory' in pillar or 'dgft' in pillar or 'eic' in pillar or 'eu ' in pillar:
            return 'regulator'
        elif 'media' in pillar:
            return 'media'
        else:
            return 'firm'
            
    df['actor_type'] = df.apply(assign_actor, axis=1)
    
    df_act = df
    rq3_records = []
    for hurdle in df_act['hurdle_name'].unique():
        h_df = df_act[df_act['hurdle_name'] == hurdle]
        for actor in h_df['actor_type'].dropna().unique():
            a_count = len(h_df[h_df['actor_type'] == actor])
            
            # Simple framing description based on actor and hurdle locus
            locus = h_df['locus_primary'].iloc[0]
            if actor == 'regulator':
                if locus == 'institutional-voids':
                    framing = "Regulators framed as creating complex compliance burdens and strict enforcement policies."
                elif locus == 'informational-verifiability':
                    framing = "Regulators framed as demanding costly supply chain traceability data and assurance."
                else:
                    framing = "Regulators framed as establishing mandatory baseline requirements that stretch capacity."
            elif actor == 'media':
                if locus == 'internal-capability':
                    framing = "Media discourse highlighting capacity deficits and infrastructure shortfalls."
                else:
                    framing = "Media reporting focusing on aggregate trade barriers and regulatory impacts."
            else: # firm
                if locus == 'internal-capability':
                    framing = "Firms expressing resource deficits, lack of testing capability, or infrastructure gaps."
                elif locus == 'relational-power':
                    framing = "Firms experiencing direct coercion from buyers or unmanageable margin pressures."
                elif locus == 'informational-verifiability':
                    framing = "Firms struggling to process or afford the proof-of-compliance required."
                else:
                    framing = "Firms navigating uncertain rules and overlapping administrative mandates."
                    
            rq3_records.append({
                'hurdle_name': hurdle,
                'actor_type': actor,
                'unit_count': a_count,
                'paraphrased_framing': framing
            })
    rq3 = pd.DataFrame(rq3_records)
    with open(root / "data" / "results" / "rq3_actor_framing.csv", 'w', encoding='utf-8') as f:
        f.write(header_str)
    rq3.to_csv(root / "data" / "results" / "rq3_actor_framing.csv", mode='a', index=False)
    print("Generated RQ3: rq3_actor_framing.csv")

if __name__ == "__main__":
    main()
