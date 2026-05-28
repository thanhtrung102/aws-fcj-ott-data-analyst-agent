---
title: "Prerequisites"
date: "2026-05-28"
weight: 2
chapter: false
pre: " <b> 5.2. </b> "
---

### Prerequisites

You need an AWS account with administrative access, the existing OTT Glue catalog, and a few local tools. **Docker is not required.**

#### 1. Existing OTT data pipeline

This workshop *consumes* an existing Glue catalog populated by an upstream SDLF pipeline. Before starting, verify in `ap-southeast-1`:

```bash
aws glue get-table \
  --database-name fpt_ott_searchevents_analytics \
  --name curated \
  --region ap-southeast-1 \
  --query "Table.[Name,PartitionKeys[].Name]" \
  --output text
```

Expected:

```
curated
dt   derived_genre
```

And the 14-day partition window must exist:

```bash
aws athena start-query-execution \
  --query-string "SELECT MIN(dt), MAX(dt), COUNT(DISTINCT dt) FROM fpt_ott_searchevents_analytics.curated WHERE dt BETWEEN '2022-06-01' AND '2022-06-14'" \
  --query-execution-context Database=fpt_ott_searchevents_analytics \
  --result-configuration OutputLocation=s3://aws-athena-query-results-<ACCT>-ap-southeast-1/ \
  --region ap-southeast-1
```

The result should report at least 14 distinct partition days in that range.

#### 2. Enable Amazon Bedrock model access

In the AWS Console, switch to **`ap-southeast-1` (Singapore)**, open **Amazon Bedrock → Model access**, and request access to:

- **Anthropic — Claude Haiku 4.5** via the **global inference profile** `global.anthropic.claude-haiku-4-5-20251001-v1:0`.

> 💡 **Highlight:** apse1 does not yet host Anthropic Claude directly. The `global.anthropic.*` inference profile **routes cross-region** and is the only Claude that works in apse1 today. The Marketplace agreement must be accepted once (`bedrock create-foundation-model-agreement` with `--policy AWSMarketplaceManageSubscriptions`).

Verify access:

```bash
aws bedrock get-inference-profile \
  --inference-profile-identifier global.anthropic.claude-haiku-4-5-20251001-v1:0 \
  --region ap-southeast-1 \
  --query "[inferenceProfileName,status]" --output text
```

Expected: `Claude Haiku 4.5 ACTIVE`.

#### 3. Required tools

| Tool | Minimum version | Check |
|------|-----------------|-------|
| AWS CLI v2 | 2.15+ | `aws --version` |
| Node.js | 20.19+ | `node --version` |
| AWS CDK | 2.1000+ | `cdk --version` |
| Python | 3.11+ | `python --version` |
| Git | any | `git --version` |

Install the AWS CDK CLI if needed:

```bash
npm install -g aws-cdk
```

#### 4. Configure credentials

```bash
aws configure
# Access key / secret for an admin IAM user
# Default region name: ap-southeast-1
# Default output format: json
```

#### 5. Get the project and bootstrap CDK

```bash
git clone --recurse-submodules https://github.com/thanhtrung102/aws-fcj-ott-data-analyst-agent.git
cd aws-fcj-ott-data-analyst-agent/infra
python -m venv .venv
source .venv/Scripts/activate    # Windows Git Bash; use source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cdk bootstrap aws://<ACCOUNT_ID>/ap-southeast-1
```

> 💡 **Highlight:** `--recurse-submodules` pulls the Hugo theme (`themes/hugo-theme-relearn`, ~1.1 GB of history). Skip the flag if you only want to deploy the CDK app — the theme is only needed to build the docs locally. On Windows Git Bash, the `cdk` CLI lives under `~/AppData/Roaming/npm/` and may not be on the bash `PATH`; add it once with `export PATH="$APPDATA/npm:$PATH"` if `cdk --version` fails.

#### 6. Lake Formation grant (required if the curated table is LF-managed)

If the upstream OTT pipeline uses Lake Formation, the new Lambda role created by `cdk deploy` needs SELECT on `fpt_ott_searchevents_analytics.curated`:

```bash
aws lakeformation grant-permissions \
  --principal DataLakePrincipalIdentifier=arn:aws:iam::<ACCT>:role/OttDataAnalystAgentStack-GlueAthenaToolsFnServiceRole-XXXXX \
  --resource "{\"Table\":{\"DatabaseName\":\"fpt_ott_searchevents_analytics\",\"Name\":\"curated\"}}" \
  --permissions SELECT \
  --region ap-southeast-1
```

The exact role name appears in the CDK deploy output of 5.3.

#### Expected state after prerequisites

- `aws sts get-caller-identity` returns your account.
- Bedrock global inference profile for **Claude Haiku 4.5** is **granted** in `ap-southeast-1`.
- `cdk --version` works and `cdk bootstrap` has created the CDK toolkit stack in apse1.
- `fpt_ott_searchevents_analytics.curated` is reachable from the CLI user.

#### Troubleshooting — low-memory machines

> ⚠️ `aws-cdk-lib` is large; `cdk synth/deploy` can need ~1.5 GB peak (Python + Node jsii). On a machine with **< 2 GB of free RAM**, expect intermittent `MemoryError` or Node exit 134 during synth.
>
> **Workaround:** synthesize once when memory is available (`cdk synth`), then deploy each stack with the AWS CLI (no `aws-cdk-lib` import):
>
> ```bash
> cdk synth   # one-time, writes cdk.out/<Stack>.template.json + asset dirs
>
> for STACK in OttDataAnalystAgentStack OttDataAnalystApiStack OttDataAnalystWebStack; do
>   aws cloudformation deploy --template-file cdk.out/$STACK.template.json \
>     --stack-name $STACK --region ap-southeast-1 \
>     --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
> done
> ```
>
> If even `cdk synth` OOMs, the asset hashes are content-addressed — once you upload assets to `cdk-hnb659fds-assets-<acct>-ap-southeast-1` once, subsequent re-deploys can reuse them without re-synth.

---

**Next:** [5.3 Deploy the Agent](../5.3-deploy-agent/)
