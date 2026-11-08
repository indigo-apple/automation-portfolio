# Upwork 投标模板（英文）

规则：**前两句必须命中客户的具体需求**，不要自我介绍开头。结尾用一个具体问题收口（提高回复率）。

---

## 模板 A — 数据采集 / 爬虫类

**Job post**: "Need someone to scrape [site] for [data]"

```
You need [specific data] from [site], refreshed [daily/weekly], delivered as a spreadsheet
your team can actually use — not a one-off CSV that breaks next week.

I've built exactly this kind of pipeline. Recent example: a scanner that pulls funding
rates from 6 exchanges (1,528 symbols), normalizes their inconsistent symbol formats,
and ranks opportunities — runs in ~20 seconds, no third-party dependencies, deployable
as a scheduled job. Repo + live demo available on request.

For your project I'd do:
1. Check whether [site] exposes a public API first — an API is 10x more stable than HTML.
2. Build the fetch layer with retries and rate limiting.
3. Normalize into your required columns, dedupe, and write CSV/Excel or straight to your DB.
4. Hand over a README with a single command to run it, plus an optional cron/systemd timer.

Two questions before I quote precisely:
1. Roughly how many records per run, and how often?
2. Does the data need to land in a database, or is a file enough?

If it's behind a login, tell me whose account it is — I only scrape data the client owns.
```
**报价锚点**：写 $120–350，工时 1–2 天。

---

## 模板 B — 自动化/脚本类（Excel、报表、重复劳动）

**Job post**: "Automate our weekly reporting" / "Need a script to do X every day"

```
The 30 minutes your team spends rebuilding that report every morning is ~130 hours a year.
That's the actual cost, not the script.

Here's what I'd replace it with: one command (or one scheduled job) that pulls the source
data, applies your current formatting rules, and drops a dated .xlsx in a folder — with
conditional highlighting for anything out of range, so exceptions jump out instead of
hiding in row 400.

I've built this pattern before: read → clean → format → archive, with the output
matching the client's existing template exactly. I can send a sample file so you can
see the formatting before committing.

To scope it I need:
1. One example of your current report (format matters more than the data).
2. Where the raw data comes from — export file, database, or an API?

If your source is a manual export today, I can also automate that step, which is usually
where the real time savings are.
```
**报价锚点**：$110–350。

---

## 模板 C — 机器人 / 监控告警类

**Job post**: "Need a Telegram bot" / "Alert me when X changes"

```
You want to stop checking [thing] manually and get a message only when something
actually changed. The hard part isn't sending a Telegram message — it's not spamming
you with duplicates and not silently dying when the network blips.

My implementation handles both: the watcher persists state so the same event never
alerts twice, and it only commits state after a successful send, so a failed push
retries on the next cycle instead of disappearing. I run a production monitoring bot
on exactly this pattern (daily digest, dedupe by content hash, silent when there's
nothing new).

For your bot:
1. Define what counts as "changed" precisely (a new row? a price move > X%? a keyword?).
2. Build the watcher + rule engine.
3. Render a compact message with a link back to the source.
4. Deploy with systemd/cron and give you a restart + log guide.

Quick questions:
1. Which chat platform — Telegram, Discord, Slack, or WhatsApp?
2. How often should it check, and how fast does an alert need to arrive?

I can share a working demo of the alert format before you commit.
```
**报价锚点**：$200–500。

---

## 通用收尾（放在最后）

```
Happy to start with a small paid test (e.g. one data source / one report) so you can
verify quality before committing to the full scope.
```

## 避坑

- 不要群发同一个模板：Upwork 会降权，客户也能看出来
- 不要先报价后提问：先问 2 个问题显得专业，也让客户投入
- 不接"unpaid test task"，只给 demo 截图/录屏
- 首单可以把价格压到 70%，但**评价必须拿到 5 星**
