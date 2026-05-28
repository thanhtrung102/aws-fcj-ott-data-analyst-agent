---
title: "Triển khai Tác nhân"
date: "2026-05-27"
weight: 3
chapter: false
pre: " <b> 5.3. </b> "
---

### Mục tiêu

Triển khai Bedrock Agent, action group `generateProductImage`, S3 bucket ảnh, và một CloudFront distribution — tất cả chỉ với một lệnh `cdk deploy`.

#### 1. Xem định nghĩa tác nhân

Hai tệp định nghĩa hành vi của tác nhân:

- `infra/agent/instruction.txt` — **tính cách (persona)**. Nó yêu cầu Claude tạo một bản brief thiết kế 5 phần rồi gọi công cụ tạo ảnh đúng một lần.
- **Action group** được khai báo trong `infra/stacks/agent_stack.py` dưới dạng *function schema* với một hàm:

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

Khi mô hình gọi hàm này, Bedrock sẽ gọi `infra/lambda/generate_image/handler.py`, hàm này gọi Stability Stable Image và lưu ảnh PNG vào S3.

> 💡 **Điểm nhấn:** Mô hình nền tảng của tác nhân là một **cross-region inference profile** (`us.anthropic.claude-sonnet-4-6`). IAM role của tác nhân được cấp `bedrock:InvokeModel` trên cả foundation model lẫn inference profile để profile có thể định tuyến qua nhiều region.

#### 2. Triển khai

```bash
cd infra
source .venv/Scripts/activate      # .venv/bin/activate trên macOS/Linux
cdk deploy ProductDesignerAgentStack --require-approval never
```

Kết quả mong đợi (≈ 5 phút — CloudFront là phần chậm nhất):

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

ID của bạn sẽ khác — hãy ghi lại `AgentId` và `AgentAliasId`.

#### 3. Những gì đã được tạo

| Tài nguyên | Mục đích |
|----------|---------|
| `AWS::Bedrock::Agent` (`ProductDesigner`) | Tác nhân: chỉ dẫn + Claude + action group |
| `AWS::Bedrock::AgentAlias` (`live`) | Con trỏ ổn định, có phiên bản, dùng để gọi tác nhân |
| `AWS::Lambda::Function` (`GenerateImageFn`) | Công cụ action-group: gọi Stability, ghi PNG vào S3 |
| `AWS::S3::Bucket` (ảnh) | Lưu các mockup được tạo (riêng tư; phục vụ qua CloudFront) |
| `AWS::CloudFront::Distribution` | Phục vụ ảnh qua HTTPS |
| `AWS::IAM::Role` (agent + Lambda) | Các role đặc quyền tối thiểu |

#### Kiểm tra

```bash
aws cloudformation describe-stacks --stack-name ProductDesignerAgentStack \
  --region us-west-2 --query "Stacks[0].Outputs[].[OutputKey,OutputValue]" --output table
```

Bạn sẽ thấy bốn output bao gồm `AgentId` và `AgentAliasId` hợp lệ.

---

**Trước:** [5.2 Chuẩn bị](../5.2-prerequisite/) | **Tiếp theo:** [5.4 Kiểm thử Tác nhân](../5.4-test-agent/)
