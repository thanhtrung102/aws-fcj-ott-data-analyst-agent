---
title: "Test the Agent"
date: "2026-05-27"
weight: 4
chapter: false
pre: " <b> 5.4. </b> "
---

### Objective

Confirm the agent both **reasons** (writes a design brief) and **acts** (calls the image tool and returns a real mockup URL).

#### Option A — Bedrock console test window

1. Open **Amazon Bedrock → Agents → ProductDesigner** in `us-west-2`.
2. In the right-hand **Test** panel, make sure the alias is **live**, then enter:
   > *Design a reusable bamboo water bottle for Vietnamese university students.*
3. Click **Show trace**. You will see the orchestration steps: the model produces a rationale, then an **Action group invocation** of `generateProductImage`, then the tool's observation (the image URL), then the final answer.

> 💡 **Highlight:** The trace is the proof that this is an *agent*: notice the explicit `generateProductImage` action between the model's thinking and its final answer.

#### Option B — Headless invoke (CLI)

From `infra/`, with the virtual environment active:

```bash
python scripts/invoke_agent.py "Design a reusable bamboo water bottle for Vietnamese university students."
```

The script reads the `AgentId`/`AgentAliasId` from the stack outputs and calls `bedrock-agent-runtime:InvokeAgent`. Real (abridged) output:

```markdown
## 3. Key Features
1. 🌿 Natural Bamboo Outer Shell — sustainably sourced Vietnamese bamboo ...
2. 🧊 Double-Wall Vacuum Insulation — cold 12h / hot 6h ...
...
## 5. Accessibility
- ♿ One-Hand Operable Lid: screw cap needs < 90° rotation, low torque ...

## 🖼️ Product Mockup
![Bamboo Water Bottle Mockup](https://d2vtwrtxd9y2gt.cloudfront.net/images/b0dd62...png)
```

The returned URL is a real object the agent just generated:

![Sample generated mockup](/images/5-Workshop/sample-mockup.png)

*The agent wrote the brief, then generated this mockup via Stability Stable Image — note it matches the brief (bamboo body, forest-green lid, engraved motif).*

#### Verify the image landed in S3

```bash
aws s3 ls s3://<ImagesBucketName>/images/ --region us-west-2
```

Expected:

```
2026-05-27 23:16:36    2152732 b0dd62052d4c4c148eb6ae7019b8db72.png
```

Opening the CloudFront URL (`https://<ImagesDistributionDomain>/images/<key>.png`) returns the PNG with HTTP 200.

---

**Previous:** [5.3 Deploy the Agent](../5.3-deploy-agent/) | **Next:** [5.5 Client Application Integration](../5.5-client-integration/)
