# Collect the Posts
## The post-conference Build Kit

Collect the LinkedIn conversation around an event, build a dataset you can work with, and find an angle for your business.

I built this workflow while studying Dreamforce and UNBOUND. The useful part was learning where to look after the obvious searches stopped finding new posts, then using what each round found to choose the next round.

### The collection loop

**Collect a batch → check what it added → find new leads → choose the next batch → repeat.**

A search finds people posting about the event. Their reactions uncover more posts. Those posts reveal company pages, other active posters, and language worth searching. Your agent follows the useful leads, changes tactics when a route gets thin, and keeps going toward your collection goal within your approved budget.

After each round, it tells you what it found, what it learned, and where it will look next. It saves that progress so you can pick up where you left off.

**Read [How the fan-out loop works](FAN-OUT-LOOP.md)** for a worked example and what to expect from your agent.

**Start here:** [Quick guide](QUICK-START.md) · [A small Dreamforce example](examples/dreamforce-posts.csv) · [Campaign worksheet](templates/campaign-worksheet.md)

### What you need

- **Codex or Claude Code**, with **Work Locally** selected and permission to read files and run scripts. Use the **Code** tab in Claude's desktop app. Standard chat and Cowork are outside this kit's setup path.
- **Apify** to collect new posts. Signup with [my partner link](https://apify.com/?fpr=adamgtm) and use **15GTM** for **15% off all plans**.
- **An empty folder** for this project. Your agent will check Python and help with setup.
- An event, a date range, and a little context about your business.

The example can be explored without an Apify token. Your coding tool's normal usage costs still apply. Apify collection is a separate cost.

### Paste this into your agent

**Use Codex or Claude Code, not standard chat or Cowork, and select “Work Locally.”** In Claude's desktop app, use the **Code** tab.

Create a folder called `post-conference-project`, open it in your local session, and paste:

```text
Get the Build Kit from https://github.com/adamgtm/post-conference-build-kit into this folder. Read its README and skills/collect-event-posts/SKILL.md. Help me set a collection goal and Apify budget, then start with a small pilot. Keep running the fan-out loop: judge each batch, use its discoveries to choose the next tactic, and continue within my approved scope until the goal or a documented stopping condition is reached. Walk me through setup in plain English, show progress after each round, then help me find an angle for my business.
```

Your first useful result is a sample of your event's posts, with the collection cost and a clear next step. With the full collection authorized, the agent continues through further rounds without asking you to direct each one. You can also tell it, “Show me the included Dreamforce example first.”

### What's inside

| File | What it does |
|---|---|
| Quick guide | Setup, collection decisions, analysis, and the next campaign step |
| Fan-out loop guide | Explains how each round determines the next, with a worked example |
| Collection skill | Directs the agent to run, evaluate, adapt, and repeat toward your goal |
| Helper scripts | Bound Apify jobs, save raw results, measure each round's additions, prepare a CSV, check sample recall |
| Collection templates | Save the goal, leads to follow, round decisions, and coverage gaps |
| Business brief | Connects the research to your company and audience |
| Dreamforce example | Shows real input data and how to look for an angle |
| Campaign worksheet | Defines an audience, offer, channels, and measurement |

A conference dataset is a useful sample of the conversation; how much you recover depends on the sources, date range, and collection limits. The collection report makes those limits visible.

The coding agent runs the loop while your session is active. The Python helpers handle collection and accounting; they do not make strategy decisions or keep working after the session closes. To resume, open the same folder and say, “Resume the collection loop from output/STATUS.md.”

This edition focuses on collecting and analyzing posts. Audience activation and paid media are a strategy worksheet, ready to expand as the campaign develops.
