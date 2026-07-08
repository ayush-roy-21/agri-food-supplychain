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

Every document admitted to CorpusA undergoes evaluation across **six quality dimensions**, scored on a standardized scale: **A (Adequate)**, **M (Marginal)**, or **I (Inadequate)**.

### The 6 DQA Dimensions:
1. **Authority (Auth)**: Source legitimacy (Statutory regulatory body vs. third-party news).
2. **Relevance (Rel)**: Direct alignment with export certification, SPS inspection, or traceability.
3. **Granularity (Gran)**: Substantive depth (Detailed technical parameters/SOPs vs. high-level overviews).
4. **Currency (Curr)**: Temporal validity (Active policy frameworks or post-2020 circulars).
5. **Completeness (Comp)**: Document integrity (Full operative text vs. truncated fragments or login forms).
6. **Machine Readability (Mach)**: Computational accessibility (Clean UTF-8 text or OCR-searchable PDF vs. scanned image PDFs).

### Minimum Threshold for Corpus Admittance:
- Documents scoring **`A,A,A,A,A,A`** are admitted as primary analytical records.
- Documents scoring below **300 words** in narrative length or representing empty search forms / dynamic dashboard shells (`Loading...`) are rejected as **Inadequate** and moved to `exceptions_log.csv` with reason codes (`failed-data-quality`).

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
5. **Core Agri-Food Relevance & Trade Friction Gate**: For generic or broad queries (`"rejection"`, `"FDA"`, `"customs"`, `"EUDR"`), requires at least `1 mandatory core food term` (`spice`, `shrimp`, `seafood`, `rice`, `tea`, `mango`, `pesticide`, `aflatoxin`, `fssai`, `apeda`, `mpeda`, `mrl`, `dwpe`, etc.) and explicit trade friction terms (`rejection`, `delay`, `consignment`, `import alert`).

### 3. Tier Separation Protocol (`separate_gdelt_tiers.py`)
To prevent sampling bias where large industrial conglomerates skew MSME trade friction analysis, surviving GDELT records are automatically split into two distinct analytical tiers based on entity recognition (`entity_allowlist.py`):
- **Clean MSME Exporters Extract**: `Corpus_B_Clean_GDELT_MSMEs_Extract.csv` (`relevance_to_study: MSME-instance`)
- **Clean Large Listed Comparators Extract**: `Corpus_B_Clean_GDELT_Large_Listed_Extract.csv` (`enterprise_scale_tier: Tier-1 / Large-Listed`)

### 4. Uniform 7-Column Exceptions Logging Schema
Every single rejected record across Corpus A and Corpus B is logged into `data/exceptions_log.csv` under a strict **7-column schema alignment**:
`[doc_id_attempted, source_name, intended_url_or_query, attempt_date, reason_inaccessible, workaround_tried_resolution, notes]`
This ensures complete auditability, downstream CSV parser stability, and exact 1-to-1 arithmetic reconciliation between raw input pools and final surviving datasets.
