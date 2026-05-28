---
title: "Deploy the Agent"
date: "2026-05-28"
weight: 3
chapter: false
pre: " <b> 5.3. </b> "
---

### Objective

Deploy the Bedrock Agent, its three-tool action group, and the Athena results bucket — all with a single `cdk deploy`.

#### 1. Review the agent definition

Two files define the agent's behaviour:

- `infra/agent/instruction.txt` — the **persona**. It tells Claude it is an OTT data analyst, gives it the full `curated` schema, scopes queries to the 14-day window 2022-06-01 → 2022-06-14, and forbids inventing rows.
- The **action group** is declared in `infra/stacks/agent_stack.py` as a *function schema* with three functions:

```python
bedrock.CfnAgent.FunctionProperty(name="get_tables", ...)
bedrock.CfnAgent.FunctionProperty(name="get_table",  ...)
bedrock.CfnAgent.FunctionProperty(name="athena_query", ...)
```

When the model calls any of these, Bedrock invokes `infra/lambda/glue_athena_tools/handler.py` (adapted from `aws-samples/sample-Agentic-Ai-Data-Operations`, `mcp-servers/glue-athena-server/lambda_handler.py`).

> 💡 **Highlight:** The agent's foundation model is the **global inference profile** `global.anthropic.claude-haiku-4-5-20251001-v1:0`. The agent's IAM role is granted `bedrock:InvokeModel` on both foundation models and inference profiles so the profile can route cross-region into apse1.

#### 2. Deploy

```bash
cd infra
source .venv/Scripts/activate      # .venv/bin/activate on macOS/Linux
cdk deploy OttDataAnalystAgentStack --require-approval never
```

Expected output (≈ 3–5 minutes):

```
OttDataAnalystAgentStack | CREATE_COMPLETE | AWS::Lambda::Function    | GlueAthenaToolsFn
OttDataAnalystAgentStack | CREATE_COMPLETE | AWS::Bedrock::Agent      | Agent
OttDataAnalystAgentStack | CREATE_COMPLETE | AWS::Bedrock::AgentAlias | Alias
OttDataAnalystAgentStack | CREATE_COMPLETE | AWS::CloudFormation::Stack | OttDataAnalystAgentStack

 ✅  OttDataAnalystAgentStack

Outputs:
OttDataAnalystAgentStack.AgentId            = 1DEBH3YNM3
OttDataAnalystAgentStack.AgentAliasId       = FF7ESZIKUT
OttDataAnalystAgentStack.ResultsBucketName  = ottdataanalystagentstack-resultsbucket-rcoyosyqkjgw
OttDataAnalystAgentStack.GlueDatabase       = fpt_ott_searchevents_analytics
```

#### 3. What was created

| Resource | Purpose |
|----------|---------|
| `AWS::Bedrock::Agent` (`OttDataAnalyst`) | The agent: instruction + Claude Haiku 4.5 + action group |
| `AWS::Bedrock::AgentAlias` (`live`) | Stable, versioned pointer used to invoke the agent |
| `AWS::Lambda::Function` (`GlueAthenaToolsFn`) | Action-group tool: routes `get_tables` / `get_table` / `athena_query` |
| `AWS::S3::Bucket` (results) | Stores Athena query results, 14-day lifecycle |
| `AWS::IAM::Role` × 2 | Least-privilege roles (Glue + Athena read for the tools Lambda; Bedrock invoke for the agent) |

#### 4. Grant Lake Formation SELECT (only if `curated` is LF-managed)

The CDK output above prints the **exact** Lambda role ARN. If your OTT pipeline uses Lake Formation, grant SELECT on the curated table to that role:

```bash
ROLE_ARN=arn:aws:iam::703668403514:role/OttDataAnalystAgentStack-GlueAthenaToolsFnServiceRole-CzQythD4q1BO

aws lakeformation grant-permissions \
  --principal DataLakePrincipalIdentifier=$ROLE_ARN \
  --resource '{"Table":{"DatabaseName":"fpt_ott_searchevents_analytics","Name":"curated"}}' \
  --permissions SELECT \
  --region ap-southeast-1
```

If your pipeline does not use Lake Formation, the IAM policy in `agent_stack.py` is already sufficient.

#### Verification

```bash
aws cloudformation describe-stacks --stack-name OttDataAnalystAgentStack \
  --region ap-southeast-1 \
  --query "Stacks[0].Outputs[].[OutputKey,OutputValue]" --output table
```

You should see four outputs including a valid `AgentId` and `AgentAliasId`.

---

**Previous:** [5.2 Prerequisites](../5.2-prerequisite/) | **Next:** [5.4 Test the Agent](../5.4-test-agent/)
