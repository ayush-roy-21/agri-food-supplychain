# The Barrier Horizon: Sustainable Supplier Hurdles Facing Indian Agri-Food MSMEs
## Data Collection & Quality Assessment Protocol

This protocol outlines the automated scraping workflow, verification standards, and Data Quality Assessment (DQA) methodology enforced across **The Barrier Horizon: Sustainable Supplier Hurdles Facing Indian Agri-Food MSMEs (CorpusA)**.

---

## 1. Automated Scraper Workflow & SSL Relaxation Protocol (`DEC-2026-001`)

Indian institutional portals (such as National Informatics Centre `NIC` hosted domains: `apeda.gov.in`, `mpeda.gov.in`, `eicindia.gov.in`, `fssai.gov.in`, `dgft.gov.in`) frequently deploy legacy or non-standard SSL certificate chains that cause standard Python HTTP libraries (`urllib` or `requests`) to throw `ssl.SSLCertVerificationError` or handshake failures.

To ensure uninterrupted institutional data retrieval without altering underlying endpoint addresses, all scraper modules implement protocol **`DEC-2026-001`**:
```python
import ssl
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE
```
*Note: This SSL context relaxation is restricted exclusively to read-only institutional data collection scrapers.*

---

## 2. PDF Corruption Prevention & Binary Header Verification

Automated web scraping of government circular pages often encounters redirects where a URL ending in `.pdf` actually returns an HTML session expiration or login shell. Saving such responses directly creates corrupted unreadable PDF files.

To safeguard corpus integrity, all scrapers enforce **magic header verification**:
1. When downloading a candidate binary document, the scraper inspects the initial bytes (`data[:5]`).
2. Only payloads starting with the signature `b"%PDF-"` are written to disk with a `.pdf` extension.
3. If the payload returns an HTML structure or fails magic header validation, the scraper rejects the corrupted PDF shell and falls back to extracting/saving the authoritative procedure narrative as structured UTF-8 text (`.txt`).

---

## 3. Data Quality Assessment (DQA) Framework

Every document admitted to Corpus A and Corpus B undergoes empirical, multi-dimensional evaluation across **six quality dimensions (`Auth,Rel,Gran,Curr,Comp,Mach`)** rather than uniform rubber-stamping (`A,A,A,A,A,A`).

### The 6 Empirical DQA Dimensions:
1. **Authority (Auth)**: Source legitimacy (`A`: Tier-1 Primary Statutory / Institutional body vs `M`: Tier-2 Academic / Industry / Media study).
2. **Relevance (Rel)**: Direct alignment with agri-food/marine MSME export compliance (`A`: High domain relevance vs `M`: Moderate/Macro MSME competitiveness survey).
3. **Granularity (Gran)**: Substantive depth evaluated by exact word count (`A`: Substantive depth $\ge 600$ words or complete structured registry profile vs `M`: Overview/derived summary $100-599$ words vs `I`: Stub or zero extracted text $< 100$ words).
4. **Currency (Curr)**: Temporal applicability (`A`: Active policy window $2024-2026$ vs `M`: Prior background reference period $2018-2023$).
5. **Completeness (Comp)**: Document integrity (`A`: Complete operative text extracted $\ge 600$ words vs `M`: Summary orientation excerpt vs `I`: Incomplete / zero words extracted via pypdf).
6. **Machine Readability (Mach)**: Computational accessibility (`A`: Clean UTF-8 text layer vs `M`: Multi-column PDF with table noise vs `I`: Image-only PDF / extraction failure without text layer).

### Scanned Image PDF & Zero-Word Extraction Protocol:
When local `pypdf` extraction encounters scanned/image PDFs without a digital OCR text layer (`word_count == 0`), the pipeline explicitly prevents false full-text registration:
- Skips writing empty `.txt` files on disk.
- Sets `"full_text_available": "no (image scan - OCR queued)"` inside `master_registry.csv` to ensure downstream `BERTopic` topic modeling pipelines cleanly ignore empty documents.
- Assigns exact `I` (Inadequate) grades across Granularity, Completeness, and Machine-Readability (`A,A,I,A,I,I` or `M,A,I,A,I,I`) and logs the item to `exceptions_log.csv`.

### OCR Quality Verification & Scraper Noise Exclusions (`DEC-2026-031`):
While optical character recognition (`ocr_corpus_a.py`) successfully recovers text from most scanned PDFs and image infographics (`RCAC-001..003`, `A-MPEDA-003`, `RCAC-200..201`), post-OCR quality audit (`DEC-2026-031`) revealed that OCR output cannot be uniformly assumed 100% legible across legacy font encodings or low-DPI scans:
1. **Parent-Level Corrupted OCR Exclusions (`A-SPICE-002`, `A-SPICE-004`)**: Two Corpus A documents (`A-SPICE-002` and `A-SPICE-004`) exhibited severe OCR/encoding corruption (`A-SPICE-002-C03` yielded 71% non-printable/non-ASCII garbled font-encoding characters, and `A-SPICE-004-C04` produced mis-OCR'd gibberish). Both parent documents and their chunks are explicitly flagged inside `EXCLUDED_CORRUPT_OR_NOISY_PARENTS` across `chunk_documents.py` and `generate_embeddings.py`, removing them from the modeling unit pool (`assemble_modeling_units()`) to prevent garbled tokens from degrading embedding representations. Note: Both `A-SPICE-002` and `A-SPICE-004` remain registered as `full_text_available: yes` in `master_registry.csv` (registry-valid under initial document recovery), but are explicitly modeling-excluded per `DEC-2026-031` once OCR corruption was found, so historical registry counts and modeling matrices do not tell conflicting stories.
2. **Chunk-Level Scraper Tail Artifact Exclusions**: During web scraping (`gdelt_pipeline.py`), three GDELT parent documents (`B-GD-020`, `B-GD-029`, `B-GD-088`) captured legitimate primary article text across their initial chunks, but ingested non-substantive footer/cookie-consent scraper noise at the tail end of the page (`B-GD-020-C05/C06`, `B-GD-029-C05/C06`, `B-GD-088-C03/C04`). These specific noisy end-chunks are filtered out via `EXCLUDED_CORRUPT_OR_NOISY_CHUNKS`, preserving the clean substantive parent text while guaranteeing 100% discourse purity in the final 509-unit embedding matrix (`unit_embeddings.npy`).

---

## 4. Academic Transparency & Section 6.1 Compliance

Per **Section 6.1** of our research governance guidelines, researchers must maintain absolute transparency regarding whether a document represents verbatim primary statutory text or a curated regulatory summary.

### Distinction & Logging Rules:
- **Primary Verbatim Scrapes**: Documents retrieved directly from official gazette servers or EUR-Lex HTML endpoints without modification are logged with `full_text_available: yes`.
- **Derived Regulatory Summaries**: When anti-bot security layers (`HTTP 403` Cloudflare gates on EUR-Lex) or portal downtime prevent automated bot downloads of direct PDFs, our scrapers generate structured, comprehensive procedure digests. To prevent researchers from mistakenly quoting exact article numbers, deadlines, or contaminant thresholds from a summary without verifying the underlying gazette, these files must be explicitly marked in `master_registry.csv`:
  - `production_context`: Prefixed with `"Derived regulatory orientation summary (per Section 6.1): ..."`
  - `full_text_available`: Logged as `"derived-summary (Section 6.1)"`

---

## 5. Corpus B Discourse & Media Intelligence DQA Protocol (`Section 10` & `Section 11`)

Public discourse, media event streams, and community forums require specialized screening workflows to prevent noisy, syndicated, or non-substantive records from contaminating topic modeling (`BERTopic`) and econometric analysis:

### 1. Section 11 Ethics & PII De-identification (`B-YT-`, `B-RD-`)
All YouTube and Reddit discourse scraping adheres strictly to our **Section 11 Ethics Protocol**:
- Scrapers verify clearance before initiating collection (`ethics_check.py`).
- All personal usernames, handles, and identifying metadata in practitioner comments and forum threads are masked via `deidentify_youtube_sanitization.py`.
- Automated transcripts containing synthetic repetition or boilerplate looped text are purged (`dqa_filter_youtube.py`).

### 2. Section 10 GDELT Content Quality Filter (`B-GD-`)
For global news articles and SPS border alert extraction (`gdelt_pipeline.py`), `dqa_filter_gdelt.py` enforces a rigorous 5-step Content Quality Filter before records are admitted to Corpus B:
1. **Syndicated Wire Deduplication**: Automatically detects and purges duplicate syndicated wire feeds (`PTI`, `ANI`, `Reuters` syndications) based on exact URL and title matching.
2. **Strict English & ASCII Script Gate**: Rejects all non-English, Arabic, or Asian script articles where keyword collisions (e.g., matching the word `"shrimp"` inside a non-English text) create false positives.
3. **Paywall / Adblock / ETPrime Stub Exclusion**: Eliminates login wrappers, subscription walls (`"subscribe to read"`, `"enable cookies"`), ETPrime stubs, and any article with under `65 words`.
4. **Unconditional Pharma / Geopolitical / Macro Rejection**: Applies strict exclusion lists (`pharma_and_macro_noise`) to unconditionally drop Indian pharmaceutical news (`Dabur`, `Lupin`, `Sun Pharma`, `USFDA official action`, `generic Ozempic`), visa/immigration policies (`H-1B`), and political/market movements (`Sensex`, `Nifty`, `ceasefire`, `missile`, `Adani`).
5. **Core Agri-Food Relevance & Trade Friction Gate (Word-Boundary Regex Matching)**: For generic or broad queries (`"rejection"`, `"FDA"`, `"customs"`, `"EUDR"`), requires at least `1 mandatory core food term` (`\b(spice|spices|shrimp|seafood|rice|tea|mango|honey|pesticide|aflatoxin|fssai|apeda|mpeda|mrl|dwpe|salmonella|etylene oxide)\b`) and explicit trade friction terms (`\b(rejection|rejected|delay|consignment|import alert|ban|banned|detained)\b`). Crucially, keyword matching uses **word-boundary regular expressions (`\bkw\b`)** rather than plain Python substring containment (`kw in text`) to prevent off-topic false positives (such as `"tea"` matching inside *steadily* or *team*, `"rice"` matching inside *prices*, or `"port"` matching inside *reports*).

### 3. Tier Separation Protocol (`separate_gdelt_tiers.py`)
To prevent sampling bias where large industrial conglomerates skew MSME trade friction analysis, surviving GDELT records are automatically split into two distinct analytical tiers based on entity recognition (`entity_allowlist.py`):
- **Clean MSME Exporters Extract**: `Corpus_B_Clean_GDELT_MSMEs_Extract.csv` (`relevance_to_study: MSME-instance`)
- **Clean Large Listed Comparators Extract**: `Corpus_B_Clean_GDELT_Large_Listed_Extract.csv` (`enterprise_scale_tier: Tier-1 / Large-Listed`)

### 4. Uniform 7-Column Exceptions Logging Schema
Every single rejected record across Corpus A and Corpus B is logged into `data/exceptions_log.csv` under a strict **7-column schema alignment**:
`[doc_id_attempted, source_name, intended_url_or_query, attempt_date, reason_inaccessible, workaround_tried_resolution, notes]`
This ensures complete auditability, downstream CSV parser stability, and exact 1-to-1 arithmetic reconciliation between raw input pools and final surviving datasets.

---

## 6. Core Data-Processing Pipeline Script Inventory (`src/data-processing/`)

All one-off, file-specific fix scripts and temporary simulation tools have been purged from the repository to maintain clean modular architecture. The production pipeline consists exclusively of the following **10 standardized reusable modules**:

1. **`chunk_documents.py`**: Standardized page-boundary (`--- PAGE N ---`), overlap-aware, and sub-linearly down-weighted chunking engine enforcing precision embedding size thresholds (`~250 words target`, `400 words hard cap`, `90 words floor`, `~30 words overlap`). Preserves single-chunk candidate documents above word thresholds (`>= 600 words` Corpus A, `>= 1,400 words` / `B-GD-071` Corpus B). Applies the **Ceiling Square-Root Rule & Stratified Sampling (`DEC-2026-025`)** (`numpy.linspace` to sample $N_{sampled} = \lceil \sqrt{N} \rceil$ chunks) alongside explicit noise/corruption filtering (`DEC-2026-031`) to prevent long documents from skewing topic modeling, reducing 1,499 raw chunks across candidate documents to exactly **383 verified balanced chunks** (`chunk_manifest.csv`) with exact parent DQA inheritance and distinct parent tracking.
2. **`extract_and_classify_corpus_a.py`**: Core PDF text extraction, sequential registration (`A-PREFIX-NNN`), and 6-dimension empirical DQA scoring pipeline for Corpus A.
3. **`ocr_corpus_a.py`**: Tesseract OCR preprocessing pipeline (v5.4.0, PSM 6, 300 DPI via `PyMuPDF`/`fitz`) that recovers scanned PDFs and standalone image infographics (`RCAC-001..003`, `A-MPEDA-003`, `A-SPICE-003..004`, `RCAC-200..201`) into machine-readable UTF-8 text (`full_text_available: yes (OCR)`). Note: per `DEC-2026-031`, legacy font encoding/gibberish OCR outputs (`A-SPICE-002`, `A-SPICE-004`) remain registered as `full_text_available: yes` in `master_registry.csv` (registry-valid), but are flagged and excluded from downstream embedding generation (`unit_embeddings.npy`) once severe OCR corruption was identified.
4. **`resolve_remaining_queued_a.py`**: Standardized EUR-Lex statutory summary generator resolving queued instruments (`A-EU-013..015`) to `derived-summary (Section 6.1)`, achieving 100% Corpus A machine readability.
5. **`dqa_filter_gdelt.py`**: GDELT news quality, paywall/syndication rejection, and word-boundary regex relevance filtering engine.
6. **`dqa_filter_youtube.py`**: YouTube transcript DQA evaluation, synthetic repetition loop detection, and filtering engine.
7. **`deidentify_youtube_sanitization.py`**: PII de-identification and masking engine for video transcripts and public practitioner comments.
8. **`separate_gdelt_tiers.py`**: Automated stratification script separating verified large listed enterprises from MSME exporter populations.
9. **`run_dqa_audit.py`**: Comprehensive cross-corpus audit script verifying scoring distributions and producing verification reports.
10. **`ethics_check.py`**: Automated privacy boundaries check confirming ethical compliance prior to data release.

---

## 7. Methodological Reconciliation & Downstream Synthesis (`METHODOLOGY_AND_LIMITATIONS.md`)

While this protocol details data extraction, quality screening (`DQA`), ethics de-identification, and scale verification, the complete downstream topic modeling methodology (`BERTopic / e5-base-v2 / UMAP+HDBSCAN`), reconciled limitations across both data extraction and analytical research questions (`RQ1..RQ4`), project acronyms, and reproducibility protocols are consolidated inside **`[METHODOLOGY_AND_LIMITATIONS.md](file:///e:/Summer%20Internship%2726/agri-food-project/docs/METHODOLOGY_AND_LIMITATIONS.md)`**.

### Key Reconciliations with Analytical Chapters:
- **Unified Limitations Synthesis (`Chapter 3`)**: Fully reconciles extraction/verification limits (*public listing bias toward large firms; untested offline municipal trade licenses; `DEC-2026-031` OCR encoding exclusions*) with analytical/modeling delimitations (*`RQ2` bilateral focus restricted to `EU DG SANTE`, `US FDA/NOAA`, and `Japan MHLW`; `Topic 8/9` micro-cluster residuals; Section 10 DQA English/ASCII script filtering*).
- **Topic Modeling Methodology (`Chapter 2`)**: Explains how clean DQA-passed documents (`267 parents`) and down-weighted chunks (`383 chunks`) transition into the 509-unit vector space (`intfloat/e5-base-v2`) and undergo class-based TF-IDF enrichment (`topics_per_class`).
- **Reproducibility Guarantee (`Chapter 4`)**: All candidate thresholds and data extraction rules correspond exactly to release tag **`v1.0.0`**, verified automatically by **`[verify_pipeline_integrity.py](file:///e:/Summer%20Internship%2726/agri-food-project/src/data-processing/verify_pipeline_integrity.py)`**.
