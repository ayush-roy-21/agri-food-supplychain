# CODEBOOK: The Barrier Horizon
**Sustainable Supplier Hurdles Facing Indian Agri-Food MSMEs**

This codebook dictates the canonical qualitative taxonomy governing Corpus A and Corpus B. It outlines the structural mapping rules applied to raw documents during Stage 4 metadata enrichment.

---

## 1. The Four Loci
Documents and modeling units are categorized into one of four theoretical loci representing the origin and nature of the hurdle facing the MSME.

### 1.1 Internal Capability
**Definition**: Encompasses the operational, financial, and technical constraints originating directly from within the MSME itself. This includes the lack of in-house accredited testing laboratories, inadequate capital to invest in HACCP/ISO compliance infrastructure, and insufficient technical know-how to navigate complex international SPS regulations. It represents the firm-level hurdles before interaction with external actors.
**Mapping Terms**: `['in-house', 'capital', 'training', 'infrastructure', 'compliance cost', 'capacity', 'technical barrier', 'quality control', 'financial constraint']`

### 1.2 Relational Power
**Definition**: Describes the systemic power asymmetries, negotiating friction, and contractual hurdles between MSMEs and larger, more dominant supply chain actors. This locus covers the struggles of smallholders when dealing with large star export houses, monopolistic third-party logistics providers, intermediary brokers, and large international buyers who dictate pricing and compliance terms.
**Mapping Terms**: `['buyer', 'contract', 'asymmetry', 'middleman', 'broker', 'logistics provider', 'star export house', 'negotiation', 'pricing power', 'intermediary']`

### 1.3 Institutional Voids
**Definition**: Captures the absence, failure, or inefficiency of supporting regulatory and infrastructural environments. This includes backlogs at government testing laboratories, missing local state-level certification bodies, fragmented multi-agency licensing processes (e.g., FSSAI vs DGFT), and the lack of accessible cold-chain or public transport infrastructure necessary for safe export.
**Mapping Terms**: `['delay', 'backlog', 'government lab', 'infrastructure', 'cold chain', 'fragmentation', 'multi-agency', 'bureaucracy', 'public transport', 'void']`

### 1.4 Informational Verifiability
**Definition**: Details the hurdles associated with proving compliance, product origin, and traceability through digital or documentary means. It focuses on the friction created by mandatory digital governance mechanisms, such as complex TraceNet polygon mapping, EUDR digital geotagging, e-CoO generation, and the opacity of destination border documentary requirements.
**Mapping Terms**: `['traceability', 'polygon', 'geotagging', 'tracenet', 'eudr', 'digital', 'documentary', 'proof', 'certification', 'opacity', 'verification']`

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
When executing automated classification, the parsing engine evaluates strings based on the following prioritization to prevent over-counting generic tags:
1. Destination Border Controls & Refusals (Highest evidentiary value)
2. Laboratory Testing & Residue Assays
3. Traceability & Digital Geotagging
4. Trade Discourse & Practitioner Experience (Evaluated last among the specific categories)
5. Facility Audit & Hygiene Standards (Catch-all statutory fallback)
