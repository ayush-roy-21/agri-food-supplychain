"""
map_registry_locus.py

Rolls up chunk-level BERTopic topic assignments (modeling_units_with_topics.csv)
into a document-level locus_tag proposal for master_registry.csv, using the
Step 3 topic->locus coding in topic_locus_mapping.csv.

Tiering logic (see accompanying writeup for rationale):
  Tier A - single real (non-outlier, non-noise) topic across all chunks -> auto-inherit
  Tier B - one real topic + Topic -1/8/9 noise chunks -> auto-inherit from the real topic,
           noise chunks discarded from the vote entirely (not just down-weighted)
  Tier C - genuinely mixed real-topic signal, OR 100% Topic -1 -> NOT auto-filled;
           reports word-count-weighted leading topic as a hypothesis only
  Tier D - registry doc has zero modeling units -> NOT auto-filled; no topic signal exists

NOISE_TOPICS = {-1, 8, 9} per the reading packet: -1 is the heterogeneous outlier
bucket with no internal locus consensus; 8 and 9 are the mentor's flagged
non-hurdle / structural-noise clusters. Chunks in these topics are excluded from
the document-level vote rather than averaged in, since including them would dilute
a real signal with noise rather than genuinely reflecting mixed content.

Usage:
    python3 map_registry_locus.py \
        --registry data/master_registry.csv \
        --units data/embeddings/modeling_units_with_topics.csv \
        --topic-mapping topic_locus_mapping.csv \
        --out registry_locus_mapping_draft.csv
"""
import argparse
import pandas as pd

NOISE_TOPICS = {-1, 8, 9}


def build_doc_topic_shares(units: pd.DataFrame) -> pd.DataFrame:
    """Word-count-weighted topic share per parent_doc_id."""
    wc = units.groupby(["parent_doc_id", "assigned_topic"])["word_count"].sum().reset_index()
    totals = wc.groupby("parent_doc_id")["word_count"].transform("sum")
    wc["share"] = wc["word_count"] / totals
    return wc


def classify_doc(topic_shares: pd.DataFrame) -> dict:
    """Given one parent doc's topic/share rows, return tier + supporting fields."""
    topics = set(topic_shares["assigned_topic"])
    real_topics = topics - NOISE_TOPICS

    if len(real_topics) == 0:
        # 100% noise/outlier chunks -> Tier C, no real signal, report nothing as hypothesis
        return {
            "tier": "C",
            "auto_fill": False,
            "reason": "100% Topic -1 (outlier) - topic model has no locus opinion for this document",
            "dominant_real_topic": None,
            "dominant_real_topic_share": None,
            "all_topic_shares": _fmt_shares(topic_shares),
        }

    if len(real_topics) == 1:
        real_topic = next(iter(real_topics))
        noise_present = len(topics - real_topics) > 0
        real_share = topic_shares.loc[topic_shares["assigned_topic"] == real_topic, "share"].iloc[0]
        return {
            "tier": "B" if noise_present else "A",
            "auto_fill": True,
            "reason": (
                f"single real topic ({real_topic}); noise chunks discarded from vote"
                if noise_present else f"single real topic ({real_topic}), no noise chunks"
            ),
            "dominant_real_topic": int(real_topic),
            "dominant_real_topic_share": round(float(real_share), 3),
            "all_topic_shares": _fmt_shares(topic_shares),
        }

    # 2+ real topics -> genuinely mixed, Tier C, report leading real topic as hypothesis only
    real_rows = topic_shares[topic_shares["assigned_topic"].isin(real_topics)]
    leading = real_rows.sort_values("share", ascending=False).iloc[0]
    return {
        "tier": "C",
        "auto_fill": False,
        "reason": f"{len(real_topics)} real topics present ({sorted(real_topics)}) - no clean single winner",
        "dominant_real_topic": int(leading["assigned_topic"]),
        "dominant_real_topic_share": round(float(leading["share"]), 3),
        "all_topic_shares": _fmt_shares(topic_shares),
    }


def _fmt_shares(topic_shares: pd.DataFrame) -> str:
    return ";".join(
        f"{int(r.assigned_topic)}:{r.share:.2f}"
        for r in topic_shares.sort_values("share", ascending=False).itertuples()
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True)
    ap.add_argument("--units", required=True)
    ap.add_argument("--topic-mapping", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    registry = pd.read_csv(args.registry, low_memory=False)
    units = pd.read_csv(args.units, low_memory=False)
    topic_map = pd.read_csv(args.topic_mapping, low_memory=False)
    topic_map["Topic"] = topic_map["Topic"].astype(int)
    topic_lookup = topic_map.set_index("Topic")[["locus_primary", "locus_secondary"]].to_dict("index")

    shares = build_doc_topic_shares(units)
    modeled_doc_ids = set(shares["parent_doc_id"])

    rows = []
    for doc_id in registry["doc_id"]:
        if doc_id not in modeled_doc_ids:
            rows.append({
                "doc_id": doc_id,
                "tier": "D",
                "auto_fill": False,
                "reason": "no modeling units exist for this document (never chunked/embedded)",
                "dominant_real_topic": None,
                "dominant_real_topic_share": None,
                "all_topic_shares": None,
                "locus_primary": None,
                "locus_secondary": None,
            })
            continue

        doc_shares = shares[shares["parent_doc_id"] == doc_id]
        result = classify_doc(doc_shares)
        result["doc_id"] = doc_id

        if result["auto_fill"] and result["dominant_real_topic"] in topic_lookup:
            locus = topic_lookup[result["dominant_real_topic"]]
            result["locus_primary"] = locus.get("locus_primary")
            result["locus_secondary"] = locus.get("locus_secondary")
        else:
            # Tier C: still surface the leading real topic's locus as an unconfirmed hypothesis
            if result.get("dominant_real_topic") in topic_lookup:
                locus = topic_lookup[result["dominant_real_topic"]]
                result["locus_primary"] = f"[HYPOTHESIS-REVIEW] {locus.get('locus_primary')}"
                result["locus_secondary"] = locus.get("locus_secondary")
            else:
                result["locus_primary"] = None
                result["locus_secondary"] = None

        rows.append(result)

    out = pd.DataFrame(rows)
    col_order = ["doc_id", "tier", "auto_fill", "locus_primary", "locus_secondary",
                 "dominant_real_topic", "dominant_real_topic_share", "reason", "all_topic_shares"]
    out = out[col_order]
    out.to_csv(args.out, index=False)

    print("Tier counts:")
    print(out["tier"].value_counts().sort_index())
    print(f"\nAuto-fillable (Tier A+B): {out['auto_fill'].sum()} / {len(out)}")
    print(f"Needs manual read (Tier C+D): {(~out['auto_fill']).sum()} / {len(out)}")
    print(f"\nWritten to {args.out}")


if __name__ == "__main__":
    main()