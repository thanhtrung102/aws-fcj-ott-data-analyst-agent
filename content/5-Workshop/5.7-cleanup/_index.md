---
title: "Clean Up Resources"
date: "2026-05-28"
weight: 7
chapter: false
pre: " <b> 5.7. </b> "
---

### Objective

Remove everything you created so there are no ongoing charges. Bedrock itself is pay-per-use (nothing to delete), but S3 (Athena results + web SPA), CloudFront, Lambda, and the agent are torn down by CDK. **The upstream OTT data pipeline is untouched** — only the three workshop stacks are removed.

> ✅ **Verified end-to-end:** All three stacks were deleted in order (Web → Api → Agent) and reached `DELETE_COMPLETE`. The S3 buckets were auto-emptied by their `auto_delete_objects` custom resources, so no manual cleanup was needed.

#### Steps (ordered)

1. **Destroy all stacks (CDK):**
   ```bash
   cd infra
   cdk destroy --all --force
   ```
   This removes Web → Api → Agent in reverse dependency order.

2. **Or the low-memory equivalent** (if `cdk destroy` OOMs):
   ```bash
   for STACK in OttDataAnalystWebStack OttDataAnalystApiStack OttDataAnalystAgentStack; do
     aws cloudformation delete-stack --stack-name $STACK --region ap-southeast-1
     aws cloudformation wait stack-delete-complete --stack-name $STACK --region ap-southeast-1
   done
   ```

3. **Verify** in the CloudFormation console that all `OttDataAnalyst*` stacks are gone:
   ```bash
   aws cloudformation list-stacks --region ap-southeast-1 \
     --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
     --query "StackSummaries[?starts_with(StackName,'OttDataAnalyst')].StackName" \
     --output text
   ```

4. (Optional) Revoke the Lake Formation grant from 5.2 #6 if no longer needed:
   ```bash
   aws lakeformation revoke-permissions \
     --principal DataLakePrincipalIdentifier=<ROLE_ARN_FROM_5.2> \
     --resource "{\"Table\":{\"DatabaseName\":\"fpt_ott_searchevents_analytics\",\"Name\":\"curated\"}}" \
     --permissions SELECT --region ap-southeast-1
   ```

5. (Optional) Disable Bedrock model access if you no longer need it.

#### Cleanup checklist

- [ ] Athena results S3 bucket emptied and deleted
- [ ] Web S3 bucket emptied and deleted
- [ ] CloudFront web distribution removed
- [ ] Bedrock Agent + alias removed
- [ ] Three Lambda functions + IAM roles removed (`GlueAthenaToolsFn`, `InvokeAgentFn`, two custom-resource Lambdas)
- [ ] No `OttDataAnalyst*` stacks remain in CloudFormation
- [ ] Upstream `fpt_ott_searchevents_analytics.curated` is **still healthy** (verify by re-running the dashboard at the SDLF CloudFront URL)

#### What is NOT cleaned up (intentionally)

The workshop **never wrote to the OTT raw or curated S3 buckets**, **never modified the Glue catalog**, and **never invoked the upstream pipeline's Lambdas or Step Functions**. After cleanup the OTT data lake is in exactly the state you found it in.

---

**Previous:** [5.6 Update & Extend](../5.6-update-extend/)
