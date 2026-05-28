---
title: "Test the Agent"
date: "2026-05-28"
weight: 4
chapter: false
pre: " <b> 5.4. </b> "
---

### Objective

Confirm the agent both **reasons** (writes valid Athena SQL against the schema in its instruction) and **acts** (calls `athena_query`, gets real rows, and presents them).

#### Option A — Bedrock console test window

1. Open **Amazon Bedrock → Agents → OttDataAnalyst** in `ap-southeast-1`.
2. In the right-hand **Test** panel, make sure the alias is **live**, then enter:
   > *Top 10 search keywords overall in the 14-day window, including any genre. Show counts.*
3. Click **Show trace**. You will see the orchestration steps: the model produces a rationale, then an **Action group invocation** of `athena_query` (with the SQL it generated), then the tool's observation (the rows returned), then the final answer.

> 💡 **Highlight:** The trace is the proof that this is an *agent*: notice the explicit `athena_query` action between the model's thinking and its final answer. The SQL was **written by the model**, not hard-coded by us.

#### Option B — Headless invoke (CLI)

From `infra/`, with the virtual environment active:

```bash
python scripts/invoke_agent.py "Top 10 search keywords overall in the 14-day window, including any genre. Show counts."
```

The script reads the `AgentId`/`AgentAliasId` from the stack outputs and calls `bedrock-agent-runtime:InvokeAgent`. Real (abridged) output:

```
Here are the **top 10 search keywords** across all genres for June 1–14, 2022:

| Rank | Keyword | Search Count |
|------|---------|--------------|
| 1 | liên minh công lý: phiên bản của zack snyder (Zack Snyder's Justice League) | 10,253 |
| 2 | fairy tail | 8,579 |
| 3 | thiên nga bóng đêm (Black Swan) | 7,183 |
| 4 | sao bằng (Shooting Star) | 6,339 |
| 5 | nữ thanh tra tài ba (Smart Investigator) | 6,276 |
| 6 | bắt ma phá án (Ghost Hunt) | 6,019 |
| 7 | running man | 5,659 |
| 8 | naruto | 5,465 |
| 9 | siêu nhân (Superhero) | 4,450 |
| 10 | yêu nhầm chị đầu (Falling In Love By Mistake) | 4,422 |

The most-searched keyword is **"Liên minh công lý: Phiên bản của Zack Snyder"** (Zack Snyder's Justice League) with 10,253 searches. The top 10 mix Vietnamese titles, anime (Fairy Tail, Naruto), and Korean/international content.

**Follow-up questions you could explore:**
- Which genres dominate these top keywords?
- How do search patterns differ by platform (mobile vs. web vs. TV)?
```

The agent wrote and executed this SQL behind the scenes:

```sql
SELECT 
  keyword_norm,
  COUNT(*) as search_count
FROM fpt_ott_searchevents_analytics.curated
WHERE dt BETWEEN '2022-06-01' AND '2022-06-14'
  AND keyword_norm IS NOT NULL
GROUP BY keyword_norm
ORDER BY search_count DESC
LIMIT 10
```

#### Verify the result in Athena directly

You can re-run the same SQL via the Athena console or CLI and confirm the rows match:

```bash
aws athena start-query-execution \
  --query-string "$(echo SELECT 
  keyword_norm,
  COUNT(*) as search_count
FROM fpt_ott_searchevents_analytics.curated
WHERE dt BETWEEN '2022-06-01' AND '2022-06-14'
  AND keyword_norm IS NOT NULL
GROUP BY keyword_norm
ORDER BY search_count DESC
LIMIT 10 | sed 's/"/\\"/g')" \
  --query-execution-context Database=fpt_ott_searchevents_analytics \
  --result-configuration OutputLocation=s3://ottdataanalystagentstack-resultsbucket-rcoyosyqkjgw/manual/ \
  --region ap-southeast-1
```

Then poll `get-query-execution` until it succeeds and use `get-query-results` to fetch the rows. The agent does this whole loop for you.

#### Trace deep-dive

Each `invoke_agent` call returns a stream of events. With `enableTrace=True` you also get:

- `orchestrationTrace.rationale.text` — the model's reasoning before acting.
- `orchestrationTrace.invocationInput.actionGroupInvocationInput` — the tool name + parameters (the SQL).
- `orchestrationTrace.observation.actionGroupInvocationOutput.text` — the JSON the tools Lambda returned.

In the 14-day window we observe typical latencies of **8–25 seconds** for an analyst question: ~2s Glue catalog read, ~3-8s Athena scan, ~5-12s Claude reasoning + answer.

---

**Previous:** [5.3 Deploy the Agent](../5.3-deploy-agent/) | **Next:** [5.5 Client Application Integration](../5.5-client-integration/)
