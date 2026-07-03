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
