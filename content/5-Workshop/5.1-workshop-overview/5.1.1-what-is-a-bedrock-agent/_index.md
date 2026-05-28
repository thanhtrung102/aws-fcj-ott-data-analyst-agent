---
title: "What is a Bedrock Agent?"
date: "2026-05-28"
weight: 1
chapter: false
pre: " <b> 5.1.1. </b> "
---

### What is an Amazon Bedrock Agent?

A **foundation model (FM)** like Anthropic Claude can *generate text*, but on its own it cannot *do* anything — it cannot fetch data or query a database. An **Amazon Bedrock Agent** closes that gap. It combines three things:

- **An instruction** — a natural-language description of the agent's role (here: an FPT Play OTT data analyst with a documented schema and a 14-day query window).
- **A foundation model** — the reasoning engine (here: Anthropic Claude Haiku 4.5 via the `global.anthropic.*` inference profile).
- **Action groups** — tools the agent may call. Each action group points to a **Lambda function** and a schema describing the operations the model is allowed to invoke.

> 💡 **Highlight:** You never call the Lambda directly. You send a question to the agent; the model *decides* which tool to invoke (often `get_table` first, then `athena_query`), Bedrock invokes your Lambda, feeds the result back to the model, and the model writes the final summarised answer.

#### The reason–act loop for an analyst question

```
User: "Top 10 search keywords in PHIM_HAN during week 1 of June 2022?"
        │
        ▼
  Bedrock Agent (Claude Haiku 4.5)
   1. Think: I have the schema in my instruction. I can write the SQL directly.
   2. Act:   athena_query(query="SELECT keyword_norm, COUNT(*) AS n
                                  FROM fpt_ott_searchevents_analytics.curated
                                  WHERE dt BETWEEN '2022-06-01' AND '2022-06-07'
                                    AND derived_genre = 'PHIM_HAN'
                                    AND keyword_norm IS NOT NULL
                                  GROUP BY keyword_norm
                                  ORDER BY n DESC
                                  LIMIT 10",
                          database="fpt_ott_searchevents_analytics")
        │
        ▼
  Action Group Lambda  ──>  Athena.StartQueryExecution  ──>  poll  ──>  GetQueryResults
        │
        ▼
   3. Read the tool result: 10 rows of {keyword_norm, n}
   4. Answer: narrative + Markdown table + suggested follow-up
```

#### Why an agent here (not just a chatbot)?

A chatbot can describe what kinds of queries are *possible*. Our agent **produces an artifact** — a real query result against real data — by calling a tool. That is the essence of *agentic* AI: language models that take actions in the world through APIs you control.

It is also why the same architecture scales: replace the Athena tool with a DynamoDB tool, or add a chart-rendering tool, and the agent gains new capabilities without changing the model.

#### Key vocabulary

| Term | Meaning |
|------|---------|
| **Instruction** | The agent's persona, schema knowledge, scope rules — in plain language |
| **Action group** | A set of callable operations, backed by a Lambda + function schema |
| **Function schema** | Per-function `name`, `description`, `parameters` so the model knows how to call them |
| **Agent alias** | A stable, versioned pointer used to invoke the agent from applications |
| **Orchestration** | Bedrock's built-in loop that decides when to call tools and when to answer |
