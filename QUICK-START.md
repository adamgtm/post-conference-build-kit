# Quick guide

## 1. Set up your workspace

**Use Codex or Claude Code, not standard chat or Cowork, and select “Work Locally.”** In Claude's desktop app, use the **Code** tab; the environment may be labeled **Local**.

Open an empty folder in that local session and paste the prompt in the [README](README.md). The agent gets the files and walks you through the rest. Selecting a folder alone does not change a cloud session into a local one.

If you are new to these tools, use the official [Codex quickstart](https://developers.openai.com/codex/quickstart) or [Claude Code Desktop guide](https://code.claude.com/docs/en/desktop).

Create an [Apify account using my partner link](https://apify.com/?fpr=adamgtm). Use **15GTM for 15% off all plans**. An Apify “Actor” is a small program that collects a particular kind of data. Your agent picks the right ones from the kit.

The agent needs an Apify API token to run those programs. Get it from your Apify account's API settings. Save it locally where the agent directs you; do not put it in a shared document or public repo. The included script reads APIFY_TOKEN from the environment or a local .env file. The agent checks for the token without displaying it.

Your agent will also check for Python 3.10 or later. The helpers use Python's standard library, so there is no package list to install.

Tell the agent the event, dates, company, target customer, and what you want to learn. The [business brief](templates/business-brief.md) gives you prompts. You can answer in conversation.

## 2. Collect the Posts

**Run the loop.** Your agent collects a batch, checks what it added, extracts new leads, and chooses the next batch. It repeats toward your goal within the approved budget. Read [How the fan-out loop works](FAN-OUT-LOOP.md) for a worked example.

**Define enough.** Tell the agent what you need to learn and whose voices matter. You can set a post target, or ask it to build a broad sample until distinct routes show diminishing returns. It records the goal, coverage priorities, budget, and stopping conditions before collecting.

**Start with good seeds.** Bring a few actual posts from the host, speakers, customers, partners, and people discussing the event. Include different points of view. Your agent can help find these. An event name, host, dates, and a few product or session names also give it useful search terms.

**Set a limit.** A small pilot helps you learn whether the queries and sources are useful. For example, you could authorize a $2 pilot within a $10 total Actor-charge allowance. These are spending choices, not promises about dataset size. Your Apify plan, other platform charges, and coding-tool usage are separate. The agent shows actual charges and remaining reservations as it works.

**Use every round to plan the next.** Search results reveal company pages and active posters. Their posts and reactions reveal more authors and useful search terms. The agent keeps a queue of these leads, follows productive branches, and tests ways to fill gaps. Newly discovered people and pages can start another round of fan-out. This last route found material our searches missed.

**Check what each pass adds.** The agent reports new relevant posts, duplicates, cost, and its next move after every round. Two weak searches are a reason to try a different route; they do not establish that collection is finished. If you want a later recap pass, reserve part of the budget and return after the event. This kit runs during your active agent session.

**Keep your progress.** The folder holds the plan, the queue of leads, and a report for every round. To continue in a new session, say: “Resume the collection loop from output/STATUS.md. Keep the same goal and spending limit.”

**Optional: measure sample recall.** Keep an independently collected set of known event posts aside until discovery finishes. The agent checks how many it recovered. Finding 32 of 40 is 80% recall against those 40, not 80% of LinkedIn. A Dreamforce reference set and the calculation helper are included. Seed posts cannot double as an independent coverage test.

The result is a readable CSV, the original data, and a collection report. Your agent removes duplicates and separates confirmed event posts from unrelated and uncertain ones.

## 3. Find your angle

Give the agent your company context before asking what to write. Have it read both popular posts and a random selection of quieter ones. Look for a repeated question, a disagreement, an unmet need, or a gap between what people say and what they demonstrate.

Ask for three candidate angles. Each should name the reader, their problem, your point of view, the evidence, what your company can contribute, and a useful offer. Read the source posts behind the strongest candidate.

A busy topic is not automatically a good angle. Choose something that matters to your customer and that you can support with experience, data, or a useful asset. The agent should show evidence that challenges its recommendation too.

## 4. Build the audience and campaign strategy

Use the [campaign worksheet](templates/campaign-worksheet.md) to connect the chosen angle to a segment and offer.

Begin with relevant authors. If the audience needs expanding, collecting commenters and reactors is a separate step with a separate budget. Define job function, company fit, geography, and exclusions before enrichment.

For paid distribution, establish a usable matched audience, a destination, a budget, and a success metric before launch. Track the path from people collected to people qualified, matched, reached, and converted. Count existing subscribers separately from new ones.

This kit gets you to the strategy. Enrichment, audience uploads, and ad launch come later.
