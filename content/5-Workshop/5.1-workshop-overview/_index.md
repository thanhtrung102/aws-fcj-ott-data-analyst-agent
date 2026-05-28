---
title: "Workshop Overview"
date: "2026-05-28"
weight: 1
chapter: false
pre: " <b> 5.1. </b> "
---

### Overview

In this workshop you will build an **AI Data Analyst agent** for FPT Play OTT — a generative-AI assistant that takes a plain-language question and returns:

1. A short narrative answer (2–4 sentences) summarising what was found.
2. The supporting **Athena result table** (top 10 rows of the actual SQL output).
3. One or two **follow-up question suggestions** the user might ask next.

The agent is fully **serverless** and **reproducible**: defined in AWS CDK, deployed with one command, and removed with one command.

> 💡 **Highlight:** The agent does not just *talk* about the data — it **acts**, writing Presto/Trino SQL and executing it on Amazon Athena. The "reason + act + read + answer" loop is what makes it an *agent* rather than a chatbot.

#### Architecture at a glance

| Layer | Service | Role |
|-------|---------|------|
| Reasoning | Anthropic Claude Haiku 4.5 on Amazon Bedrock | Interprets the question and writes SQL |
| Orchestration | Amazon Bedrock Agent + Action Group | Wraps the model with an instruction and three tools |
| Catalog | AWS Glue Data Catalog | Metadata for the existing `curated` table |
| SQL engine | Amazon Athena | Serverless Presto/Trino over S3 |
| Storage | Amazon S3 (Athena results, 14-day lifecycle) | Query result cache |
| API | AWS Lambda + Lambda Function URL | A thin, Docker-free layer that invokes the agent |
| Frontend | Static web app on S3 + CloudFront | A browser UI to chat with the agent |

#### Dataset under analysis

The agent points at an **existing** Glue catalog already populated by an upstream SDLF pipeline:

| | |
|---|---|
| Database | `fpt_ott_searchevents_analytics` |
| Table | `curated` |
| Partition keys | `dt` (YYYY-MM-DD), `derived_genre` |
| Row count | ~1.15 M curated rows total |
| Workshop window | **2022-06-01 → 2022-06-14** (14 days) |
| Genre codes | `PHIM_TRUNG`, `PHIM_VIET`, `PHIM_HAN`, `PHIM_AU_MY`, `ANIME`, `THE_THAO`, `NHAC`, `TRUYEN_HINH`, `UNKNOWN` |

#### Implementation Steps

1. [What is a Bedrock Agent?](5.1.1-what-is-a-bedrock-agent/)
2. [Services Used](5.1.2-services/)
