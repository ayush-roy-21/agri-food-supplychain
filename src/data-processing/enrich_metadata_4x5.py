"""
src/data-processing/enrich_metadata_4x5.py

Enriches `data/embeddings/modeling_units_metadata.csv` with canonical class variables
required for downstream BERTopic modeling (`topics_per_class`), without altering
the existing embedding matrix (`unit_embeddings.npy`).

Adds 4 analytical dimensions derived via joins against `master_registry.csv` and text:
1. `corpus_tier`: Institutional vs. practitioner framing (already present, verified).
2. `institutional_pillar`: Cleaned canonical source categories from `source_name_instrument_body`.
3. `locus_bucket` & `logic_bucket` (`grid_bucket`): Mapped down from 121 distinct `locus_tag`
   and 97 distinct `verification_logic` free-text strings to the canonical 4×5 grid.
4. `digital_system_flag` & `digital_systems_mentioned`: Keyword-tagged presence of digital
   export systems (TraceNet, HortiNet, ICEGATE, FoSCoS, e-CoO, e-SANTA, TRACES-NT, OASIS).

Also exports a standalone mapping table `data/embeddings/mapping_table_4x5.csv` for audit transparency.

Usage:
    python src/data-processing/enrich_metadata_4x5.py
"""

import csv
from pathlib import Path
import pandas as pd

# 1. Canonical Mapping Definitions for Locus (4 categories)
def map_locus_bucket(locus_tag: str) -> str:
    if pd.isna(locus_tag) or not str(locus_tag).strip():
        return "Cross-Cutting & Institutional Governance"
    
    t = str(locus_tag).strip().lower()
    
    # Marine / Seafood / Aquaculture domain
    if any(k in t for k in ['marine', 'aquaculture', 'seafood', 'shrimp', 'fish', 'mpeda', 'catch', 'eumofa', 'iuu', 'noaa', 'apsada', 'dwpe-alerts', 'asc-certified']):
        return "Marine & Aquaculture"
    
    # Spices & Botanical Herbs domain
    elif any(k in t for k in ['spice', 'cumin', 'chilli', 'cardamom', 'turmeric', 'qel', 'salmonella', 'aflatoxin', 'eto', 'flavour']):
        return "Spices & Botanical Herbs"
    
    # Horticulture, Cereals, Basmati & Organic domain
    elif any(k in t for k in ['horticulture', 'cereal', 'rice', 'basmati', 'organic', 'floriculture', 'apeda', 'tracenet', 'hortinet', 'produce', 'fruit']):
        return "Horticulture, Cereals & Organic"
    
    # Cross-Cutting & Institutional Governance domain
    else:
        return "Cross-Cutting & Institutional Governance"

# 2. Canonical Mapping Definitions for Verification Logic (5 categories)
def map_logic_bucket(logic_tag: str) -> str:
    if pd.isna(logic_tag) or not str(logic_tag).strip():
        return "Facility Audit & Hygiene Standards"
    
    l = str(logic_tag).strip().lower()
    
    # NOTE (fix applied after 5x4 grid coverage audit): the original check
    # order put 'Trade Discourse' first, and its keyword 'media-signaling'
    # is a substring of the single most common verification_logic value in
    # the corpus -- "media-signaling-and-border-rejections (external trade
    # friction)" -- which ALSO contains 'border-rejection'. Checking the
    # generic bucket first meant that value (and 5 similar compound tags)
    # always won before the more specific, more evidentially important
    # category could be tested. Affected 210 of 509 units (41.3% of the
    # corpus) -- Destination Border Controls & Refusals was undercounted
    # at 6 units when it should be 216. Fix: check specific/high-value
    # categories first, generic 'Trade Discourse' last before the
    # statutory default.

    # Destination Border Controls & Refusals
    if any(k in l for k in ['border-rejection', 'fda-charge', 'import-alert', '20pct-physical-sampling', 'bcp-documentary', 'refusal']):
        return "Destination Border Controls & Refusals"

    # Laboratory Testing & Residue Assays
    elif any(k in l for k in ['testing', 'assay', 'screening', 'laboratory', 'hplc', 'lc-ms-ms', 'gc-ms-ms', 'mrl', 'nabl', 'sampling', 'chloramphenicol', 'nitrofuran', 'pathogen', 'residue', 'aflatoxin', 'eto', 'iso-17025']):
        return "Laboratory Testing & Residue Assays"

    # Traceability & Digital Geotagging
    elif any(k in l for k in ['trace', 'tracenet', 'geotagg', 'polygon', 'e-coo', 'catch-certificate-online', 'icegate', 'digital', 'one-step', 'shipping-bill']):
        return "Traceability & Digital Geotagging"

    # Trade Discourse & Practitioner Experience (generic catch-all, checked
    # last among the four "positive" categories)
    elif any(k in l for k in ['media-signaling', 'practitioner-lived', 'direct-institutional', 'public-forum', 'discourse', 'cost-breakdown', 'assessment-metrics', 'export-protocol', 'multi-year-commodity', 'origin-level-hazard', 'general-food-law', 'duty-scrip', 'trade-policy', 'good-agricultural-practices-farm-assurance']):
        return "Trade Discourse & Practitioner Experience"

    # Facility Audit, Inspection & Hygiene Standards (default statutory enforcement)
    else:
        return "Facility Audit & Hygiene Standards"

# 3. Canonical Mapping for Institutional Pillar (cleaned from source_name_instrument_body)
def map_institutional_pillar(source_name: str, corpus_tier: str, parent_doc_id: str = "", locus_tag: str = "") -> str:
    if corpus_tier == "B" and any(k in str(parent_doc_id).lower() for k in ["b-yt", "b-rd", "b-gd"]):
        return "Practitioner & Media Discourse"
    
    s = f"{source_name if not pd.isna(source_name) else ''} {parent_doc_id} {locus_tag}".strip()
    s_low = s.lower()
    
    if any(k in s_low for k in ["apeda", "rcac-"]):
        return "APEDA (Agricultural & Processed Food Authority)"
    elif any(k in s_low for k in ["spices board", "a-spice-"]):
        return "Spices Board of India"
    elif any(k in s_low for k in ["mpeda", "a-mpeda-"]):
        return "MPEDA (Marine Products Export Authority)"
    elif any(k in s_low for k in ["eic", "eia", "export inspection", "a-eic-"]):
        return "EIC/EIA (Export Inspection Council)"
    elif any(k in s_low for k in ["fssai", "a-fssai-"]):
        return "FSSAI (Food Safety Authority of India)"
    elif any(k in s_low for k in ["dg sante", "european commission", "eu ", "eur-lex", "rasff", "a-eu-", "a-eudr-"]):
        return "EU DG SANTE / European Commission"
    elif any(k in s_low for k in ["fda", "us food and drug", "noaa", "a-fda-", "a-iec-"]):
        return "US FDA / US Regulatory Agencies"
    elif any(k in s_low for k in ["dgft", "ministry of commerce", "icegate", "customs", "a-dgft-"]):
        return "DGFT & Ministry of Commerce"
    elif any(k in s_low for k in ["mofpi", "msme", "niti", "csr", "zed", "pib", "a-mofpi-", "a-msme-", "a-zed-", "a-csr-"]):
        return "Domestic Infrastructure & Capacity (MoFPI/MSME/NITI/CSR)"
    elif any(k in s_low for k in ["supplychain_research", "eudr_csddd", "macro_exim_data", "academic", "research"]):
        return "Academic & Strategic Research Pool"
    elif any(k in s_low for k in ["gdelt", "youtube", "reddit", "media"]):
        return "Practitioner & Media Discourse"
    else:
        return "General Statutory & State Gazette"

# 4. Keyword Tagging for Digital Systems (RQ3)
DIGITAL_SYSTEMS_MAP = {
    "TraceNet": ["tracenet"],
    "HortiNet": ["hortinet"],
    "ICEGATE": ["icegate"],
    "FoSCoS": ["foscos"],
    "e-CoO": ["e-coo"],
    "e-SANTA": ["e-santa"],
    "TRACES-NT": ["traces-nt", "traces nt"],
    "OASIS": ["oasis portal", "oasis system"]
}

def tag_digital_systems(text: str, locus: str, logic: str) -> tuple[str, str]:
    combined = (str(text) + " " + str(locus) + " " + str(logic)).lower()
    found = []
    for sys_name, keywords in DIGITAL_SYSTEMS_MAP.items():
        if any(kw in combined for kw in keywords):
            found.append(sys_name)
    
    if found:
        return "Yes", ", ".join(sorted(set(found)))
    else:
        return "No", "None"

def main():
    root_dir = Path(__file__).resolve().parent.parent.parent
    registry_path = root_dir / "data" / "master_registry.csv"
    metadata_path = root_dir / "data" / "embeddings" / "modeling_units_metadata.csv"
    mapping_out_path = root_dir / "data" / "embeddings" / "mapping_table_4x5.csv"
    
    print(f"[*] Loading master registry from: {registry_path}")
    reg_df = pd.read_csv(registry_path)
    
    # Create lookup map from master_registry for source_name_instrument_body
    source_map = dict(zip(reg_df["doc_id"], reg_df["source_name_instrument_body"]))
    
    print(f"[*] Loading modeling units metadata from: {metadata_path}")
    meta_df = pd.read_csv(metadata_path)
    print(f"    Total units loaded: {len(meta_df)}")
    
    # 1. Map locus_bucket and logic_bucket
    meta_df["locus_bucket"] = meta_df["locus_tag"].apply(map_locus_bucket)
    meta_df["logic_bucket"] = meta_df["verification_logic"].apply(map_logic_bucket)
    meta_df["grid_bucket"] = meta_df["locus_bucket"] + " × " + meta_df["logic_bucket"]
    
    # 2. Map institutional_pillar
    meta_df["source_name_instrument_body"] = meta_df["parent_doc_id"].map(source_map)
    meta_df["institutional_pillar"] = meta_df.apply(
        lambda row: map_institutional_pillar(row.get("source_name_instrument_body"), row["corpus_tier"], row["parent_doc_id"], row["locus_tag"]),
        axis=1
    )
    
    # 3. Tag digital systems
    digital_flags = []
    digital_names = []
    for _, row in meta_df.iterrows():
        flag, names = tag_digital_systems(row["text"], row["locus_tag"], row["verification_logic"])
        digital_flags.append(flag)
        digital_names.append(names)
    meta_df["digital_system_flag"] = digital_flags
    meta_df["digital_systems_mentioned"] = digital_names
    
    # Export enriched metadata
    meta_df.to_csv(metadata_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
    print(f"[*] Saved enriched modeling units metadata ({len(meta_df)} rows, {len(meta_df.columns)} columns) to: {metadata_path}")
    
    # Build and export standalone mapping table for all distinct locus and logic values across dataset
    all_loci = sorted(set(reg_df["locus_tag"].dropna()).union(set(meta_df["locus_tag"].dropna())))
    all_logics = sorted(set(reg_df["verification_logic"].dropna()).union(set(meta_df["verification_logic"].dropna())))
    
    mapping_rows = []
    for loc in all_loci:
        mapping_rows.append({
            "tag_type": "locus_tag",
            "free_text_value": loc,
            "canonical_bucket": map_locus_bucket(loc),
            "justification": "Mapped via domain keyword boundaries to 4-Locus Grid"
        })
    for log in all_logics:
        mapping_rows.append({
            "tag_type": "verification_logic",
            "free_text_value": log,
            "canonical_bucket": map_logic_bucket(log),
            "justification": "Mapped via regulatory inspection/testing/traceability mechanism to 5-Logic Grid"
        })
    
    mapping_df = pd.DataFrame(mapping_rows)
    mapping_df.to_csv(mapping_out_path, index=False)
    print(f"[*] Saved standalone 4x5 mapping lookup table ({len(mapping_df)} rows) to: {mapping_out_path}")
    
    # Summary of enrichment
    print("\n==========================================================================")
    print(f"                      ENRICHMENT SUMMARY ({len(meta_df)} UNITS)")
    print("==========================================================================")
    print("\n1. Corpus Tier (`corpus_tier`):")
    print(meta_df["corpus_tier"].value_counts().to_string())
    
    print("\n2. Institutional Pillar (`institutional_pillar`):")
    print(meta_df["institutional_pillar"].value_counts().to_string())
    
    print("\n3. Locus Buckets (`locus_bucket` - 4 Loci):")
    print(meta_df["locus_bucket"].value_counts().to_string())
    
    print("\n4. Logic Buckets (`logic_bucket` - 5 Verification Logics):")
    print(meta_df["logic_bucket"].value_counts().to_string())
    
    print("\n5. Digital System Presence (`digital_system_flag`):")
    print(meta_df["digital_system_flag"].value_counts().to_string())
    print("\n   Top mentioned digital systems:")
    print(meta_df[meta_df["digital_system_flag"]=="Yes"]["digital_systems_mentioned"].value_counts().to_string())
    print("==========================================================================")

if __name__ == "__main__":
    main()