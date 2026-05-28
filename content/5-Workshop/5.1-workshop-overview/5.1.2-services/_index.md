---
title: "Services Used"
date: "2026-05-28"
weight: 2
chapter: false
pre: " <b> 5.1.2. </b> "
---

### Services Used

| Service | Why it is used | Cost model |
|---------|----------------|-----------|
| **Amazon Bedrock — Agents** | Hosts the OTT Data Analyst agent and orchestrates the reason–act loop | Per agent invocation (charged as model tokens) |
| **Amazon Bedrock — Anthropic Claude Haiku 4.5** (`global.anthropic.claude-haiku-4-5-20251001-v1:0`) | The reasoning model that writes SQL and summarises results | Per input/output token (~$0.0008/1k input, ~$0.004/1k output) |
| **AWS Glue Data Catalog** | Metadata store for the existing OTT tables; powers the `get_tables`/`get_table` tools | Free (within reasonable API call limits) |
| **Amazon Athena** | Serverless Presto/Trino over S3; executes the SQL the agent writes | **$5 per TB scanned** — workshop queries scan KBs to MBs, costing < $0.01 |
| **AWS Lambda** | Runs the action-group tools (`get_tables`, `get_table`, `athena_query`) and the public `invoke_agent` API | Per request + duration (free-tier friendly) |
| **Amazon S3** | Stores Athena results (with 14-day lifecycle) and the static web app | Per GB + requests (pennies) |
| **Amazon CloudFront** | CDN that serves the web app over HTTPS | Per GB transferred (essentially zero idle) |
| **AWS IAM** | Least-privilege roles for the agent and Lambdas | Free |
| **AWS Lake Formation** | Required for the action-group Lambda to read the existing OTT tables (LF-managed) | Free |
| **AWS CDK (Python)** | Infrastructure as code — one command to deploy and destroy | Free (uses CloudFormation) |

#### Region note

> 💡 **Highlight:** This workshop deploys to **`ap-southeast-1` (Singapore)**. That is where the upstream FPT Play SDLF pipeline (and its `fpt_ott_searchevents_analytics` Glue catalog) already lives. Anthropic Claude Haiku 4.5 is available there via the **global inference profile** `global.anthropic.claude-haiku-4-5-20251001-v1:0` — the only Claude profile that routes to apse1 today, so we use it.

#### What you will NOT need

- **No Docker.** All Lambdas are packaged as plain ZIP archives (their only runtime dependency, `boto3`, ships in the Lambda runtime).
- **No servers to manage.** Every component is serverless or fully managed.
- **No vector database / knowledge base.** The 17-column `curated` schema is small enough that we inline it in the agent's instruction; the agent does not need RAG.
- **No new data pipeline.** The workshop *consumes* the existing `curated` table; it does not rebuild it.
