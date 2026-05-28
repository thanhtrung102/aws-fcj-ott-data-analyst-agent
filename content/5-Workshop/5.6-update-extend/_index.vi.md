---
title: "Cập nhật & Mở rộng"
date: "2026-05-28"
weight: 6
chapter: false
pre: " <b> 5.6. </b> "
---

### Mục tiêu

Xem tác nhân lặp nhanh thế nào. Vì mọi thứ là IaC, đổi hành vi tác nhân chỉ cần một chỉnh sửa + một `cdk deploy`.

#### Ví dụ 1 — Mở rộng cửa sổ truy vấn

Mở `infra/agent/instruction.txt` và đổi phạm vi workshop từ `2022-06-01 → 2022-06-14` thành toàn bộ 21 ngày (`2022-06-01 → 2022-06-23`):

```diff
- Workshop scope: the 14-day window 2022-06-01 through 2022-06-14 (inclusive).
+ Workshop scope: the 21-day window 2022-06-01 through 2022-06-23 (inclusive).
```

Redeploy chỉ agent stack:

```bash
cdk deploy OttDataAnalystAgentStack --require-approval never
```

> 💡 **Điểm nhấn:** Chỉ `AWS::Bedrock::Agent` thay đổi; CloudFormation update tại chỗ và `auto_prepare` tự prepare lại agent. Đặt lại câu hỏi — agent sẽ scope vào cửa sổ rộng hơn mà không cần đổi code.

#### Ví dụ 2 — Thêm công cụ thứ tư: `list_partitions`

Power user đôi khi muốn biết **dữ liệu nào tồn tại** trước khi hỏi tổng hợp. Thêm function này vào action group trong `infra/stacks/agent_stack.py`:

```python
bedrock.CfnAgent.FunctionProperty(
    name="list_partitions",
    description="Liệt kê các giá trị distinct cho partition key trong bảng Glue.",
    parameters={
        "database": bedrock.CfnAgent.ParameterDetailProperty(type="string", required=True, description="Tên DB Glue"),
        "table":    bedrock.CfnAgent.ParameterDetailProperty(type="string", required=True, description="Tên bảng Glue"),
        "partition_key": bedrock.CfnAgent.ParameterDetailProperty(type="string", required=True, description="Cột partition"),
    },
)
```

Thêm nhánh tương ứng trong `infra/lambda/glue_athena_tools/handler.py`:

```python
def _list_partitions(database, table, partition_key):
    parts = []
    paginator = glue.get_paginator("get_partitions")
    for page in paginator.paginate(DatabaseName=database, TableName=table):
        for p in page["Partitions"]:
            ...
    return {"distinct_values": sorted(set(parts)), "count": len(set(parts))}
```

`cdk deploy OttDataAnalystAgentStack` đưa công cụ mới lên. Mô hình tự nhận biết vì function schema action group đã thay đổi.

#### Ví dụ 3 — Đổi mô hình nền tảng

Mô hình agent có thể đổi qua CDK context — không cần sửa code:

```bash
cdk deploy OttDataAnalystAgentStack \
  -c agentModel=global.anthropic.claude-sonnet-4-5-20250929-v1:0
```

Chuyển sang Sonnet cho câu hỏi nhiều bước phức tạp; giữ Haiku 4.5 (mặc định) cho chi phí ~3x thấp hơn mỗi câu.

#### Ví dụ 4 — Trỏ vào dataset khác

Glue database cũng là context parameter:

```bash
cdk deploy OttDataAnalystAgentStack -c glueDatabase=my_other_catalog
```

Instruction.txt vẫn ghi `fpt_ott_searchevents_analytics`, nên bạn cũng cần cập nhật persona — nhưng function schema chấp nhận tên DB bất kỳ, **công cụ** chạy được mà không sửa. Đây là cách trỏ workshop sang dữ liệu account OTT khác, hoặc sang viewership data thay vì search-event data.

#### Ví dụ 5 — Thêm công cụ vẽ biểu đồ

Thắng lợi UX lớn nhất cho người không SQL là **biểu đồ**. Thêm công cụ thứ năm `render_chart(query_result_json, chart_type)` dùng `matplotlib` để render PNG vào S3 bucket có sẵn và trả về CloudFront URL. SPA đã render Markdown `![](url)`.

Đây là cùng pattern Amazon Bedrock AgentCore Code Interpreter dùng; ta làm dưới dạng Lambda thuần cho workshop.

---

**Trước:** [5.5 Tích hợp Client](../5.5-client-integration/) | **Tiếp:** [5.7 Dọn dẹp Tài nguyên](../5.7-cleanup/)
