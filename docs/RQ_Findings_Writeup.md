# Research Findings: Sustainable Supplier Hurdles for Indian Agri-Food MSMEs

*This write-up corresponds to the v1.1.0 pipeline output: 15 BERTopic topics (4 noise-gated, 11 substantive) fitted on 432 modeling units, reduced to 345 units after noise gating, drawn from 259 registry records (112 Corpus A, 147 Corpus B). All locus assignments follow the evidence-based 6-step qualitative walkthrough protocol defined in `CODEBOOK.md`, with 2:1 primary/secondary weighting.*

## RQ1: The Barrier Horizon (Locus Distribution)
Following the 6-step qualitative walkthrough of 15 BERTopic clusters, **4 topics** were identified as scraper/earnings noise (Topics 1, 5, 9, 13) and gated out to `exceptions_log.csv` with reason `preprocessing-noise`. Of the remaining **11 substantive topics**, 3 were classified as `inductive-other` (outlier bucket, aggregate press-release discourse, and macro trade commentary) and **8 map to the four core decision loci**:

### Structural Hurdles (cross-cutting, systemic barriers)
1. **Mandatory Consignment-Wise Inspection (Topic 0)**: Heightened EU border controls and EIC schemes impose strict health certification requirements on spice and marine exports. (`institutional-voids` primary; 85 units)
2. **Cross-Border Testing Disruptions (Topic 2)**: Indian authorities mandated laboratory testing on imported Nepali tea, leading buyers to suspend purchases and disrupting cross-border trade. (`institutional-voids` primary, `relational-power` secondary; 34 units)
3. **Statutory Hygiene and Sanitary Regulations (Topic 12)**: Mandatory facility standards and waste disposal practices challenge the infrastructure capabilities of petty food business operators. (`internal-capability` primary, `institutional-voids` secondary; 12 units)

### Sector-Specific Hurdles
4. **Pack-House and Cold-Chain Infrastructure Concentration (Topic 3)**: Post-harvest facilities are clustered in a few districts, leaving exporters outside those corridors without EU-compliant infrastructure. (`internal-capability` primary, `institutional-voids` secondary; 28 units)
5. **EUDR Compliance Data Burden (Topic 4)**: EUDR mandates extensive geolocation and traceability data collection, imposing heavy processing burdens on exporters. (`informational-verifiability` primary, `internal-capability` secondary; 22 units)
6. **Fisheries Value-Addition Deficit (Topic 6)**: Ministerial discourse highlights the need for production quality and value-added export capabilities rather than raw commodity exports. (`internal-capability` primary; 18 units)
7. **Rice Post-Harvest Infrastructure (Topic 7)**: Inadequate scientific storage and transport logistics degrade grain quality and disrupt exports. (`internal-capability` primary; 18 units)
8. **EU Corporate Sustainability Directives (Topic 10)**: European sustainability reporting directives mandate complex assurance procedures across supply chains. (`informational-verifiability` primary; 16 units)
9. **Modern Slavery Monitoring Technologies (Topic 14)**: Academic frameworks for multi-actor collaboration to identify modern slavery through monitoring technologies. (`informational-verifiability` primary, `relational-power` secondary; 9 units)

### Locus Distribution Summary
| Locus | Registry Count | Share |
|:---|:---:|:---:|
| institutional-voids | 87 | 33.6% |
| inductive-other | 77 | 29.7% |
| informational-verifiability | 43 | 16.6% |
| internal-capability | 41 | 15.8% |
| relational-power | 11 | 4.2% |

The data points to **Institutional Voids** as the single largest structural locus (33.6%), followed by **Informational Verifiability** (16.6%) and **Internal Capability** (15.8%). **Relational Power** is present but at the lowest frequency (4.2%), consistent with the study's focus on regulatory rather than buyer-driven trade barriers.

## RQ2: Hurdle Interlock & Co-occurrence
Structural hurdles rarely operate in isolation. The interlock analysis highlights three key dynamics:
- **Internal Capability × Institutional Voids (Topics 3, 12)**: Institutional requirements (FSSAI hygiene mandates, APEDA pack-house approvals) directly trigger internal capability deficits. The rule is clear, but the capital required to build compliant facilities forms a hard barrier for MSMEs.
- **Institutional Voids × Relational Power (Topic 2)**: A sudden institutional mandate (mandatory sampling for Nepal tea) immediately triggers a relational power shift, where buyers respond by suspending purchases. The state imposes the rule, but the buyer executes the punishment.
- **Informational Verifiability × Internal Capability (Topic 4)**: EUDR due diligence data requirements are formally about proving compliance (verifiability), but the operational cost of collecting and processing geolocation data binds back to firm-level resource constraints (capability).

## RQ3: Actor Framing Divergence
When analyzing the textual discourse around these hurdles:
- **Regulators** frame these mechanisms as necessary food safety and public health mandates (e.g., EIC and FSSAI notifications focus on procedural compliance and hazard exclusion) or as demanding costly supply chain traceability data and assurance.
- **Practitioners and Media** focus on the economic disruption and structural asymmetry (e.g., highlighting that buyers suspend purchases, or that petty operators lack the infrastructure to comply). Media discourse particularly highlights capacity deficits and infrastructure shortfalls at the sector level.
- **Firms** express resource deficits and lack of testing capability when hurdles sit in the `internal-capability` locus, while navigating uncertain rules and overlapping administrative mandates when hurdles are `institutional-voids`.

## RQ4: Temporal Readiness (Formally Descoped)
As logged in `DEC-2026-036`, RQ4 (movement over time) was formally descoped due to the sparse historical multi-year coverage of the specific regulatory mechanisms in the GDELT data.
