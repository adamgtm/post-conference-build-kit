# Collection methods and helper commands

## Routes and what we learned

These are observations from Adam's September 2026 runs, not guarantees for every event.

Use these as tactics inside the skill's adaptive loop. Their order below is not a fixed execution plan. Revisit a route with newly discovered targets when the previous results justify it; log what changed before spending again.

1. **Seeds and targeted search.** Start with captured post URLs from a mix of host, speakers, partners, customers and independent voices. Build queries from event names, hashtags, product names and session language. Use newest and relevance order.
2. **Host and company pages.** Pull relevant company pages directly. The conference pilots found posts search had missed. Include company pages that emerge as authors, not just the host.
3. **Active non-host posters.** Identify people with repeated relevant posts. Their own posts and recent reactions are a useful next route. Inspect the nested post returned with each reaction.
4. **Recaps.** A later pass can use “takeaways,” “back from,” and “what I learned,” sorted by newest. Save a snapshot before adding this pass.

Queries that tag host executives or filter to current employees helped in the conference work. Executive reactions were stronger for funding announcements than conferences. Pulling every seed-post liker's own posts had low yield in these pilots; leave that broad expansion off by default.

We often reached a few hundred results per query/sort. The Actor's current documentation says roughly 400–500 per query. Treat both as retrieval limits, not a reason to promise a hard ceiling. New query variants and routes are more useful than repeatedly paying for duplicate pages.

## Actors

The four core Actors below currently expose public post collection without requiring LinkedIn cookies. Apify credentials are still needed to run jobs. Read each live input schema before using a template.

| Job | Actor | Input essentials |
|---|---|---|
| Search | [harvestapi/linkedin-post-search](https://apify.com/harvestapi/linkedin-post-search) | searchQueries, sortBy, maxPosts, postedLimitDate |
| A person's posts | [harvestapi/linkedin-profile-posts](https://apify.com/harvestapi/linkedin-profile-posts) | profileUrls, maxPosts, postedLimitDate |
| A person's reactions to posts | [harvestapi/linkedin-profile-reactions](https://apify.com/harvestapi/linkedin-profile-reactions) | profileUrls, maxItems |
| A company's posts | [harvestapi/linkedin-company-posts](https://apify.com/harvestapi/linkedin-company-posts) | targetUrls, maxPosts, postedLimitDate |

Optional audience work uses [post reactions](https://apify.com/harvestapi/linkedin-post-reactions) and [post comments](https://apify.com/harvestapi/linkedin-post-comments). These are documented next steps, not enabled in the core collection helper.

Example search input; replace the event/date from the brief:

```json
{"searchQueries":["Dreamforce 2026"],"sortBy":"date","maxPosts":50,"postedLimitDate":"2026-09-08","profileScraperMode":"short","scrapeReactions":false,"scrapeComments":false}
```

Example profile reactions input: profileUrls is a list of observed profile URLs; maxItems can start at 40 per profile. Company input uses targetUrls and maxPosts, for example 50 per company. Limits generally apply per query/profile/company. Multiply by the number of targets when estimating cost. Never use zero as a bound; it can mean all available results.

postedLimitDate is a lower date bound. Filter the upper bound locally as well. Do not discard posts only because the event name is absent if the text, mentions and event context establish relevance.

## Commands the agent runs

From the kit root, after the reader approves the amount:

```sh
python3 scripts/apify_collect.py init --project output --budget 10
python3 scripts/review_round.py snapshot --project output --round 001
python3 scripts/apify_collect.py start --project output --name search-date-01 --actor search --input output/jobs/search-date-01.json --cap 0.25
python3 scripts/apify_collect.py fetch --project output --name search-date-01
python3 scripts/apify_collect.py status --project output
python3 scripts/prepare_posts.py --project output --start 2026-09-08 --end 2026-09-25
```

The start command returns quickly. Fetch checks once; if still running, continue another task and fetch later. It paginates and saves partial datasets for failed/timed-out runs too. Paid POSTs are never retried automatically.

After reading the full new post texts and recording relevance in output/decisions.csv:

```sh
python3 scripts/prepare_posts.py --project output --start 2026-09-08 --end 2026-09-25 --decisions output/decisions.csv
python3 scripts/review_round.py review --project output --round 001 --jobs search-date-01
```

The round helper makes no network calls. `snapshot` saves all current candidates as output/rounds/001/before.csv; for the first empty collection it writes a header-only baseline. It refuses to overwrite a baseline or start another round before the previous one has metrics. Run it before starting that round's jobs. `review` writes metrics.json; supply every job in that round. It checks that earlier candidates remain and that the listed results have been prepared. Failed terminal runs retain useful partial additions but are marked incomplete, so their low yield cannot support saturation.

Metrics distinguish newly discovered confirmed posts from older candidates newly labeled relevant. Duplicates include repeats from earlier rounds and within this batch. For overlapping jobs, a post's new-discovery credit goes to the first fetched observation, breaking ties by job name. These are marginal additions, not a causal comparison of Actors. Unknown charges keep their full cap reserved; cost efficiency stays unmeasured until all round charges are known.

After review, update the round report, frontier.csv, coverage check, and STATUS.md. Pick the next batch from the discoveries and remaining gaps. Take round 002's baseline only after completing that review. The helper measures progress; the coding agent chooses and executes the next move.

A same-name, same-input start returns the saved receipt. A changed input requires a new name and a new reservation. An uncertain start blocks further starts. Use the Apify console to find its actual run, then `adopt --project output --name NAME --run-id ID`; adoption verifies Actor, input and cap before attaching the ID.

All jobs in the project share one ledger. Terminal jobs with known charges use those charges; unfinished/unknown-charge jobs reserve their full cap. The budget covers Actor charges from these jobs, not subscription fees or work outside this ledger. The helper checks current pay-per-event pricing before starting, because maxTotalChargeUsd applies to that model. [Apify run API](https://docs.apify.com/api/v2/actors-runs-post).

Use a .env file beside the kit's README or APIFY_TOKEN in the environment. Never echo the value. A stale .collect-lock after a killed process may be removed only after checking that no collector process is still using the project; keep the ledger and reconcile pending runs.

## Labels and exports

Save decisions.csv in output with these columns:

```csv
post_url,about_event,reason
```

Use yes, no, or uncertain. URLs must come from candidates.csv. Then rerun prepare_posts.py with --decisions output/decisions.csv. It writes confirmed posts.csv, uncertain.csv, excluded.csv, and counts.json. It preserves source routes, captured URLs and complete text. Missing dates are uncertain for the window and excluded from confirmed exports.

For a public share, exclude author profile URLs and unverified affiliation fields. Internal candidates retain captured profile URLs because fan-out needs them.
