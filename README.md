# Collect the Posts
## The post-conference Build Kit

Collect the LinkedIn conversation around an event, build a dataset you can work with, and find an angle for your business.

I built this workflow while studying Dreamforce and UNBOUND. The useful part was learning where to look after the obvious searches stopped finding new posts.

**Start here:** [Quick guide](QUICK-START.md) · [A small Dreamforce example](examples/dreamforce-posts.csv) · [Campaign worksheet](templates/campaign-worksheet.md)

### What you need

- **Codex or Claude Code**, running in a local folder with permission to read files and run scripts.
- **Apify** to collect new posts. Signup with [my partner link](https://apify.com/?fpr=adamgtm) and use **15GTM** for **15% off all plans**.
- **An empty folder** for this project. Your agent will check Python and help with setup.
- An event, a date range, and a little context about your business.

The example can be explored without an Apify token. Your coding tool's normal usage costs still apply. Apify collection is a separate cost.

### Paste this into your agent

Create a folder called `post-conference-project`, open it in Codex or Claude Code, and paste:

```text
Get the Build Kit from https://github.com/adamgtm/post-conference-build-kit into this folder. Read its README and skills/collect-event-posts/SKILL.md. Help me collect LinkedIn posts around my event and find an angle for my business. Walk me through setup in plain English, ask for the context you need, and start with a small pilot. Get my Apify budget before spending.
```

Your first useful result is a sample of your event's posts, with the collection cost and a clear next step. You can also tell the agent, “Show me the included Dreamforce example first.”

### What's inside

| File | What it does |
|---|---|
| Quick guide | Setup, collection decisions, analysis, and the next campaign step |
| Collection skill | Gives your agent the workflow and lessons from the build |
| Helper scripts | Bound Apify jobs, save raw results, prepare a CSV, check sample recall |
| Business brief | Connects the research to your company and audience |
| Dreamforce example | Shows real input data and how to look for an angle |
| Campaign worksheet | Defines an audience, offer, channels, and measurement |

A conference dataset is a useful sample of the conversation; how much you recover depends on the sources, date range, and collection limits. The collection report makes those limits visible.

This edition focuses on collecting and analyzing posts. Audience activation and paid media are a strategy worksheet, ready to expand as the campaign develops.
