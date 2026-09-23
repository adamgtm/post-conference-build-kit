# The included example

dreamforce-posts.csv contains 24 real posts from the earlier public Dreamforce export: eight highly engaged posts and sixteen selected with a fixed random seed. It is an excerpt for learning the workflow. Do not calculate whole-event shares from it or equate its row count with the current dashboard.

Ask the agent: “Read these posts alongside my business brief. Show me two possible angles, the source posts behind each, and what more you would need to know.”

The [public Dreamforce dataset](https://github.com/adamgtm/dreamforce-2026-linkedin) is a separate, larger snapshot. Snapshot size and dates should come from that repo's current README.

## Optional recall exercise

dreamforce-reference-holdout.csv is a frozen set of 40 confirmed event posts from Adam's separately tracked panel. It covers the September 8–25, 2026 window as observed by September 23. The panel is selective, and the collection predates the end of that window. This is a check against known posts, not a representative sample of all LinkedIn.

If collecting Dreamforce independently, ask the agent to leave this file unread until it has frozen its discovered posts. Then run:

```sh
python3 scripts/sample_recall.py --collected output/posts.csv --references examples/dreamforce-reference-holdout.csv --out output/recall.json
```

If these URLs were used as seeds, the result is known-post recovery rather than independent recall. The 24-post example and this reference file were drawn from Adam's existing work; testing one against the other is a mechanics exercise only.

For another event, supply your own independently collected references. The helper expects post_url and total_engagement columns. Use engagement measured at the same reference snapshot for both numerator and denominator. Missing or all-zero weights make weighted recall unmeasured.

manifest.json records selection methods and source hashes. Public files omit author profile URLs and inferred affiliation labels.
