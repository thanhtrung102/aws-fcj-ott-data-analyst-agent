---
title: "Client Application Integration"
date: "2026-05-28"
weight: 5
chapter: false
pre: " <b> 5.5. </b> "
---

### Objective

Put a browser UI in front of the agent so analysts and PMs who don't know SQL can ask questions. The web app holds **no AWS credentials** — it calls a serverless endpoint that invokes the agent on its behalf.

#### Why a Lambda Function URL (not API Gateway)?

> 💡 **Highlight:** The agent's reason-then-run-Athena loop typically takes **15–30 seconds** on cold path and can spike to 60s+ when scanning multiple partitions. Amazon API Gateway has a **hard 30-second** integration timeout, so a synchronous call through it would return 503 mid-query. A **Lambda Function URL** has no such cap — it honours the Lambda's own timeout (we set 120s). That is why `OttDataAnalystApiStack` exposes a Function URL.

#### 1. Deploy the API and web stacks

```bash
cd infra
source .venv/Scripts/activate
cdk deploy OttDataAnalystApiStack OttDataAnalystWebStack --require-approval never
```

Outputs:

```
OttDataAnalystApiStack.ApiUrl = https://6xfis6ttruifkbaxtemu3evwde0bkfyc.lambda-url.ap-southeast-1.on.aws/
OttDataAnalystWebStack.WebUrl = https://d31ailu10g1wh5.cloudfront.net
```

#### 2. Smoke-test the API

```bash
curl -s -X POST "https://6xfis6ttruifkbaxtemu3evwde0bkfyc.lambda-url.ap-southeast-1.on.aws/" \
  -H "content-type: application/json" \
  -d '{"prompt":"Top 10 search keywords overall in the 14-day window, including any genre. Show counts."}' \
  --max-time 120 | python -m json.tool
```

The response is JSON with an `answer` field containing the analyst's summary + Markdown table, plus a `sessionId` you can pass back on follow-up calls to preserve conversation state.

> ✅ **Verified end-to-end:** `curl` against the Function URL returned **HTTP 200 in 8.96s** with a full analyst answer and the Athena rows — past the old 30s API Gateway wall.

#### 3. Use the web app

Open the `WebUrl` in a browser, type a question, and click **Ask**. After ~15-30s you get the brief, the result table, and 1-2 follow-up suggestions.

Sample questions seeded in the SPA:

- *Top 10 search keywords overall in the 14-day window*
- *How does the genre mix differ on mobile vs TV?*
- *Which day had the most abandoned searches and why?*
- *List the top UNKNOWN keywords by frequency*
- *Which hour of the day has the highest search volume?*

#### Request flow

```
Browser ──fetch POST──> Lambda Function URL ──InvokeAgent──> Bedrock Agent
                                                                  │
                                              (action group → Glue/Athena → result rows)
                                                                  │
Browser <──── JSON {answer, sessionId} ◄──────────────────────────┘
Static assets: Browser ──> CloudFront ──> S3 (index.html, app.js, config.js)
```

`config.js` is generated at deploy time with the Function URL via `BucketDeployment(Source.data(...))`; the SPA's `app.js` reads `window.API_URL` and POSTs there.

> ⚠️ **Security note:** Function URL uses `AuthType: NONE` and permissive CORS for workshop simplicity. For production, add Cognito (or IAM auth) and restrict CORS to your domain. The Lambda role grants `bedrock:InvokeAgent` only on the specific alias ARN, so even a stray call cannot invoke other agents.

---

**Previous:** [5.4 Test the Agent](../5.4-test-agent/) | **Next:** [5.6 Update & Extend](../5.6-update-extend/)
