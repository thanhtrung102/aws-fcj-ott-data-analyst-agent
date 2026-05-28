---
title: "AI Data Analyst Agent for OTT Search Events"
description: "FCJ Workshop — Build an AI Data Analyst Agent on Amazon Bedrock that answers natural-language questions about 14 days of 2022 FPT Play OTT search events"
---

# AI Data Analyst Agent for OTT Search Events on Amazon Bedrock

A First Cloud Journey (FCJ) workshop. You will build and deploy a **generative-AI data analyst agent** on **Amazon Bedrock** that lets stakeholders ask plain-language questions ("top search keywords in week 1 by genre", "which hour had the most abandoned searches") about a real 14-day window of FPT Play OTT search events — the agent writes the SQL, runs it on Amazon Athena, and returns a summarised answer with the result table.

{{% notice info %}}
This workshop is fully cloud-deployed (AWS CDK Python) and **Docker-free**. Estimated time: **60–90 minutes**. Estimated cost if cleaned up promptly: **under $1**.
{{% /notice %}}

## What you will build

- A **Bedrock Agent** ("OttDataAnalyst") backed by Anthropic Claude Haiku 4.5 that reasons over the schema and writes Presto/Trino SQL.
- An **action group** with three read-only tools — `get_tables`, `get_table`, `athena_query` — adapted from [aws-samples/sample-Agentic-Ai-Data-Operations](https://github.com/aws-samples/sample-Agentic-Ai-Data-Operations) (`mcp-servers/glue-athena-server/`).
- A serverless **Lambda Function URL + static SPA** (S3 + CloudFront) so non-technical users can chat with the agent.
- All targeted at an existing Glue catalog `fpt_ott_searchevents_analytics.curated` (~1.15 M curated rows, 17 columns + `dt`/`derived_genre` partitions) in `ap-southeast-1`.

Start here → [5. Workshop](5-workshop/)
