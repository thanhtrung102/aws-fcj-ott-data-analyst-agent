---
title: "Update & Extend"
date: "2026-05-27"
weight: 6
chapter: false
pre: " <b> 5.6. </b> "
---

### Objective

See how fast the agent iterates. Because everything is infrastructure-as-code, changing the agent's behaviour is an edit plus one `cdk deploy`.

#### Example 1 — Change the persona

Open `infra/agent/instruction.txt` and narrow the agent to a niche. For example, add this line to the brief requirements:

```text
6. Sustainability - estimate the recycled/biodegradable content and end-of-life disposal path.
```

Redeploy just the agent stack:

```bash
cdk deploy ProductDesignerAgentStack --require-approval never
```

> 💡 **Highlight:** Only the `AWS::Bedrock::Agent` resource changes; CloudFormation updates it in place and `auto_prepare` re-prepares the agent. Re-run 5.4's test and the brief now includes a Sustainability section.

#### Example 2 — Tune the image style

In `infra/lambda/generate_image/handler.py`, change the default style appended to every prompt (for example, force a consistent catalog look):

```python
body = {
    "prompt": text[:2000],
    "mode": "text-to-image",
    "aspect_ratio": "4:5",          # portrait catalog framing
    "output_format": "png",
}
```

`cdk deploy ProductDesignerAgentStack` ships the new Lambda code in seconds.

#### Example 3 — Swap the foundation model

The agent model is configurable via CDK context — no code edit needed:

```bash
cdk deploy ProductDesignerAgentStack -c agentModel=us.anthropic.claude-haiku-4-5-20251001-v1:0
```

Use a smaller model (Haiku) for faster, cheaper drafts; a larger one (Sonnet) for richer briefs.

#### Example 4 — Add a second tool

Add a `saveDesignBrief` function to the action group that writes the brief to S3 as Markdown, then grant the Lambda `s3:PutObject`. The agent will start offering to save briefs once the tool exists and the instruction mentions it.

---

**Previous:** [5.5 Client Application Integration](../5.5-client-integration/) | **Next:** [5.7 Clean Up Resources](../5.7-cleanup/)
