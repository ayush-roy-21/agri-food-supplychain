# CODEBOOK: The Barrier Horizon
**Sustainable Supplier Hurdles Facing Indian Agri-Food MSMEs**

## 1. The Four Loci, as Decision Tests
A locus in this study captures the fundamental nature of the hurdle facing the exporter. 

| Locus | One-sentence decision test | Diagnostic phrases you will actually see | NOT this locus if... |
|---|---|---|---|
| **internal-capability** | If the firm had more money, skills, equipment or scale, the hurdle would shrink. The deficit sits inside the firm. | cannot afford testing; no cold chain; certification fee too high for our volume; no trained staff; lab is far away; paperwork we cannot manage; small consignment, full fee | The complaint is about a rule being unclear or shifting (that is institutional-voids) or about a buyer's demand (that is relational-power). |
| **relational-power** | Another chain actor holds the power: a buyer, agent, lead firm or platform sets terms the exporter must accept or exit. | buyer insists on; agent takes the margin; delisted by; take it or leave it; price dictated; middleman; importer demands extra audit; exclusive contract | The demand comes from a regulator or law, not a commercial actor (that is institutional-voids or informational-verifiability). |
| **institutional-voids** | The rules environment itself is the problem: fragmented, overlapping, uncertain, weakly enforced, or the origin carries stigma. | deadline postponed again; two agencies ask different things; scheme changed midway; no single window; enforcement lax at home; India flagged after RASFF; policy flip-flop; which standard applies | The rule is clear and stable and the problem is proving compliance with it (that is informational-verifiability) or affording it (internal-capability). |
| **informational-verifiability** | The firm may even comply, but cannot prove it credibly: evidence is costly, traceability breaks, or the certificate is not believed. | catch certificate; geolocation of plots; batch mixed at aggregator; residue report rejected; document not accepted; audit trail; due-diligence statement; chain of custody; mislabelled origin | The proof exists and is accepted but costs too much for the firm's size (internal-capability) or is demanded by one buyer only (relational-power). |

Multi-locus hurdles are normal. Pick the primary by asking which mechanism, if removed, would dissolve the hurdle; the other goes in `locus_secondary`. A buyer demanding geolocation proof is `informational-verifiability` primary (the proof is the problem) with `relational-power` secondary (the buyer transmits it).

## 2. The Noise Gate, before any coding
| If the topic's top words look like this... | ...then do this, and do NOT code it |
|---|---|
| `comments, download, pdf, format, subscribe, author, user, sir, print, related articles, english, news` | It is scraper noise or website furniture. Log the units to `exceptions_log.csv` with reason `preprocessing-noise`, flag for refit, move on. Noise is never `inductive-other`. |
| `company results, fy26, growth, profit, quarterly, shares` | It is an earnings or press-release cluster, not a hurdle. Same treatment: log, flag, move on. |

## 3. Worked Walkthrough: Topic 3, from documents to signed row

**Step 1. Open the evidence, not the keywords**
The default label is `3_export_agricultural_mangoes_district`. Ignore it. Open the ten most representative documents for Topic 3 from `bertopic_topic_info.csv`. In this example they include two GDELT news items on mango exporters in a named district (`B-GD-047`, `B-GD-089`), an APEDA circular listing approved pack-houses (`A-APEDA-006`), and a practitioner video on getting produce to an approved facility (`B-YT-012`).

**Step 2. Write down what the documents actually say**
`B-GD-047`: growers in the district cannot export because the nearest APEDA-approved pack-house is 300 km away. `B-GD-089`: exporters in two clusters handle most mango volume; others sell to them at a discount. `A-APEDA-006`: the approved pack-house list, showing concentration in a handful of districts. `B-YT-012`: a practitioner explains that without an approved facility nearby, produce loses eligibility and margin. Four sources, two source types, one shared complaint.

**Step 3. Ask the locus decision test**
Would more firm-side resources dissolve this? Largely yes: the binding constraint is access to compliant post-harvest infrastructure, a capability and resources deficit, so `internal-capability` is primary. Is there a second mechanism? Yes: the public approval and infrastructure map is itself uneven, which is an institutional provision gap, so `institutional-voids` is secondary. It is not `relational-power`: the pack-house owners buying at a discount is a consequence of the gap, not its cause.

**Step 4. Draft the name, reject the bad draft, write the good one**
Bad draft: mango export infrastructure problems. Rejected: no mechanism, no actor, could describe anything. Good name states who lacks what and with what consequence, in one sentence of roughly 20 to 30 words, in the words the data uses: *Pack-house and cold-chain infrastructure is concentrated in a few districts, leaving exporters outside those clusters without EU-compliant post-harvest facilities.*

**Step 5. Attach the receipts and sign**
List three to five doc_ids from at least two source types. Then, and only then, the supervisor signs with initials and date. The finished row:

| Topic | 3 |
|---|---|
| locus_primary | internal-capability |
| locus_secondary | institutional-voids |
| hurdle_name | Pack-house and cold-chain infrastructure is concentrated in a few districts, leaving exporters outside those clusters without EU-compliant post-harvest facilities. |
| evidence_doc_ids | B-GD-047; B-GD-089; A-APEDA-006; B-YT-012 |
| supervisor_signoff | AR / 2026-07-24 |

**Step 6. Self-check before you move to the next topic**
Four questions. 
1. Could a stranger recognise this hurdle in a new document from the name alone? 
2. Does every doc_id in the row actually evidence it? 
3. Did you deliberately consider `institutional-voids` before assigning something else, since that locus has been systematically under-coded? 
4. Does the name avoid the forbidden patterns? Any name starting with "Hurdle for Topic" or with a number and underscores fails the integrity check and will be rejected automatically. 

If all four pass, sign and proceed. Budget roughly 25 to 30 minutes per topic; if a topic takes five, you are transcribing keywords, not reading documents.
