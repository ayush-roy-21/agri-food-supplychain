import pandas as pd
import csv

record = {
    'decision_id': 'DEC-2026-040', 
    'decision_date': '2026-07-23', 
    'decision_type': 'corpus-finding', 
    'subject_doc_id_or_source': 'Institutional-Voids Locus Absorption', 
    'rationale_and_context': 'In the refitted 4-topic model on verified MSME pass-units, the institutional-voids locus does not appear as a standalone primary topic. Instead, regulatory overlaps and bureaucratic complexities have been absorbed as secondary dimensions into all three other loci (e.g., MPEDA access costs, APEDA registrations, and CSRD burdens). This documents that institutional-voids acts as a cross-cutting systemic friction rather than an isolated hurdle.', 
    'impacted_locus_or_logic': 'institutional-voids', 
    'logged_by': 'AR / Automated Pipeline'
}

df = pd.DataFrame([record])
df.to_csv('data/decision_log.csv', mode='a', header=False, index=False, quoting=csv.QUOTE_MINIMAL)
print("Logged DEC-2026-040")
