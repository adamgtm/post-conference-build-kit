"""Offline collection replays; texts/results are synthetic, URLs from the included example."""
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import apify_collect as collector
import prepare_posts as prepare
import review_round as rounds

with (ROOT / "examples/dreamforce-posts.csv").open(newline="", encoding="utf-8") as handle:
    URLS = [row["post_url"] for row in csv.DictReader(handle)]


class RoundTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def raw(self, name, indices, cost="0.20", status="SUCCEEDED", nested=False):
        items = [{"type": "post", "linkedinUrl": URLS[i], "author": {"name": "Fixture author"},
                  "postedAt": {"date": "2026-09-15"}, "content": "Synthetic event fixture"} for i in indices]
        if nested:
            items = [{"post": item, "actor": {"name": "Fixture reactor"}} for item in items]
        collector.save(self.project / "raw" / (name + ".json"),
                       {"items": items, "status": status, "run_id": name, "cost_usd": cost,
                        "cap_usd": "0.50", "checked_at": "2026-09-23T12:00:00Z"})

    def prepare(self, labels):
        decisions = self.project / "decisions.csv"
        prepare.write_csv(decisions, [{"post_url": URLS[i], "about_event": label, "reason": "Fixture judgment"}
                                     for i, label in labels.items()], ["post_url", "about_event", "reason"])
        prepare.prepare(self.project, "2026-09-08", "2026-09-25", decisions)

    def test_three_round_replay_separates_discovery_reclassification_and_duplicates(self):
        rounds.snapshot(self.project, "001")
        self.raw("search", [0, 1, 2])
        self.prepare({0: "yes", 1: "uncertain", 2: "no"})
        first = rounds.review(self.project, "001", ["search"])
        self.assertEqual((first["new_confirmed"], first["new_uncertain"], first["new_excluded"]), (1, 1, 1))

        rounds.snapshot(self.project, "002")
        self.raw("reactions", [0, 1, 3, 3], nested=True)
        self.prepare({0: "yes", 1: "yes", 2: "no", 3: "yes"})
        second = rounds.review(self.project, "002", ["reactions"])
        self.assertEqual(second["new_confirmed"], 1)
        self.assertEqual(second["older_posts_newly_confirmed"], 1)
        self.assertEqual(second["duplicate_observations"], 3)
        self.assertEqual(second["total_confirmed_after"], 3)
        self.assertEqual(second["new_confirmed_per_dollar"], 5)

        rounds.snapshot(self.project, "003")
        self.raw("company", [0, 3])
        self.prepare({0: "yes", 1: "yes", 2: "no", 3: "yes"})
        third = rounds.review(self.project, "003", ["company"])
        self.assertEqual((third["new_confirmed"], third["duplicate_observations"]), (0, 2))
        self.assertEqual(third["total_confirmed_after"], 3)

    def test_overlapping_jobs_share_credit_and_unknown_cost_is_not_zero(self):
        rounds.snapshot(self.project, "001")
        self.raw("a", [0, 1])
        self.raw("b", [1, 2], cost=None)
        self.prepare({0: "yes", 1: "yes", 2: "yes"})
        result = rounds.review(self.project, "001", ["b", "a"])
        self.assertEqual(result["new_confirmed"], 3)
        self.assertEqual(sum(j["new_confirmed"] for j in result["by_job"].values()), 3)
        self.assertEqual(result["by_job"]["b"]["new_confirmed"], 1)
        self.assertEqual(result["unknown_charge_reservations_usd"], "0.50")
        self.assertIsNone(result["new_confirmed_per_dollar"])

    def test_failed_partial_result_is_not_a_complete_weak_round(self):
        rounds.snapshot(self.project, "001")
        self.raw("partial", [0], status="TIMED-OUT")
        self.prepare({0: "yes"})
        result = rounds.review(self.project, "001", ["partial"])
        self.assertEqual(result["new_confirmed"], 1)
        self.assertEqual(result["incomplete_jobs"], ["partial"])

    def test_resume_preserves_baseline_and_requires_prepared_complete_job_set(self):
        rounds.snapshot(self.project, "001")
        with self.assertRaisesRegex(ValueError, "already exists"):
            rounds.snapshot(self.project, "001")
        with self.assertRaisesRegex(ValueError, "previous round"):
            rounds.snapshot(self.project, "002")
        self.raw("a", [0])
        self.prepare({0: "yes"})
        self.raw("b", [0])
        with self.assertRaisesRegex(ValueError, "every new raw job"):
            rounds.review(self.project, "001", ["a"])
        with self.assertRaisesRegex(ValueError, "Prepare all"):
            rounds.review(self.project, "001", ["a", "b"])
        self.prepare({0: "yes"})
        result = rounds.review(self.project, "001", ["a", "b"])
        self.assertEqual(result["known_charges_usd"], "0.40")
        self.assertEqual(result["new_confirmed"], 1)

    def test_pending_ledger_job_blocks_review_and_next_snapshot(self):
        collector.initialize(self.project, "1")
        rounds.snapshot(self.project, "001")
        self.raw("a", [0])
        self.prepare({0: "yes"})
        ledger = collector.load(self.project)
        ledger["jobs"] = {"a": {"status": "SUCCEEDED", "raw": "raw/a.json"},
                          "b": {"status": "START_UNCERTAIN"}}
        collector.save(self.project / "collection-ledger.json", ledger)
        with self.assertRaisesRegex(ValueError, "every new ledger job"):
            rounds.review(self.project, "001", ["a"])
        # Even outside an open round, unreconciled spend must be resumed first.
        collector.save(self.project / "rounds/001/metrics.json", {"jobs": ["a"]})
        with self.assertRaisesRegex(ValueError, "Reconcile"):
            rounds.snapshot(self.project, "002")

    def test_lost_candidates_are_not_silent_negative_growth(self):
        rounds.snapshot(self.project, "001")
        self.raw("a", [0])
        self.prepare({0: "yes"})
        rounds.review(self.project, "001", ["a"])
        rounds.snapshot(self.project, "002")
        self.raw("b", [1])
        self.prepare({0: "yes", 1: "yes"})
        rows = rounds.read_rows(self.project / "candidates.csv")
        prepare.write_csv(self.project / "candidates.csv", [rows[prepare.post_key(URLS[1])]])
        with self.assertRaisesRegex(ValueError, "disappeared"):
            rounds.review(self.project, "002", ["b"])


if __name__ == "__main__":
    unittest.main()
