# Round N

Save in output/rounds/NNN/report.md. The agent fills this in before and after the batch.

## Before collection

- Goal progress and coverage gap:
- Selected lead IDs from frontier.csv:
- What earlier result led to this choice (or seed rationale for round 1):
- Tactic, exact targets/query, sort, date window, result limits:
- Why this batch is worth trying; alternative considered:
- Job names, input paths, and maximum charges:
- Available allowance after existing reservations and protected recap money:
- Snapshot: before.csv (all current candidates, taken before these jobs)

## Results

- Metrics: metrics.json from scripts/review_round.py
- Newly discovered confirmed posts; total confirmed now:
- New uncertain/excluded posts; duplicates:
- Older posts newly confirmed or removed from confirmed (separate from discovery):
- Actual charges; unknown charges still reserved; available budget:
- Relevant additions per dollar when charges are known:
- Any incomplete/failed jobs or retrieval limits:

## Learning and next move

- What the new posts teach us about where to look:
- New people, company pages, and query language, with evidence post URLs:
- Leads added/updated in frontier.csv:
- Coverage changes and remaining gaps:
- Tactic decision: continue / change targets / switch route / retire for now
- Next batch and why, or exact stop reason with evidence:

Write a short progress update for the reader, update STATUS.md, then execute the next round within the approved scope.
