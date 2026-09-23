#!/usr/bin/env python3
"""Normalize saved HarvestAPI posts and reactions; export judged event posts."""
import argparse
from collections import Counter
import csv
from datetime import date
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

FIELDS = ["post_url", "posted_date", "author_name", "author_headline", "author_type", "author_url",
          "is_repost", "likes", "comments", "reposts", "total_engagement", "post_text", "in_window",
          "about_event", "reason", "source_jobs", "source_run_ids"]


def post_key(url):
    parsed = urlsplit(url or "")
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {"linkedin.com", "www.linkedin.com"}:
        raise ValueError("Expected a captured LinkedIn post URL")
    if not (parsed.path.startswith("/posts/") or parsed.path.startswith("/feed/update/")):
        raise ValueError("A profile URL is not a post URL")
    match = re.search(r"(?:activity[-:]|ugcPost:|share:)(\d{10,})", parsed.path)
    return match.group(1) if match else parsed.path.rstrip("/")


def write_csv(path, rows, fields=FIELDS):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def number(value):
    if value is None or value == "":
        return None
    result = int(value)
    if result < 0:
        raise ValueError("Negative engagement")
    return result


def normalize(item):
    # Reaction actor rows wrap the actual post. Never use the reactor as its author.
    raw = item["post"] if isinstance(item.get("post"), dict) else item
    if raw.get("type") not in {None, "post"}:
        return None
    url = raw.get("linkedinUrl") or (raw.get("socialContent") or {}).get("shareUrl") or ""
    key = post_key(url)
    author = raw.get("author") or {}
    engagement = raw.get("engagement") or {}
    posted = raw.get("postedAt") or {}
    posted = posted.get("date", "") if isinstance(posted, dict) else str(posted)
    try:
        day = date.fromisoformat(posted[:10]).isoformat()
    except ValueError:
        day = ""
    counts = [number(engagement.get(k)) for k in ("likes", "comments", "shares")]
    if counts[2] is None:
        counts[2] = number(engagement.get("reposts"))
    return key, {"post_url": url, "posted_date": day,
                 "author_name": author.get("name") or " ".join(filter(None, [author.get("firstName"), author.get("lastName")])),
                 "author_headline": author.get("info") or author.get("headline") or "",
                 "author_type": author.get("type", "unknown"), "author_url": author.get("linkedinUrl", ""),
                 "is_repost": bool(raw.get("repost") or raw.get("repostId")),
                 "likes": counts[0], "comments": counts[1], "reposts": counts[2],
                 "total_engagement": sum(counts) if all(c is not None for c in counts) else None,
                 "post_text": raw.get("content") or ""}


def prepare(project, start, end, decisions=None):
    if date.fromisoformat(start) > date.fromisoformat(end):
        raise ValueError("Collection start is after end")
    records, routes, runs = {}, {}, {}
    counts = Counter()
    blobs = [(p, json.loads(p.read_text(encoding="utf-8"))) for p in sorted((project / "raw").glob("*.json"))]
    # Use one coherent, most recently fetched observation for engagement counters.
    blobs.sort(key=lambda pair: (pair[1].get("checked_at", ""), pair[0].name))
    for path, blob in blobs:
        for item in blob.get("items", []):
            counts["raw_items"] += 1
            try:
                result = normalize(item)
            except (ValueError, TypeError, AttributeError):
                counts["unusable_rows"] += 1
                continue
            if not result:
                counts["non_post_rows"] += 1
                continue
            key, record = result
            counts["duplicate_observations"] += key in records
            records[key] = record
            routes.setdefault(key, set()).add(path.stem)
            runs.setdefault(key, set()).add(blob.get("run_id") or "imported")
    labels = {}
    if decisions:
        with decisions.open(newline="", encoding="utf-8-sig") as handle:
            for decision in csv.DictReader(handle):
                key = post_key(decision["post_url"])
                if key in labels:
                    raise ValueError("Duplicate decision for a post; resolve it before export")
                if key not in records:
                    raise ValueError("Decision refers to a post absent from the raw collection")
                value = decision["about_event"].strip().lower()
                if value not in {"yes", "no", "uncertain"}:
                    raise ValueError("Use yes, no, or uncertain in about_event")
                labels[key] = (value, decision.get("reason", ""))
    rows = []
    for key, record in sorted(records.items()):
        day = record["posted_date"]
        in_window = "unknown" if not day else ("yes" if start <= day <= end else "no")
        value, reason = labels.get(key, ("uncertain", "Not yet judged"))
        record.update(in_window=in_window, about_event=value, reason=reason,
                      source_jobs=";".join(sorted(routes[key])), source_run_ids=";".join(sorted(runs[key])))
        rows.append(record)
    confirmed = [r for r in rows if r["in_window"] == "yes" and r["about_event"] == "yes"]
    uncertain = [r for r in rows if r["in_window"] != "no" and r["about_event"] != "no" and (r["in_window"] == "unknown" or r["about_event"] == "uncertain")]
    excluded = [r for r in rows if r["in_window"] == "no" or r["about_event"] == "no"]
    project.mkdir(parents=True, exist_ok=True)
    for name, records_out in [("candidates", rows), ("posts", confirmed), ("uncertain", uncertain), ("excluded", excluded)]:
        write_csv(project / (name + ".csv"), records_out)
    counts.update(unique_candidates=len(rows), confirmed=len(confirmed), uncertain=len(uncertain), excluded=len(excluded))
    (project / "counts.json").write_text(json.dumps(dict(counts), indent=2) + "\n", encoding="utf-8")
    return dict(counts)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project", type=Path, required=True)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--decisions", type=Path)
    a = p.parse_args()
    try:
        print(json.dumps(prepare(a.project, a.start, a.end, a.decisions), indent=2))
    except (ValueError, KeyError, OSError) as exc:
        p.exit(1, str(exc) + "\n")
