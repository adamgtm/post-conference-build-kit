#!/usr/bin/env python3
"""Snapshot and measure one collection round. No network calls or strategy decisions."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re

from apify_collect import TERMINAL, lock, money, now, save
from prepare_posts import FIELDS, normalize, post_key, write_csv


def read_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not {"post_url", "in_window", "about_event"}.issubset(reader.fieldnames or []):
            raise ValueError("Expected the candidates.csv produced by prepare_posts.py")
        result = {}
        for row in reader:
            key = post_key(row["post_url"])
            if key in result:
                raise ValueError("Duplicate post key in candidate snapshot")
            result[key] = row
        return result


def disposition(row):
    if row["in_window"] == "yes" and row["about_event"] == "yes":
        return "confirmed"
    if row["in_window"] == "no" or row["about_event"] == "no":
        return "excluded"
    return "uncertain"


def round_folder(project, number):
    if not re.fullmatch(r"[0-9]{3,}", number):
        raise ValueError("Use a round number such as 001")
    return project / "rounds" / number


def snapshot(project, number):
    with lock(project):
        folder = round_folder(project, number)
        if (folder / "before.csv").exists() or (folder / "baseline.json").exists():
            raise ValueError("Round baseline already exists; resume it without overwriting")
        for baseline in (project / "rounds").glob("*/baseline.json"):
            if not (baseline.parent / "metrics.json").exists():
                raise ValueError("Finish the previous round before snapshotting another")
        source = project / "candidates.csv"
        if not source.exists() and any((project / "raw").glob("*.json")):
            raise ValueError("Prepare existing raw data before taking a baseline")
        rows = read_rows(source) if source.exists() else {}
        ledger_path = project / "collection-ledger.json"
        ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {"jobs": {}}
        if any(j.get("status") not in TERMINAL or not j.get("raw") for j in ledger["jobs"].values()):
            raise ValueError("Reconcile and download existing jobs before starting a round")
        folder.mkdir(parents=True, exist_ok=True)
        write_csv(folder / "before.csv", rows.values(), FIELDS)
        baseline = {"round": number, "created_at": now(), "jobs_before": sorted(ledger["jobs"]),
                    "raw_before": sorted(p.stem for p in (project / "raw").glob("*.json")),
                    "candidates_before": len(rows)}
        save(folder / "baseline.json", baseline)
        return baseline


def review(project, number, jobs):
    if not jobs or len(set(jobs)) != len(jobs):
        raise ValueError("Supply each job in this round exactly once")
    if any(not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", name) for name in jobs):
        raise ValueError("Invalid job name")
    with lock(project):
        folder = round_folder(project, number)
        baseline = json.loads((folder / "baseline.json").read_text())
        if set(jobs) & set(baseline["jobs_before"]):
            raise ValueError("A round cannot claim jobs that preceded its baseline")
        new_raw = {p.stem for p in (project / "raw").glob("*.json")} - set(baseline["raw_before"])
        if new_raw != set(jobs):
            raise ValueError("Include every new raw job in this round, even duplicate-only jobs")
        ledger_path = project / "collection-ledger.json"
        if ledger_path.exists():
            ledger = json.loads(ledger_path.read_text())
            if set(ledger["jobs"]) - set(baseline["jobs_before"]) != set(jobs):
                raise ValueError("Reconcile and include every new ledger job before review")
        if (folder / "metrics.json").exists():
            previous = json.loads((folder / "metrics.json").read_text())
            if set(previous["jobs"]) != set(jobs):
                raise ValueError("Preserve the job set of a reviewed round")
        before = read_rows(folder / "before.csv")
        after = read_rows(project / "candidates.csv")
        if set(before) - set(after):
            raise ValueError("Earlier candidates disappeared; restore cumulative preparation")
        blobs = [(name, json.loads((project / "raw" / (name + ".json")).read_text())) for name in jobs]
        blobs.sort(key=lambda pair: (pair[1].get("checked_at", ""), pair[0]))
        returned, first_job = set(), {}
        counts = Counter(raw_items=0, unusable_rows=0, non_post_rows=0, valid_observations=0)
        costs, unknown, incomplete = money(0), money(0), []
        by_job = {}
        for name, blob in blobs:
            if blob.get("status") not in TERMINAL:
                raise ValueError("Fetch a terminal result for every job before reviewing")
            if blob["status"] != "SUCCEEDED":
                incomplete.append(name)
            if blob.get("cost_usd") is None:
                unknown += money(blob["cap_usd"])
            else:
                costs += money(blob["cost_usd"])
            unique = set()
            for item in blob.get("items", []):
                counts["raw_items"] += 1
                try:
                    normalized = normalize(item)
                except (ValueError, TypeError, AttributeError):
                    counts["unusable_rows"] += 1
                    continue
                if normalized is None:
                    counts["non_post_rows"] += 1
                    continue
                key, _ = normalized
                if key not in after or name not in after[key].get("source_jobs", "").split(";"):
                    raise ValueError("Prepare all round results before reviewing")
                counts["valid_observations"] += 1
                unique.add(key)
                returned.add(key)
                first_job.setdefault(key, name)
            by_job[name] = {"unique_returned": len(unique), "new_candidates": 0, "new_confirmed": 0,
                            "cost_usd": blob.get("cost_usd"), "cap_usd": blob.get("cap_usd"),
                            "status": blob["status"]}
        new = returned - set(before)
        if set(after) - set(before) != new:
            raise ValueError("Unlisted jobs added candidates; include the whole round")
        for key in new:
            row = by_job[first_job[key]]
            row["new_candidates"] += 1
            row["new_confirmed"] += disposition(after[key]) == "confirmed"
        new_counts = Counter(disposition(after[key]) for key in new)
        before_confirmed = {k for k, row in before.items() if disposition(row) == "confirmed"}
        after_confirmed = {k for k, row in after.items() if disposition(row) == "confirmed"}
        result = {
            "round": number, "reviewed_at": now(), "jobs": jobs, **counts,
            "unique_returned": len(returned), "new_candidates": len(new),
            "duplicate_observations": counts["valid_observations"] - len(new),
            "new_confirmed": new_counts["confirmed"], "new_uncertain": new_counts["uncertain"],
            "new_excluded": new_counts["excluded"],
            "older_posts_newly_confirmed": len((after_confirmed - before_confirmed) & set(before)),
            "older_posts_no_longer_confirmed": len(before_confirmed - after_confirmed),
            "total_confirmed_before": len(before_confirmed), "total_confirmed_after": len(after_confirmed),
            "known_charges_usd": str(costs), "unknown_charge_reservations_usd": str(unknown),
            "new_confirmed_per_dollar": (float(money(new_counts["confirmed"]) / costs)
                                         if costs > 0 and unknown == 0 else None),
            "incomplete_jobs": incomplete, "by_job": by_job,
            "attribution": "First observed in this round by fetched timestamp, then job name; marginal, not causal.",
        }
        save(folder / "metrics.json", result)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("snapshot", "review"):
        p = sub.add_parser(command)
        p.add_argument("--project", type=Path, required=True)
        p.add_argument("--round", required=True)
        if command == "review":
            p.add_argument("--jobs", nargs="+", required=True)
    args = parser.parse_args()
    try:
        result = (snapshot(args.project, args.round) if args.command == "snapshot"
                  else review(args.project, args.round, args.jobs))
        print(json.dumps(result, indent=2))
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
