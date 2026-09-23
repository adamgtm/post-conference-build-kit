#!/usr/bin/env python3
"""Compute overlap with a frozen reference set, never estimated LinkedIn coverage."""
import argparse
import csv
import json
import math
from pathlib import Path
from prepare_posts import post_key


def rows(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def recall(collected, references):
    discovered = {post_key(r["post_url"]) for r in rows(collected)}
    ref = {}
    for row in rows(references):
        key = post_key(row["post_url"])
        raw = row.get("total_engagement", "")
        weight = float(raw) if raw != "" else None
        if weight is not None and (not math.isfinite(weight) or weight < 0):
            raise ValueError("Reference weights must be finite and nonnegative")
        if key in ref and ref[key]["weight"] != weight:
            raise ValueError("Duplicate reference has conflicting weights")
        ref[key] = {"post_url": row["post_url"], "weight": weight}
    found = discovered.intersection(ref)
    known_weights = bool(ref) and all(r["weight"] is not None for r in ref.values())
    total_weight = sum(r["weight"] for r in ref.values()) if known_weights else None
    return {"reference_posts": len(ref), "found": len(found),
            "count_recall": len(found) / len(ref) if ref else None,
            "engagement_weighted_recall": sum(ref[k]["weight"] for k in found) / total_weight if total_weight else None,
            "missing_post_urls": [r["post_url"] for k, r in ref.items() if k not in found],
            "meaning": "Recall against this reference set only; independence must be established from its provenance."}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--collected", type=Path, required=True)
    p.add_argument("--references", type=Path, required=True)
    p.add_argument("--out", type=Path)
    a = p.parse_args()
    try:
        result = json.dumps(recall(a.collected, a.references), indent=2) + "\n"
        if a.out:
            a.out.parent.mkdir(parents=True, exist_ok=True)
            a.out.write_text(result, encoding="utf-8")
        print(result)
    except (ValueError, KeyError, OSError) as exc:
        p.exit(1, str(exc) + "\n")
