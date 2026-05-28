---
title: "Update & Extend"
date: "2026-05-28"
weight: 6
chapter: false
pre: " <b> 5.6. </b> "
---

### Objective

See how fast the agent iterates. Because everything is infrastructure-as-code, changing the agent's behaviour is an edit plus one `cdk deploy`.

#### Example 1 — Widen the query window

Open `infra/agent/instruction.txt` and change the workshop scope from `2022-06-01 → 2022-06-14` to the full 21-day range (`2022-06-01 → 2022-06-23`):

```diff
- Workshop scope: the 14-day window 2022-06-01 through 2022-06-14 (inclusive).
+ Workshop scope: the 21-day window 2022-06-01 through 2022-06-23 (inclusive).
```

Redeploy just the agent stack:

```bash
cdk deploy OttDataAnalystAgentStack --require-approval never
```

> 💡 **Highlight:** Only the `AWS::Bedrock::Agent` resource changes; CloudFormation updates it in place and `auto_prepare` re-prepares the agent. Re-run a question — the agent will now scope to the wider window without any code change.

#### Example 2 — Add a fourth tool: `list_partitions`

Power users sometimes want to know **what data is even available** before they ask aggregations. Add this function to the action group in `infra/stacks/agent_stack.py`:

```python
bedrock.CfnAgent.FunctionProperty(
    name="list_partitions",
    description="List the distinct values for a partition key in a Glue table (e.g. which `dt` days or which `derived_genre` codes exist).",
    parameters={
        "database": bedrock.CfnAgent.ParameterDetailProperty(type="string", required=True, description="Glue DB name"),
        "table":    bedrock.CfnAgent.ParameterDetailProperty(type="string", required=True, description="Glue table name"),
        "partition_key": bedrock.CfnAgent.ParameterDetailProperty(type="string", required=True, description="Partition column"),
    },
)
```

Add a matching branch in `infra/lambda/glue_athena_tools/handler.py`:

```python
def _list_partitions(database, table, partition_key):
    parts = []
    paginator = glue.get_paginator("get_partitions")
    for page in paginator.paginate(DatabaseName=database, TableName=table):
        for p in page["Partitions"]:
            # PartitionKeys are ordered; find the index of partition_key
            ...
    return {"distinct_values": sorted(set(parts)), "count": len(set(parts))}
```

`cdk deploy OttDataAnalystAgentStack` ships the new tool. The model picks it up automatically because the action group function schema changed.

#### Example 3 — Swap the foundation model

The agent model is configurable via CDK context — no code edit needed:

```bash
cdk deploy OttDataAnalystAgentStack \
  -c agentModel=global.anthropic.claude-sonnet-4-5-20250929-v1:0
```

Switch to Sonnet for richer reasoning on complex multi-step questions; stick with Haiku 4.5 (default) for ~3x lower cost per question.

#### Example 4 — Point at a different dataset

The Glue database is also a context parameter:

```bash
cdk deploy OttDataAnalystAgentStack -c glueDatabase=my_other_catalog
```

The agent's instruction.txt still says `fpt_ott_searchevents_analytics`, so you would also update the persona file — but the function schemas accept any database name, so the **tools** work without changes. This is the path to repointing the workshop at another OTT account's data, or at viewership data instead of search-event data.

#### Example 5 — Add a chart-generation tool

The biggest UX win for non-SQL users is **charts**. Add a fifth tool `render_chart(query_result_json, chart_type)` that uses `matplotlib` to render a PNG into the existing S3 bucket and returns a CloudFront URL. The SPA already renders `![](url)` Markdown image links.

This is the same pattern Amazon Bedrock AgentCore's Code Interpreter uses; we're just doing it as a plain Lambda for the workshop.

---

**Previous:** [5.5 Client Application Integration](../5.5-client-integration/) | **Next:** [5.7 Clean Up Resources](../5.7-cleanup/)
