---
title: "Workshop"
date: "2026-05-28"
weight: 5
chapter: false
pre: " <b> 5. </b> "
---

# Building an AI Data Analyst Agent on Amazon Bedrock

#### Overview

**Amazon Bedrock Agents** let you build generative-AI applications that can reason over a task and **take actions** by calling your own APIs (Lambda functions). In this workshop you will build an **OTT Data Analyst agent**: ask a question in plain language about FPT Play search-event data, and the agent writes Presto/Trino SQL, executes it on **Amazon Athena**, then summarises the answer with a result table.

> An *agent* differs from a plain chatbot: it is given an **instruction** (its role), a **foundation model** (its reasoning brain), and one or more **action groups** (tools it can invoke). Bedrock orchestrates the loop "think → call a tool → read the result → answer".

We use four building blocks to assemble a complete, serverless workflow:

- **Foundation Model (Anthropic Claude Haiku 4.5)** — the reasoning brain that interprets the question and writes SQL.
- **Bedrock Agent + Action Group** — wraps the model with an instruction and three tools: `get_tables`, `get_table`, `athena_query`.
- **AWS Glue Data Catalog + Amazon Athena** — the metastore and serverless SQL engine over the existing 14-day OTT search-event dataset in S3.
- **Serverless delivery (Lambda Function URL + S3/CloudFront)** — a Docker-free way to call the agent from a browser.

The action-group code is adapted from [aws-samples/sample-Agentic-Ai-Data-Operations](https://github.com/aws-samples/sample-Agentic-Ai-Data-Operations) (`mcp-servers/glue-athena-server/lambda_handler.py`), trimmed to the three read-only tools needed for analyst Q&A.

#### Dataset

The agent queries an existing Glue catalog already populated by the upstream FPT Play SDLF pipeline:

- **Database**: `fpt_ott_searchevents_analytics`
- **Table**: `curated` — 17 columns + partition keys `dt`, `derived_genre`
- **Scope**: 14-day window **2022-06-01 → 2022-06-14** (real, ~750K events in this slice)
- **Region**: `ap-southeast-1`

#### Outcomes

By the end of the workshop you will have:

- A deployed Bedrock Agent that converts natural-language questions into Athena queries.
- An S3 results bucket with a 14-day expiration lifecycle to keep query results tidy.
- A static web app that lets non-SQL users explore the same data.
- Everything defined in **AWS CDK (Python)** and removable with `cdk destroy`.

#### Contents

1. [Workshop Overview](5.1-workshop-overview/)
2. [Prerequisites](5.2-prerequisite/)
3. [Deploy the Agent](5.3-deploy-agent/)
4. [Test the Agent](5.4-test-agent/)
5. [Client Application Integration](5.5-client-integration/)
6. [Update & Extend](5.6-update-extend/)
7. [Clean Up Resources](5.7-cleanup/)
