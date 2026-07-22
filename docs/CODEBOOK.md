# CODEBOOK: The Barrier Horizon
**Sustainable Supplier Hurdles Facing Indian Agri-Food MSMEs**

This codebook dictates the canonical qualitative taxonomy governing Corpus A and Corpus B. It outlines the structural mapping rules applied to raw documents during Stage 4 metadata enrichment (`enrich_metadata_4x5.py`) prior to vector embedding. 

---

## 1. The Four Loci (Commodity Scopes)
Documents and modeling units are categorized into one of four primary thematic loci based on substantive commodity exposure.

### 1.1 Marine & Aquaculture
**Definition**: Pertains to the regulatory hurdles, pre-shipment inspections, and international border compliance mandates targeting the seafood and aquaculture export sector. This locus is fundamentally driven by marine health certification, catch traceability, and residue monitoring mechanisms enforced by institutional bodies such as MPEDA, EIC, EU DG SANTE, and the US FDA/NOAA.
**Mapping Terms**: `['marine', 'aquaculture', 'seafood', 'shrimp', 'fish', 'mpeda', 'catch', 'eumofa', 'iuu', 'noaa', 'apsada', 'dwpe-alerts', 'asc-certified']`

### 1.2 Spices & Botanical Herbs
**Definition**: Encompasses the statutory testing regimes, pathogen monitoring requirements, and non-tariff friction affecting spice exporters. This locus captures both domestic institutional oversight by the Spices Board of India and specific destination market testing constraints such as mandatory sampling for Salmonella, Aflatoxin, and pesticide residue limits (MRLs).
**Mapping Terms**: `['spice', 'cumin', 'chilli', 'cardamom', 'turmeric', 'qel', 'salmonella', 'aflatoxin', 'eto', 'flavour']`

### 1.3 Horticulture, Cereals & Organic
**Definition**: Covers the export protocols, phytosanitary requirements, and organic certification standards applicable to fresh produce, cereals (e.g., Basmati rice), and processed horticultural products. It focuses heavily on APEDA's structural mandate, National Programme for Organic Production (NPOP) equivalence, and farm-level traceability systems.
**Mapping Terms**: `['horticulture', 'cereal', 'rice', 'basmati', 'organic', 'floriculture', 'apeda', 'tracenet', 'hortinet', 'produce', 'fruit']`

### 1.4 Cross-Cutting & Institutional Governance
**Definition**: Serves as the macro-level aggregation and fallback locus for regulatory frameworks, trade discourse, and institutional policy changes that impact multiple agricultural commodities simultaneously or lack a singular commodity focus. This includes general export-import licensing (IEC), overarching FTP mandates by DGFT, and domestic food safety overlaps via FSSAI.
**Mapping Terms**: Applies automatically when documents do not match the specific mapping terms of the three primary commodity loci.

---

## 2. The Five Verification Logics
Verification logic categorizes the nature of the institutional compliance test or the operational hurdle encountered by the exporter.

### 2.1 Destination Border Controls & Refusals
Represents instances of external trade friction where export consignments are intercepted, sampled, or rejected upon reaching international destination markets (e.g., EU border sampling, FDA Import Refusals).
**Mapping Terms**: `['border-rejection', 'fda-charge', 'import-alert', '20pct-physical-sampling', 'bcp-documentary', 'refusal']`

### 2.2 Laboratory Testing & Residue Assays
Involves the pre-shipment or mandatory analytical testing required to prove compliance with domestic or international Maximum Residue Limits (MRLs), microbiological thresholds, and pathogen absence.
**Mapping Terms**: `['testing', 'assay', 'screening', 'laboratory', 'hplc', 'lc-ms-ms', 'gc-ms-ms', 'mrl', 'nabl', 'sampling', 'chloramphenicol', 'nitrofuran', 'pathogen', 'residue', 'aflatoxin', 'eto', 'iso-17025']`

### 2.3 Traceability & Digital Geotagging
Encompasses the mandatory digital governance mechanisms and farm-level polygon mapping systems required to prove product origin and combat issues like deforestation or IUU fishing.
**Mapping Terms**: `['trace', 'tracenet', 'geotagg', 'polygon', 'e-coo', 'catch-certificate-online', 'icegate', 'digital', 'one-step', 'shipping-bill']`

### 2.4 Trade Discourse & Practitioner Experience
Captures the lived operational hurdles, financial friction, and localized discourse surrounding compliance, primarily observed in Corpus B practitioner communities (Reddit, YouTube) or macro-level trade policy discussions.
**Mapping Terms**: `['media-signaling', 'practitioner-lived', 'direct-institutional', 'public-forum', 'discourse', 'cost-breakdown', 'assessment-metrics', 'export-protocol', 'multi-year-commodity', 'origin-level-hazard', 'general-food-law', 'duty-scrip', 'trade-policy', 'good-agricultural-practices-farm-assurance']`

### 2.5 Facility Audit & Hygiene Standards
Covers internal capability audits, HACCP/GFSI certification regimes, and basic pre-requisite hygiene standards required for processing plant approvals.
**Mapping Terms**: Default statutory logic applied when more specific enforcement tags are not triggered.

---

## 3. Actor Vocabulary
To prevent the conflation of large capital-rich enterprises with the target MSME sample under study, all entities extracted from Corpus A and B must adhere to the following scale and verification tiers:

- **Large-Listed / Large-Private-Star-Export-House**: Capital-rich enterprises (e.g., *KRBL Limited*, *Avanti Feeds Limited*). Kept strictly separate from the core MSME target sample, these entities serve only as **analytical contrast cases** (`large-firm-comparator (internal-capability-locus contrast)`) to highlight institutional capacity gaps.
- **MSME-Verified**: Exporters authenticated via statutory registration strings (e.g., Udyam IDs `UDYAM-XX-00-0000000` or explicit RCMC codes).
- **Keyword-Plausible-Unverified**: Smallholder practitioners and domain commenters in Corpus B lacking checkable statutory IDs but participating in relevant trade discourse. Tagged appropriately to distinguish conversational data from statutory verification.
- **Institutional Regulators**:
    - **Domestic**: APEDA, Spices Board, MPEDA, EIC, FSSAI, DGFT.
    - **International**: EU DG SANTE, US FDA/NOAA.

## 4. Term-List Mapping Priority Rules
When executing automated classification (e.g., via `enrich_metadata_4x5.py`), the parsing engine evaluates strings based on the following prioritization to prevent over-counting generic tags:
1. Destination Border Controls & Refusals (Highest evidentiary value)
2. Laboratory Testing & Residue Assays
3. Traceability & Digital Geotagging
4. Trade Discourse & Practitioner Experience (Evaluated last among the specific categories)
5. Facility Audit & Hygiene Standards (Catch-all statutory fallback)
