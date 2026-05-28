---
title: "Deploy the Agent"
date: "2026-05-27"
weight: 3
chapter: false
pre: " <b> 5.3. </b> "
---

### Objective

Deploy the Bedrock Agent, its `generateProductImage` action group, the images S3 bucket, and a CloudFront distribution — all with a single `cdk deploy`.

#### 1. Review the agent definition

Two files define the agent's behaviour:

- `infra/agent/instruction.txt` — the **persona**. It tells Claude to produce a 5-part design brief and then call the image tool exactly once.
- The **action group** is declared in `infra/stacks/agent_stack.py` as a *function schema* with one function:

```python
bedrock.CfnAgent.FunctionProperty(
    name="generateProductImage",
    description="Generate a photorealistic product mockup image ...",
    parameters={
        "prompt": ParameterDetailProperty(type="string", required=True, ...),
        "style":  ParameterDetailProperty(type="string", required=False, ...),
    },
)
```

When the model calls this function, Bedrock invokes `infra/lambda/generate_image/handler.py`, which calls Stability Stable Image and stores the PNG in S3.

> 💡 **Highlight:** The agent's foundation model is a **cross-region inference profile** (`us.anthropic.claude-sonnet-4-6`). The agent's IAM role is granted `bedrock:InvokeModel` on both foundation models and inference profiles so the profile can route across regions.

#### 2. Deploy

```bash
cd infra
source .venv/Scripts/activate      # .venv/bin/activate on macOS/Linux
cdk deploy ProductDesignerAgentStack --require-approval never
```

Expected output (≈ 5 minutes — CloudFront is the slow part):

```
ProductDesignerAgentStack | CREATE_COMPLETE | AWS::Lambda::Function    | GenerateImageFn
ProductDesignerAgentStack | CREATE_COMPLETE | AWS::Bedrock::Agent      | Agent
ProductDesignerAgentStack | CREATE_COMPLETE | AWS::Bedrock::AgentAlias | Alias
ProductDesignerAgentStack | CREATE_COMPLETE | AWS::CloudFormation::Stack | ProductDesignerAgentStack

 ✅  ProductDesignerAgentStack

Outputs:
ProductDesignerAgentStack.AgentId = VYIT8TZEM5
ProductDesignerAgentStack.AgentAliasId = NKM6XZAGB4
ProductDesignerAgentStack.ImagesBucketName = productdesigneragentstack-imagesbucket...
ProductDesignerAgentStack.ImagesDistributionDomain = d2vtwrtxd9y2gt.cloudfront.net
Deployment time: 275.63s
```

Your IDs will differ — note the `AgentId` and `AgentAliasId`.

#### 3. What was created

| Resource | Purpose |
|----------|---------|
| `AWS::Bedrock::Agent` (`ProductDesigner`) | The agent: instruction + Claude + action group |
| `AWS::Bedrock::AgentAlias` (`live`) | A stable, versioned pointer used to invoke the agent |
| `AWS::Lambda::Function` (`GenerateImageFn`) | Action-group tool: calls Stability, writes PNG to S3 |
| `AWS::S3::Bucket` (images) | Stores generated mockups (private; served via CloudFront) |
| `AWS::CloudFront::Distribution` | Serves the images over HTTPS |
| `AWS::IAM::Role` (agent + Lambda) | Least-privilege roles |

#### Verification

```bash
aws cloudformation describe-stacks --stack-name ProductDesignerAgentStack \
  --region us-west-2 --query "Stacks[0].Outputs[].[OutputKey,OutputValue]" --output table
```

You should see four outputs including a valid `AgentId` and `AgentAliasId`.

---

**Previous:** [5.2 Prerequisites](../5.2-prerequisite/) | **Next:** [5.4 Test the Agent](../5.4-test-agent/)
