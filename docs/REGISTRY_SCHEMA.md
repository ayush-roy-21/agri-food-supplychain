# The Barrier Horizon: Sustainable Supplier Hurdles Facing Indian Agri-Food MSMEs
## Registry Schema & Audit Log Data Dictionary

To ensure inter-corpus consistency and computational compatibility across multi-agent research teams investigating **The Barrier Horizon: Sustainable Supplier Hurdles Facing Indian Agri-Food MSMEs**, all data collection operations in **CorpusA** log into a single source of truth: `data/master_registry.csv`.

---

## 1. Master Registry Schema (`data/master_registry.csv`)

The master registry strictly follows a **13-column relational schema**. Scraper scripts and analytical tools must never alter column ordering or drop required fields.

| Col # | Column Name | Data Type | Description & Allowed Values | Example |
| :---: | :--- | :--- | :--- | :--- |
| **1** | `doc_id` | String | Unique alphanumeric document identifier prefixed by institutional pillar. | `A-APEDA-001`, `A-SPICE-006`, `A-EUDR-001` |
| **2** | `corpus_id` | String | Single-letter corpus designator. For this project, always `A`. | `A` |
| **3** | `source_institution` | String | Official institutional name and parent ministry/organization. | `Spices Board Ministry of Commerce & Industry` |
| **4** | `url` | String | Direct source web link or API endpoint from which document was fetched. | `https://indianspices.com/...` |
| **5** | `retrieval_date_and_format`| String | Composite string combining ISO date (`YYYY-MM-DD`), file format (`pdf`/`html`/`csv`/`txt`), and language. | `2026-07-03 / html / English` |
| **6** | `title_or_description` | String | Formal document title prefixed by its production context or Section 6.1 disclosure. | `Statutory spices export circular: Mandatory Testing for Salmonella...` |
| **7** | `dqa_score` | String | Comma-separated 6-dimension DQA score (Auth, Rel, Gran, Curr, Comp, Mach). | `A,A,A,A,A,A` |
| **8** | `dqa_justification` | String | Brief rationale or duplicate score representation verifying adequacy. | `A,A,A,A,A,A` |
| **9** | `full_text_available` | String | Verifies whether primary full text is stored locally (`yes`/`no`/`derived-summary (Section 6.1)`). | `yes` or `derived-summary (Section 6.1)` |
| **10** | `commodity_scope` | String | Standardized domain tag indicating covered product category. | `spices`, `marine`, `processed-foods`, `sustainability-eudr` |
| **11** | `target_market` | String | Destination export market or international jurisdiction. | `all`, `USA`, `EU`, `UK`, `Japan` |
| **12** | `translation_needed` | String | Indicates whether English translation was required (`required`/`not-required`). | `not-required` |
| **13** | `processing_status` | String | Status of document ingestion and HTTP verification. | `retrieved (HTTP 200)` |

---

## 2. Auxiliary Audit Logs

### A. Exceptions Log (`data/exceptions_log.csv`)
Tracks all encountered web documents, navigation pages, search forms, or dynamic dashboard shells that failed DQA admission thresholds.
- **Fields**: `exception_id`, `doc_id`, `url`, `rejection_date`, `reason_code`, `remediation_action`
- **Allowed Reason Codes**:
  - `failed-data-quality`: Document length below 300 words, empty interface dropdowns, or dynamic JavaScript shell (`Loading...`).
  - `corrupted-pdf-shell`: Server returned HTML redirect page instead of binary PDF payload.
  - `out-of-scope`: Circular unrelated to agricultural exports or trade compliance.

### B. Decision Log (`data/decision_log.csv`)
Records major architectural, methodological, and scoping decisions made during corpus construction.
- **Fields**: `decision_id`, `decision_date`, `decision_type`, `subject_doc_id_or_source`, `rationale_and_context`, `impacted_locus_or_logic`, `logged_by`
