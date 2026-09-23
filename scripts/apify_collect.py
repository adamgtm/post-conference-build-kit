#!/usr/bin/env python3
"""Small, resumable Apify collector. Python standard library only."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.apify.com/v2"
ROOT = Path(__file__).resolve().parents[1]
ACTORS = {
    "search": "harvestapi~linkedin-post-search",
    "profile-posts": "harvestapi~linkedin-profile-posts",
    "profile-reactions": "harvestapi~linkedin-profile-reactions",
    "company-posts": "harvestapi~linkedin-company-posts",
}
TERMINAL = {"SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"}


def now():
    return datetime.now(timezone.utc).isoformat()


def money(value):
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise ValueError("Invalid dollar amount") from None
    if not result.is_finite() or result < 0:
        raise ValueError("Dollar amounts must be finite and nonnegative")
    return result


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


@contextmanager
def lock(project):
    project.mkdir(parents=True, exist_ok=True)
    guard = project / ".collect-lock"
    try:
        guard.mkdir()
    except FileExistsError:
        raise ValueError("Collector lock exists. Check for a running collector before removing a stale lock.") from None
    try:
        yield
    finally:
        guard.rmdir()


def token():
    value = os.environ.get("APIFY_TOKEN", "").strip()
    if not value and (ROOT / ".env").exists():
        for line in (ROOT / ".env").read_text(encoding="utf-8").split("\n"):
            key, sep, val = line.strip().partition("=")
            if sep and key == "APIFY_TOKEN":
                value = val.strip().strip("\"'")
    if not value:
        raise ValueError("Set APIFY_TOKEN in the environment or the kit's local .env file. Do not paste it into chat.")
    return value


def api(path, body=None):
    headers = {"Authorization": "Bearer " + token(), "User-Agent": "AdamGTM-Build-Kit/0.1"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    request = urllib.request.Request(API + path, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        # Never dump a request, token, or a provider response that could echo credentials.
        raise ValueError(f"Apify returned HTTP {exc.code}; inspect the run in Apify. No automatic paid retry.") from None
    except (urllib.error.URLError, TimeoutError):
        raise ValueError("Apify request interrupted. Reconcile the saved job before starting again.") from None


def load(project):
    path = project / "collection-ledger.json"
    if not path.exists():
        raise ValueError("Initialize this project once with the reader's approved budget first.")
    return json.loads(path.read_text(encoding="utf-8"))


def exposure(ledger):
    return sum((money(job["cost_usd"]) if job.get("status") in TERMINAL and job.get("cost_usd") is not None
                else money(job["cap_usd"]) for job in ledger["jobs"].values()), Decimal("0"))


def validate_input(actor, value):
    if not isinstance(value, dict):
        raise ValueError("Actor input must be a JSON object")
    target, bound = {
        "search": ("searchQueries", "maxPosts"),
        "profile-posts": ("profileUrls", "maxPosts"),
        "profile-reactions": ("profileUrls", "maxItems"),
        "company-posts": ("targetUrls", "maxPosts"),
    }[actor]
    if not isinstance(value.get(target), list) or not value[target] or not all(isinstance(x, str) and x.strip() for x in value[target]):
        raise ValueError(f"Supply a nonempty {target} list")
    if type(value.get(bound)) is not int or value[bound] <= 0:
        raise ValueError(f"{bound} must be a positive integer; zero may mean unlimited")
    if actor == "search" and value.get("sortBy") not in {"date", "relevance"}:
        raise ValueError("Set sortBy to date or relevance")
    if value.get("scrapeComments") or value.get("scrapeReactions"):
        raise ValueError("Core collection keeps nested comments/reactions off; budget audience work separately")


def current_pricing(meta):
    eligible = [p for p in meta.get("pricingInfos", []) if p.get("startedAt") and p["startedAt"] <= now()]
    if not eligible:
        raise ValueError("Cannot verify current Actor pricing; inspect the Actor before collection")
    pricing = max(eligible, key=lambda p: p["startedAt"])
    if pricing.get("pricingModel") != "PAY_PER_EVENT":
        raise ValueError("Actor is not pay-per-event; the configured dollar cap cannot be relied on")
    return pricing


def initialize(project, budget):
    amount = money(budget)
    if amount <= 0:
        raise ValueError("Budget must be positive")
    with lock(project):
        if (project / "collection-ledger.json").exists():
            raise ValueError("Project already has a budget ledger; do not reset it to bypass earlier spend")
        save(project / "collection-ledger.json", {"version": 1, "created_at": now(), "budget_usd": str(amount), "jobs": {}})
    return {"budget_usd": str(amount)}


def start(project, name, actor, inp, cap):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", name):
        raise ValueError("Job names use lowercase letters, digits, underscores and hyphens")
    validate_input(actor, inp)
    charge = money(cap)
    if charge <= 0:
        raise ValueError("Run cap must be positive")
    with lock(project):
        ledger = load(project)
        existing = ledger["jobs"].get(name)
        if existing:
            if (existing["actor"], existing["input"], money(existing["cap_usd"])) != (ACTORS[actor], inp, charge):
                raise ValueError("Name already used with a different job. Preserve it and choose another name.")
            return existing
        if any(not j.get("run_id") for j in ledger["jobs"].values()):
            raise ValueError("A prior start is uncertain. Adopt its real run before starting anything else.")
        if exposure(ledger) + charge > money(ledger["budget_usd"]):
            raise ValueError("This run's reservation would exceed the approved project budget")
        meta = api("/acts/" + ACTORS[actor])["data"]
        pricing = current_pricing(meta)
        if charge < money(pricing.get("minimalMaxTotalChargeUsd", 0)):
            raise ValueError("Run cap is below the Actor's current minimum")
        job = {"actor": ACTORS[actor], "actor_id": meta["id"], "input": inp, "cap_usd": str(charge),
               "created_at": now(), "status": "START_UNCERTAIN", "run_id": None, "cost_usd": None}
        ledger["jobs"][name] = job
        save(project / "collection-ledger.json", ledger)  # Reservation BEFORE the paid request.
        run = api("/acts/" + ACTORS[actor] + "/runs?" + urllib.parse.urlencode({"maxTotalChargeUsd": str(charge), "timeout": 600}), inp)["data"]
        job.update(run_id=run["id"], status=run["status"], dataset_id=run.get("defaultDatasetId"))
        save(project / "collection-ledger.json", ledger)
        return job


def adopt(project, name, run_id):
    if not re.fullmatch(r"[A-Za-z0-9]+", run_id):
        raise ValueError("Invalid run ID")
    with lock(project):
        ledger = load(project)
        job = ledger["jobs"][name]
        if job.get("run_id"):
            raise ValueError("Job already has a run ID; fetch it")
        if any(j.get("run_id") == run_id for j in ledger["jobs"].values()):
            raise ValueError("That run is already attached to another job")
        run = api("/actor-runs/" + run_id)["data"]
        actual = api("/key-value-stores/" + run["defaultKeyValueStoreId"] + "/records/INPUT")
        started = datetime.fromisoformat(run["startedAt"].replace("Z", "+00:00"))
        reserved = datetime.fromisoformat(job["created_at"])
        if started < reserved or run.get("actId") != job["actor_id"] or actual != job["input"] or money(run.get("options", {}).get("maxTotalChargeUsd", -1)) != money(job["cap_usd"]):
            raise ValueError("Run Actor/input/cap does not match the saved job")
        job.update(run_id=run_id, status=run["status"], dataset_id=run.get("defaultDatasetId"))
        save(project / "collection-ledger.json", ledger)
        return job


def fetch(project, name):
    with lock(project):
        ledger = load(project)
        job = ledger["jobs"][name]
        if not job.get("run_id"):
            raise ValueError("Start was uncertain. Locate and adopt the actual run; do not submit it again.")
        run = api("/actor-runs/" + job["run_id"])["data"]
        job["status"] = run["status"]
        job["cost_usd"] = str(money(run["usageTotalUsd"])) if run.get("usageTotalUsd") is not None else None
        job["dataset_id"] = run.get("defaultDatasetId")
        job["checked_at"] = now()
        save(project / "collection-ledger.json", ledger)
        if job["status"] not in TERMINAL:
            return {"status": job["status"], "run_id": job["run_id"], "next": "fetch this saved job later"}
        items = []
        if job["dataset_id"]:
            offset = 0
            while True:
                page = api("/datasets/" + job["dataset_id"] + "/items?" + urllib.parse.urlencode({"format": "json", "offset": offset, "limit": 1000}))
                if not isinstance(page, list):
                    raise ValueError("Unexpected dataset response")
                items.extend(page)
                if len(page) < 1000:
                    break
                offset += len(page)
        raw = project / "raw" / (name + ".json")
        save(raw, {**job, "items": items})
        job["raw"] = str(raw.relative_to(project))
        job["items"] = len(items)
        save(project / "collection-ledger.json", ledger)
        return {k: job.get(k) for k in ("status", "run_id", "items", "cost_usd", "cap_usd", "raw")}


def status(project):
    ledger = load(project)
    held = exposure(ledger)
    return {"budget_usd": ledger["budget_usd"], "spent_or_reserved_usd": str(held),
            "unallocated_usd": str(money(ledger["budget_usd"]) - held),
            "jobs": {name: {k: j.get(k) for k in ("status", "run_id", "items", "cost_usd", "cap_usd", "raw")} for name, j in ledger["jobs"].items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "start", "fetch", "status", "adopt"):
        p = sub.add_parser(name)
        p.add_argument("--project", type=Path, required=True)
        if name == "init":
            p.add_argument("--budget", required=True)
        if name in {"start", "fetch", "adopt"}:
            p.add_argument("--name", required=True)
        if name == "start":
            p.add_argument("--actor", choices=ACTORS, required=True)
            p.add_argument("--input", type=Path, required=True)
            p.add_argument("--cap", required=True)
        if name == "adopt":
            p.add_argument("--run-id", required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            result = initialize(args.project, args.budget)
        elif args.command == "start":
            result = start(args.project, args.name, args.actor, json.loads(args.input.read_text(encoding="utf-8")), args.cap)
        elif args.command == "fetch":
            result = fetch(args.project, args.name)
        elif args.command == "adopt":
            result = adopt(args.project, args.name, args.run_id)
        else:
            result = status(args.project)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
