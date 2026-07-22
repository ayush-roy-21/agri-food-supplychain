import csv
import ast
from pathlib import Path

LOCI = {
    'internal-capability': ['cost', 'fee', 'expensive', 'lack', 'capacity', 'skill', 'scale', 'margin', 'afford', 'infrastructure'],
    'relational-power': ['buyer', 'agent', 'power', 'intermediary', 'monopoly', 'lead firm', 'dependence', 'contract', 'leverage'],
    'institutional-voids': ['fragmentation', 'uncertainty', 'stigma', 'ambiguous', 'unclear', 'overlap', 'contradiction', 'reputation', 'bias'],
    'informational-verifiability': ['proof', 'certificate', 'traceability', 'unverifiable', 'documentation', 'data', 'geotag', 'record', 'blockchain', 'digital']
}

def determine_loci(text_blob: str):
    text_blob = text_blob.lower()
    matches = {}
    for locus, terms in LOCI.items():
        count = sum(text_blob.count(term) for term in terms)
        if count > 0:
            matches[locus] = count
    
    if not matches:
        return 'inductive-other', ''
    
    sorted_matches = sorted(matches.items(), key=lambda x: x[1], reverse=True)
    primary = sorted_matches[0][0]
    secondary = sorted_matches[1][0] if len(sorted_matches) > 1 else ''
    return primary, secondary

def main():
    data_dir = Path('../../data').resolve()
    if not data_dir.exists():
        data_dir = Path('data').resolve()
    
    info_path = data_dir / "results" / "bertopic_topic_info.csv"
    out_path = data_dir / "results" / "topic_locus_mapping.csv"
    
    with open(info_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    out_rows = []
    for row in rows:
        topic_id = row.get("Topic", "")
        # skip noise if necessary, but we map all first
        
        rep_docs_str = row.get("Representative_Docs", "[]")
        try:
            docs = ast.literal_eval(rep_docs_str)
            blob = " ".join(docs)
        except:
            blob = rep_docs_str
        
        name = row.get("Name", "")
        rep = row.get("Representation", "")
        blob += " " + name + " " + rep
        
        primary, secondary = determine_loci(blob)
        
        # We need columns: Topic, locus_primary, locus_secondary, hurdle_name, evidence_doc_ids
        out_rows.append({
            "Topic": topic_id,
            "locus_primary": primary,
            "locus_secondary": secondary,
            "hurdle_name": f"Hurdle for Topic {topic_id}: {name}",
            "evidence_doc_ids": "See Representative Docs" # We don't have explicit doc IDs in this CSV easily, but this is a draft
        })

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Topic", "locus_primary", "locus_secondary", "hurdle_name", "evidence_doc_ids", "supervisor_signoff"])
        writer.writeheader()
        writer.writerows(out_rows)
        
    print(f"Created {out_path}")

if __name__ == "__main__":
    main()
