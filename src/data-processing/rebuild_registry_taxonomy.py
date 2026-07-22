import csv
from pathlib import Path

# Mapping terms from proposed CODEBOOK
VERIFICATION_LOGICS = {
    'residue-and-mrl': ['testing', 'assay', 'screening', 'laboratory', 'hplc', 'lc-ms-ms', 'gc-ms-ms', 'mrl', 'nabl', 'sampling', 'pathogen', 'residue', 'aflatoxin', 'eto', 'salmonella'],
    'catch-legality-aquaculture': ['marine', 'aquaculture', 'catch', 'iuu', 'chloramphenicol', 'nitrofuran', 'pht', 'catch-certificate'],
    'land-use-geolocation': ['trace', 'tracenet', 'geotagg', 'polygon', 'deforestation', 'eudr', 'land-use', 'farm-mapping'],
    'facility-and-process': ['audit', 'hygiene', 'haccp', 'iso-17025', 'facility', 'plant', 'packhouse', 'gfsi', 'inspection']
}

LOCI = {
    'internal-capability': ['cost', 'fee', 'expensive', 'lack', 'capacity', 'skill', 'scale', 'margin', 'afford', 'infrastructure'],
    'relational-power': ['buyer', 'agent', 'power', 'intermediary', 'monopoly', 'lead firm', 'dependence', 'contract', 'leverage'],
    'institutional-voids': ['fragmentation', 'uncertainty', 'stigma', 'ambiguous', 'unclear', 'overlap', 'contradiction', 'reputation', 'bias'],
    'informational-verifiability': ['proof', 'certificate', 'traceability', 'unverifiable', 'documentation', 'data', 'geotag', 'record', 'blockchain', 'digital']
}

def determine_logic(text_blob: str) -> str:
    text_blob = text_blob.lower()
    for logic, terms in VERIFICATION_LOGICS.items():
        for term in terms:
            if term in text_blob:
                return logic
    return 'not-applicable'

def determine_locus(text_blob: str) -> str:
    text_blob = text_blob.lower()
    for locus, terms in LOCI.items():
        for term in terms:
            if term in text_blob:
                return locus
    return 'not-applicable'

def main():
    data_dir = Path('../../data').resolve()
    if not data_dir.exists():
        data_dir = Path('data').resolve()
    
    registry_path = data_dir / "master_registry.csv"
    
    with open(registry_path, "r", encoding="utf-8-sig") as f:
        reader = list(csv.DictReader(f))
        fieldnames = list(reader[0].keys())

    if "source_topic_tag" not in fieldnames:
        idx = fieldnames.index("locus_tag")
        fieldnames.insert(idx + 1, "source_topic_tag")

    undecidable = 0
    for row in reader:
        if "source_topic_tag" not in row or not row["source_topic_tag"]:
            row["source_topic_tag"] = row["locus_tag"]
            
        text_blob = f"{row.get('production_context', '')} {row.get('source_topic_tag', '')} {row.get('title_url_query', '')}".lower()
        
        row["verification_logic"] = determine_logic(text_blob)
        loc = determine_locus(text_blob)
        if loc == 'not-applicable':
            undecidable += 1
            loc = 'inductive-other'
        row["locus_tag"] = loc

    print(f"Total rows: {len(reader)}. Undecidable/inductive-other loci: {undecidable}")

    with open(registry_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reader)

if __name__ == "__main__":
    main()
