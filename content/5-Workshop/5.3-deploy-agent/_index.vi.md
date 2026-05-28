---
title: "Triển khai Tác nhân"
date: "2026-05-28"
weight: 3
chapter: false
pre: " <b> 5.3. </b> "
---

### Mục tiêu

Triển khai Bedrock Agent, action group ba công cụ của nó, và bucket lưu kết quả Athena — tất cả bằng một lệnh `cdk deploy`.

#### 1. Xem định nghĩa tác nhân

Hai file định nghĩa hành vi tác nhân:

- `infra/agent/instruction.txt` — **persona**. Cho Claude biết nó là nhà phân tích dữ liệu OTT, cấp toàn bộ schema `curated`, giới hạn truy vấn trong cửa sổ 14 ngày 2022-06-01 → 2022-06-14, cấm bịa dữ liệu.
- **Action group** được khai báo trong `infra/stacks/agent_stack.py` dưới dạng *function schema* với ba hàm:

```python
bedrock.CfnAgent.FunctionProperty(name="get_tables", ...)
bedrock.CfnAgent.FunctionProperty(name="get_table",  ...)
bedrock.CfnAgent.FunctionProperty(name="athena_query", ...)
```

Khi mô hình gọi bất kỳ hàm nào, Bedrock gọi `infra/lambda/glue_athena_tools/handler.py` (phỏng theo `aws-samples/sample-Agentic-Ai-Data-Operations`, `mcp-servers/glue-athena-server/lambda_handler.py`).

> 💡 **Điểm nhấn:** Mô hình nền tảng của tác nhân là **global inference profile** `global.anthropic.claude-haiku-4-5-20251001-v1:0`. Role IAM của tác nhân được cấp `bedrock:InvokeModel` trên cả foundation model lẫn inference profile để profile có thể route cross-region vào apse1.

#### 2. Triển khai

```bash
cd infra
source .venv/Scripts/activate      # .venv/bin/activate cho macOS/Linux
cdk deploy OttDataAnalystAgentStack --require-approval never
```

Kết quả mong đợi (≈ 3–5 phút):

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

#### 3. Những gì đã được tạo

| Tài nguyên | Mục đích |
|----------|---------|
| `AWS::Bedrock::Agent` (`OttDataAnalyst`) | Tác nhân: instruction + Claude Haiku 4.5 + action group |
| `AWS::Bedrock::AgentAlias` (`live`) | Con trỏ ổn định, có phiên bản, dùng để gọi tác nhân |
| `AWS::Lambda::Function` (`GlueAthenaToolsFn`) | Công cụ action group: route `get_tables` / `get_table` / `athena_query` |
| `AWS::S3::Bucket` (results) | Lưu kết quả truy vấn Athena, lifecycle 14 ngày |
| `AWS::IAM::Role` × 2 | Đặc quyền tối thiểu (Glue + Athena read cho tools Lambda; Bedrock invoke cho tác nhân) |

#### 4. Cấp Lake Formation SELECT (chỉ nếu `curated` được LF-managed)

Output CDK ở trên in ra **chính xác** Lambda role ARN. Nếu pipeline OTT của bạn dùng Lake Formation, cấp SELECT trên bảng curated cho role đó:

```bash
ROLE_ARN=arn:aws:iam::703668403514:role/OttDataAnalystAgentStack-GlueAthenaToolsFnServiceRole-CzQythD4q1BO

aws lakeformation grant-permissions \
  --principal DataLakePrincipalIdentifier=$ROLE_ARN \
  --resource '{"Table":{"DatabaseName":"fpt_ott_searchevents_analytics","Name":"curated"}}' \
  --permissions SELECT \
  --region ap-southeast-1
```

Nếu pipeline không dùng Lake Formation, IAM policy trong `agent_stack.py` đã đủ.

#### Kiểm tra

```bash
aws cloudformation describe-stacks --stack-name OttDataAnalystAgentStack \
  --region ap-southeast-1 \
  --query "Stacks[0].Outputs[].[OutputKey,OutputValue]" --output table
```

Bạn sẽ thấy bốn output bao gồm `AgentId` và `AgentAliasId` hợp lệ.

---

**Trước:** [5.2 Chuẩn bị](../5.2-prerequisite/) | **Tiếp:** [5.4 Kiểm thử Tác nhân](../5.4-test-agent/)
