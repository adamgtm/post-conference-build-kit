import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import apify_collect as collector
import prepare_posts as prepare
import sample_recall as recall

with (ROOT / "examples/dreamforce-posts.csv").open(encoding="utf-8-sig", newline="") as f:
    EXAMPLES = list(csv.DictReader(f))
URL = EXAMPLES[0]["post_url"]
INPUT = {"searchQueries": ["Dreamforce 2026"], "maxPosts": 10, "sortBy": "date"}
META = {"id": "actor123", "pricingInfos": [{"pricingModel": "PAY_PER_EVENT", "startedAt": "2026-01-01T00:00:00Z"}]}


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name)
        collector.initialize(self.project, "1")

    def tearDown(self):
        self.temp.cleanup()

    def test_reservation_precedes_post_and_repeat_does_not_charge(self):
        def fake(path, body=None):
            if body is None:
                return {"data": META}
            self.assertEqual(collector.exposure(collector.load(self.project)), collector.money("0.7"))
            self.assertIn("maxTotalChargeUsd=0.7", path)
            return {"data": {"id": "run1", "status": "RUNNING", "defaultDatasetId": "dataset1"}}
        with patch.object(collector, "api", side_effect=fake) as api:
            first = collector.start(self.project, "pilot", "search", INPUT, "0.7")
            second = collector.start(self.project, "pilot", "search", INPUT, "0.7")
            self.assertEqual(first, second)
            self.assertEqual(api.call_count, 2)
            with self.assertRaisesRegex(ValueError, "exceed"):
                collector.start(self.project, "extra", "search", INPUT, "0.4")
            self.assertEqual(api.call_count, 2)

    def test_uncertain_post_blocks_new_spend(self):
        with patch.object(collector, "api", side_effect=[{"data": META}, ValueError("connection lost")]):
            with self.assertRaises(ValueError):
                collector.start(self.project, "pilot", "search", INPUT, "0.7")
        with patch.object(collector, "api") as api:
            with self.assertRaisesRegex(ValueError, "uncertain"):
                collector.start(self.project, "next", "search", INPUT, "0.1")
            api.assert_not_called()
        self.assertEqual(collector.exposure(collector.load(self.project)), collector.money("0.7"))

    def test_fetch_failed_run_paginates_partial_results_and_records_cost(self):
        ledger = collector.load(self.project)
        ledger["jobs"]["pilot"] = {"run_id": "run1", "status": "RUNNING", "cap_usd": "0.7", "cost_usd": None}
        collector.save(self.project / "collection-ledger.json", ledger)
        with patch.object(collector, "api", side_effect=[{"data": {"status": "FAILED", "usageTotalUsd": 0.12, "defaultDatasetId": "data1"}}, [{}] * 1000, [{"last": True}]]) as api:
            result = collector.fetch(self.project, "pilot")
            self.assertEqual(result["items"], 1001)
            self.assertIn("offset=1000", api.call_args_list[-1].args[0])
        self.assertEqual(collector.exposure(collector.load(self.project)), collector.money("0.12"))
        self.assertEqual(len(json.loads((self.project / "raw/pilot.json").read_text())["items"]), 1001)

    def test_missing_cost_keeps_reservation_and_nonfinite_values_fail(self):
        self.assertEqual(collector.exposure({"jobs": {"j": {"status": "SUCCEEDED", "cost_usd": None, "cap_usd": "0.7"}}}), collector.money("0.7"))
        for bad in ("NaN", "Infinity", "-1"):
            with self.assertRaises(ValueError):
                collector.money(bad)
        with self.assertRaises(ValueError):
            collector.validate_input("search", {**INPUT, "maxPosts": 0})
        with self.assertRaises(ValueError):
            collector.current_pricing({"pricingInfos": [{"startedAt": "2020-01-01", "pricingModel": "FLAT_PRICE_PER_MONTH"}]})


class DatasetTests(unittest.TestCase):
    def test_reaction_author_dedup_window_and_judgment(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            raw = {"type": "post", "linkedinUrl": URL, "author": {"name": "Actual author"},
                   "postedAt": {"date": "2026-09-15T12:00:00Z"}, "content": "Event text\u2028with a line separator",
                   "engagement": {"likes": 3, "comments": 2, "shares": 1}}
            collector.save(root / "raw/search.json", {"items": [raw], "run_id": "one"})
            collector.save(root / "raw/reactions.json", {"items": [{"actor": {"name": "Someone else"}, "post": raw}], "run_id": "two"})
            self.assertEqual(prepare.prepare(root, "2026-09-08", "2026-09-25")["confirmed"], 0)
            decisions = root / "decisions.csv"
            prepare.write_csv(decisions, [{"post_url": URL, "about_event": "yes", "reason": "Describes the event"}], ["post_url", "about_event", "reason"])
            result = prepare.prepare(root, "2026-09-08", "2026-09-25", decisions)
            self.assertEqual((result["confirmed"], result["duplicate_observations"]), (1, 1))
            record = recall.rows(root / "posts.csv")[0]
            self.assertEqual(record["author_name"], "Actual author")
            self.assertEqual(record["total_engagement"], "6")
            self.assertEqual(record["source_jobs"], "reactions;search")
            self.assertIn("\u2028", record["post_text"])
            self.assertEqual(prepare.prepare(root, "2026-09-16", "2026-09-25", decisions)["excluded"], 1)

    def test_recall_uses_reference_weights_not_collected_weights(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            fields = ["post_url", "total_engagement"]
            prepare.write_csv(root / "found.csv", [{"post_url": URL, "total_engagement": 999}], fields)
            prepare.write_csv(root / "refs.csv", [{"post_url": URL, "total_engagement": 3}, {"post_url": EXAMPLES[1]["post_url"], "total_engagement": 1}], fields)
            result = recall.recall(root / "found.csv", root / "refs.csv")
            self.assertEqual(result["count_recall"], 0.5)
            self.assertEqual(result["engagement_weighted_recall"], 0.75)
            prepare.write_csv(root / "refs.csv", [], fields)
            self.assertIsNone(recall.recall(root / "found.csv", root / "refs.csv")["count_recall"])


if __name__ == "__main__":
    unittest.main()
