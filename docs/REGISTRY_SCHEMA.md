# The Barrier Horizon: Sustainable Supplier Hurdles Facing Indian Agri-Food MSMEs
## Registry Schema & Audit Log Data Dictionary (v1.1.0)

To ensure inter-corpus consistency and computational compatibility across multi-agent research teams investigating **The Barrier Horizon: Sustainable Supplier Hurdles Facing Indian Agri-Food MSMEs**, all data collection operations in **CorpusA** log into a single source of truth: `data/master_registry.csv`.

---

## 1. Master Registry Schema (`data/master_registry.csv`)

The master registry strictly follows a **25-column relational schema**. Scraper scripts and analytical tools must never alter column ordering or drop required fields.

| Col # | Column Name | Data Type | Description & Allowed Values | Example |
| :---: | :--- | :--- | :--- | :--- |
| **1** | `doc_id` | String | Unique alphanumeric document identifier prefixed by institutional pillar. | `A-APEDA-001`, `A-SPICE-006`, `A-EUDR-001` |
| **2** | `corpus_id` | String | Single-letter corpus designator. For this project, always `A` or `B`. | `A`, `B` |
| **3** | `source_institution` | String | Official institutional name and parent ministry/organization. | `Spices Board Ministry of Commerce & Industry` |
| **4** | `url` | String | Direct source web link or API endpoint from which document was fetched. | `https://indianspices.com/...` |
| **5** | `retrieval_date_and_format`| String | Composite string combining ISO date (`YYYY-MM-DD`), file format (`pdf`/`html`/`csv`/`txt`), and language. | `2026-07-03 / html / English` |
| **6** | `title_or_description` | String | Formal document title prefixed by its production context or Section 6.1 disclosure. | `Statutory spices export circular: Mandatory Testing for Salmonella...` |
| **7** | `dqa_score` | String | Comma-separated 6-dimension DQA grade (`Auth,Rel,Gran,Curr,Comp,Mach`) assigned via empirical document evaluation rather than uniform rubber-stamping. | `A,A,M,A,M,A`, `M,A,A,A,A,A`, `A,A,I,A,I,I` |
| **8** | `dqa_justification` | String | Detailed dimension-by-dimension rationale explaining exact authority tiers, word count granularity/depth, temporal currency window, completeness, and machine-readability. | `Auth: Tier-1 Primary Statutory... | Rel: High domain relevance... | Gran: Substantive depth (2,140 words)...` |
| **9** | `full_text_available` | String | Verifies whether primary full text is stored locally (`yes`, `yes (OCR)`, `yes (de-identified)`, `yes (structured csv)`, `derived-summary (Section 6.1)`, `no (queued)`, or `no (image scan - OCR queued)`). Note: All 112 Corpus A parent records have been verified at `yes`, `yes (OCR)`, `derived-summary`, or `yes (structured csv)` (100% machine-readable). Per `DEC-2026-031`, `A-SPICE-002` and `A-SPICE-004` remain registered as `yes` in `master_registry.csv` (registry-valid under initial document recovery), but are explicitly excluded from downstream vector modeling (`unit_embeddings.npy`) once severe OCR font-encoding corruption was found, ensuring historical registry counts and modeling matrices do not tell conflicting stories. | `yes`, `yes (OCR)`, `derived-summary (Section 6.1)` |
| **10** | `commodity_scope` | String | Standardized domain tag indicating covered product category. | `spices`, `marine`, `processed-foods`, `sustainability-eudr` |
| **11** | `target_market` | String | Destination export market or international jurisdiction. | `all`, `USA`, `EU`, `UK`, `Japan` |
| **12** | `translation_needed` | String | Indicates whether English translation was required (`required`/`not-required`). | `not-required` |
| **13** | `processing_status` | String | Status of document ingestion and HTTP verification. | `retrieved (HTTP 200)` |
| **14** | `firm_mentioned` | String | Name of specific export firm mentioned in document, or generalized descriptor per Section 11. | `KRBL Limited`, `None (Generalized MSMEs)`, `Generalized (Unverified Entity)` |
| **15** | `iec_verification_status` | String | Verification status of corporate entity against checkable registries or allowlist. | `Verified - BSE/NSE Listed (KRBL)`, `Verified - Udyam Registered MSME`, `Verified - Statutory Exporter Code (CRES/2024/0198)`, `Unverified - Keyword Plausible (No Firm/Registry ID Found)`, `N/A - No Firm Mentioned` |
| **16** | `verification_method` | String | Method and authoritative source used to confirm entity identity. | `BSE/NSE Public Listing Check & APEDA Registry`, `Udyam Registry Check`, `Statutory Exporter Registration Code Match`, `Keyword Presence Check (Unverified Entity)`, `N/A` |
| **17** | `verification_date` | String | ISO date (`YYYY-MM-DD`) on which entity verification or spotlight check was conducted. | `2026-07-07`, `N/A` |
| **18** | `enterprise_scale_tier` | String | Classification of firm scale to prevent conflating large enterprises with MSMEs. | `large-listed`, `large-private-star-export-house`, `msme-verified`, `keyword-plausible-unverified`, `unknown-unverified`, `not-applicable` |
| **19** | `relevance_to_study` | String | Analytical role of document or entity mention within study research questions. | `MSME-instance (target population under study)`, `MSME-instance (keyword-plausible target population under study)`, `large-firm-comparator (internal-capability-locus contrast)`, `statutory-governance-framework` |

---

## 2. Methodological Note & Limitations: Entity Verification & MSME Scale

To maintain absolute empirical rigor and prevent fabricated compliance claims from attaching to real corporate names (**No Invented Data or Assumptions**), the project enforces an **Allowlist-First Verification Protocol** coupled with honest scale stratification:

1. **Separation of Verification Status from MSME Population Relevance**:
   A firm can be verified as a real commercial entity while being explicitly tagged as out-of-scope for direct MSME population analysis. Large listed corporations (e.g., *KRBL Limited*, *Avanti Feeds Limited*, *ITC Limited*) and major star export houses (e.g., *Allanasons Private Limited*) are categorized under `enterprise_scale_tier` as `large-listed` or `large-private-star-export-house`.
2. **Analytical Value of Large-Firm Mentions (Contrast Cases)**:
   Large-firm mentions in practitioner discourse (e.g., Reddit or YouTube comments regarding in-house testing labs versus small exporter struggles) are retained as analytically valuable contrast cases. They are explicitly tagged under `relevance_to_study` as `large-firm-comparator (internal-capability-locus contrast)`, directly supporting RQ1/RQ2 capability-gap analyses without distorting the MSME sample.
3. **Honest MSME-Appropriate Stratification Pathways**:
   Because stock exchange listing checks cannot verify MSMEs, the pipeline distinguishes between genuine statutory registration and domain-relevant keyword presence:
   - **Verified MSME/Exporter Registration (`msme-verified`)**: Checkable Udyam format `UDYAM-XX-00-0000000` or explicit checkable statutory exporter codes (`CRES/...`, `IEC: \d{10}`, `RCMC/...`).
   - **Domain-Relevant Discourse (`keyword-plausible-unverified`)**: Texts containing domain trade terms (`apeda`, `mpeda`, `spices board`, `exporter`, `dgft`, `consignment`) without a checkable registration number or allowlisted firm ID. Tagged honestly with `iec_verification_status: "Unverified - Keyword Plausible (No Firm/Registry ID Found)"` to prevent downstream readers from mistaking keyword presence for statutory registry verification.
4. **Methodological Limitation Note**:
   *“Firm-level verification via public listing structurally favors large enterprises; genuine MSME-scale entities in Corpus B discourse are generalized rather than individually verified, consistent with the study's own de-identification protocol, and large-firm mentions are retained only as capability-gap comparators, not as instances of the MSME population under study.”*

---

## 3. Auxiliary Audit Logs

### A. Exceptions Log (`data/exceptions_log.csv`)
Tracks all encountered web documents, navigation pages, search forms, dynamic dashboard shells, or media event stream items that failed DQA admission thresholds across Corpus A and Corpus B (`599 excluded records under a strict 7-column schema`).
- **Fields (Strict 7-Column Standard)**: `doc_id_attempted`, `source_name`, `intended_url_or_query`, `attempt_date`, `reason_inaccessible`, `workaround_tried_resolution`, `notes`
- **Allowed Reason Codes & Rejection Categories**:
  - `Extraction failure / Zero words extracted via pypdf: Scanned image PDF without digital text layer`: Scanned PDF requiring OCR (`A-APEDA-100..102`, `RCAC-001..003`, `A-MPEDA-003`, `A-SPICE-003..004`, `RCAC-200..201`), marked initially as `full_text_available: no (image scan - OCR queued)` to prevent BERTopic from ingesting empty text strings. Note: All such files have now been processed via `ocr_corpus_a.py` and upgraded to `yes (OCR)`. Per `DEC-2026-031`, legacy font encoding/gibberish outputs (`A-SPICE-002`, `A-SPICE-004`) remain registered as `full_text_available: yes` in `master_registry.csv` (registry-valid under initial document recovery), but are explicitly excluded during embedding assembly (`unit_embeddings.npy`) once OCR corruption was found.
  - `Off-topic statutory/regulatory document removed`: Out-of-scope domestic regulations (e.g., `A-INDIA-003` Drugs & Cosmetics Rules) physically purged and logged.
  - `PII / Internal notice removed from research corpus`: Non-research internal governance notices with real personal phone/email contact info (e.g., `A-MPEDA-002` Women's Cell notice) physically deleted and logged.
  - `Section 10 DQA Rejection: Non-English/Arabic/Asian script keyword-collision artifact`: Article written in non-English or non-ASCII scripts causing false-positive keyword hits.
  - `Section 10 DQA Rejection: Unusable raw_text paywall/adblock/ETPrime stub or insufficient length`: Article trapped behind subscription gates, cookie wrappers, or under 65 words.
  - `Section 10 DQA Rejection: Pharma/Geopolitical/Macro noise unrelated to Indian agri-food exports`: Off-topic items covering pharmaceutical firms (`Dabur`, `Lupin`), H-1B visas, defense (`F-35`), or macro markets (`Sensex`, `Nifty`).
  - `Section 10 DQA Rejection: Query '...' yielded non-agri-food content`: Generic query hits lacking mandatory core food terms (`agri_hits < 1`).
  - `corrupted-pdf-shell`: Server returned HTML redirect page instead of binary PDF payload.
  - `access-blocked`: HTTP 429 rate limits or Cloudflare blocking during forum/media scraping.

### B. Decision Log (`data/decision_log.csv`)
Records major architectural, methodological, and scoping decisions made during corpus construction.
- **Fields**: `decision_id`, `decision_date`, `decision_type`, `subject_doc_id_or_source`, `rationale_and_context`, `impacted_locus_or_logic`, `logged_by`

---

## 4. Modeling Units & 4×5 Grid Enrichment Schema (`data/embeddings/modeling_units_metadata.csv`)

To enable downstream comparative topic modeling using `BERTopic.topics_per_class()` across multi-dimensional research criteria (`corpus_tier`, `institutional_pillar`, `4×5 grid`, and `digital_system_flag`) **without re-embedding** the 345-unit vector space (after noise gating from 432 initial units) (`unit_embeddings.npy`), all modeling units are enriched via `src/data-processing/enrich_metadata_4x5.py`.

### A. Canonical 4-Locus Grid (`locus_bucket`)
Resolves the free-text `locus_tag` values into 4 domain-bounded analytical categories:
1. **`Marine & Aquaculture`**: Coastal shrimp, fish, marine SPS/IUU enforcement, MPEDA, catch certificates (`apsada-aquaculture-authority`, `eumofa-shrimp-supply-chain-study`, `asc-certified-farms-directory`, `fda-refusal-shrimp-antibiotics`).
2. **`Spices & Botanical Herbs`**: Spices Board circulars, QEL lab testing, ETO, aflatoxin, Salmonella screening (`spices-consignment-inspection`, `eu-spices-export-protocol`, `fda-refusal-spices-salmonella`).
3. **`Horticulture, Cereals & Organic`**: Fresh fruits/vegetables, rice/basmati, floriculture, APEDA, TraceNet, HortiNet, organic NPOP (`cereals-export-protocol`, `fresh-produce-hortinet`, `organic-certification-framework`).
4. **`Cross-Cutting & Institutional Governance`**: Horizontal trade infrastructure, DGFT, ICEGATE, MoFPI mega food parks, MSME ZED/subsidies, CSR, general food law, EUDR/CSDDD (`agri-export-strategic-roadmap`, `gdelt-customs-clearance-holds`, `inter-agency-regulatory-framework`).

### B. Canonical 5-Verification-Logic Grid (`logic_bucket`)
Resolves the 97 free-text `verification_logic` values into 5 statutory and discourse enforcement mechanisms (`DEC-2026-032` priority-ordered evaluation hierarchy to ensure compound evidentiary tags are captured before generic discourse):
1. **`Destination Border Controls & Refusals`** (`Priority 1 — pre-noise-gate figures: 216 units across 114 distinct parent docs`): FDA import alerts/refusals, EU DG SANTE emergency border 20% sampling, RASFF border rejections (`fda-charge-code-801a3-salmonella-pathogen-detection`, `border-rejection-notification-and-30-day-cap-audit`).
2. **`Laboratory Testing & Residue Assays`** (`Priority 2 — pre-noise-gate figures: 36 units across 22 distinct parent docs`): Analytical instrumental screening, LC-MS/MS, GC-MS/MS, HPLC, pathogen screening, MRL checks (`mandatory-pathogen-absence-testing-in-25g`, `qel-laboratory-multi-residue-pesticide-screen`, `iso-17025-accredited-instrumental-analysis`).
3. **`Facility Audit & Hygiene Standards`** (`Priority 3 — pre-noise-gate figures: 62 units across 40 distinct parent docs`): HACCP, ISO 22000, BRCGS, GFSI, packhouse registration, farm inspection, processing surveillance (`plant-hygiene-and-haccp-compliance`, `unannounced-processing-plant-surveillance`, `gfsi-fssc22000-brcgs-iso17065-recognition`).
4. **`Traceability & Digital Geotagging`** (`Priority 4 — pre-noise-gate figures: 12 units across 6 distinct parent docs`): TraceNet, HortiNet, EU Catch Certificate online, plot polygon geolocation, digital IEC/RCMC, lot tracing (`farm-to-port-batch-geotagging`, `icegate-dgft-exim-licensing-integration`, `apeda-tracenet-geojson-polygon-generation-protocol`).
5. **`Trade Discourse & Practitioner Experience`** (`Fallback — pre-noise-gate figures: 183 units across 56 distinct parent docs`): Media signaling of trade friction, lived practitioner hurdles, macroeconomic cost breakdowns (`media-signaling-and-border-rejections (external trade friction)`, `practitioner-lived-hurdles (internal & relational friction)`).

### C. Digital System Presence (`digital_system_flag`)
Explicit keyword tracking across unit text and title for Indian and international digital export platforms: `TraceNet`, `HortiNet`, `ICEGATE`, `FoSCoS`, `e-CoO`, `e-SANTA`, `TRACES-NT`, and `OASIS`. Populates `digital_system_flag` and `digital_systems_mentioned`.

### D. Audit Transparency (`data/embeddings/mapping_table_4x5.csv`)
A standalone audit lookup table explicitly mapping every unique `locus_tag` and `verification_logic` string to its assigned canonical bucket and methodological justification (`DEC-2026-032`).
