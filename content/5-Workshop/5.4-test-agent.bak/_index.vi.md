---
title: "Kiểm thử Tác nhân"
date: "2026-05-27"
weight: 4
chapter: false
pre: " <b> 5.4. </b> "
---

### Mục tiêu

Xác nhận tác nhân vừa **suy luận** (viết bản brief thiết kế) vừa **hành động** (gọi công cụ tạo ảnh và trả về URL mockup thật).

#### Cách A — Cửa sổ Test trong Bedrock console

1. Mở **Amazon Bedrock → Agents → ProductDesigner** ở `us-west-2`.
2. Trong bảng **Test** bên phải, đảm bảo alias là **live**, rồi nhập:
   > *Design a reusable bamboo water bottle for Vietnamese university students.*
3. Bấm **Show trace**. Bạn sẽ thấy các bước điều phối: mô hình tạo lý luận, rồi một **Action group invocation** gọi `generateProductImage`, rồi observation của công cụ (URL ảnh), rồi câu trả lời cuối cùng.

> 💡 **Điểm nhấn:** Trace chính là bằng chứng đây là một *tác nhân*: hãy chú ý action `generateProductImage` rõ ràng nằm giữa phần suy nghĩ và câu trả lời cuối của mô hình.

#### Cách B — Gọi headless (CLI)

Từ thư mục `infra/`, với virtual environment đang kích hoạt:

```bash
python scripts/invoke_agent.py "Design a reusable bamboo water bottle for Vietnamese university students."
```

Script đọc `AgentId`/`AgentAliasId` từ output của stack và gọi `bedrock-agent-runtime:InvokeAgent`. Kết quả thật (rút gọn):

```markdown
## 3. Key Features
1. 🌿 Natural Bamboo Outer Shell — tre Việt Nam khai thác bền vững ...
2. 🧊 Double-Wall Vacuum Insulation — lạnh 12h / nóng 6h ...
...
## 5. Accessibility
- ♿ One-Hand Operable Lid: nắp vặn cần xoay < 90°, lực thấp ...

## 🖼️ Product Mockup
![Bamboo Water Bottle Mockup](https://d2vtwrtxd9y2gt.cloudfront.net/images/b0dd62...png)
```

URL trả về là một đối tượng thật mà tác nhân vừa tạo:

![Mockup mẫu được tạo ra](/images/5-Workshop/sample-mockup.png)

*Tác nhân đã viết brief, rồi tạo mockup này qua Stability Stable Image — lưu ý nó khớp với brief (thân tre, nắp xanh rừng, họa tiết khắc).*

#### Kiểm tra ảnh đã vào S3

```bash
aws s3 ls s3://<ImagesBucketName>/images/ --region us-west-2
```

Kết quả mong đợi:

```
2026-05-27 23:16:36    2152732 b0dd62052d4c4c148eb6ae7019b8db72.png
```

Mở URL CloudFront (`https://<ImagesDistributionDomain>/images/<key>.png`) trả về ảnh PNG với HTTP 200.

---

**Trước:** [5.3 Triển khai Tác nhân](../5.3-deploy-agent/) | **Tiếp theo:** [5.5 Tích hợp Ứng dụng Client](../5.5-client-integration/)
