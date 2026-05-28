---
title: "Client Application Integration"
date: "2026-05-27"
weight: 5
chapter: false
pre: " <b> 5.5. </b> "
---

### Objective

Put a browser UI in front of the agent. The web app holds **no AWS credentials** — it calls a serverless endpoint that invokes the agent for it.

#### Why a Lambda Function URL (not API Gateway)?

> 💡 **Highlight:** The agent's reason-then-generate-image loop takes **~35–45 seconds**. Amazon API Gateway has a **hard 30-second** integration timeout, so a synchronous call through it returns `503` before the image is ready. A **Lambda Function URL** has no such cap — it honours the Lambda's own timeout (we set 120s). That is why `ProductDesignerApiStack` exposes a Function URL.

#### 1. Deploy the API and web stacks

```bash
cd infra
source .venv/Scripts/activate
cdk deploy ProductDesignerApiStack ProductDesignerWebStack --require-approval never
```

Outputs:

```
ProductDesignerApiStack.ApiUrl = https://<id>.lambda-url.us-west-2.on.aws/
ProductDesignerWebStack.WebUrl = https://<dist>.cloudfront.net
```

#### 2. Smoke-test the API

```bash
curl -s -X POST "<ApiUrl>" \
  -H "content-type: application/json" \
  -d '{"prompt":"Design a compact foldable solar phone charger for street vendors"}' \
  --max-time 120 | python -m json.tool
```

The response is JSON with an `answer` field containing the design brief and a Markdown image link to the generated mockup, plus a `sessionId`.

#### 3. Use the web app

Open the `WebUrl` in a browser, type a product idea, and click **Design it**. After ~30–45s you get the brief and the generated mockup rendered inline.

> ✅ **Verified end-to-end from this deployment:** `curl` against the Function URL returned **HTTP 200 in 30.5s** with a complete design brief (concept → 6 features → materials table → accessibility) and a generated mockup URL on the images CloudFront — past the old 30s API Gateway wall, with the agent's tool call completing inside the request.

#### Request flow

```
Browser ──fetch POST──> Lambda Function URL ──InvokeAgent──> Bedrock Agent
                                                                  │
                                                       (action group → Stability → S3)
                                                                  │
Browser <──── JSON {answer, sessionId} ◄──────────────────────────┘
Static assets: Browser ──> CloudFront ──> S3 (index.html, app.js, config.js)
```

`config.js` (the only environment-specific file) is generated at deploy time with the Function URL, so the same static assets work for any deployment.

> ⚠️ **Security note:** For workshop simplicity the Function URL uses `AuthType: NONE` and permissive CORS. For production, put the endpoint behind Amazon Cognito (or IAM auth) and restrict CORS to your domain.

---

**Previous:** [5.4 Test the Agent](../5.4-test-agent/) | **Next:** [5.6 Update & Extend](../5.6-update-extend/)
