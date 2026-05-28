---
title: "Cập nhật & Mở rộng"
date: "2026-05-27"
weight: 6
chapter: false
pre: " <b> 5.6. </b> "
---

### Mục tiêu

Xem tác nhân được cải tiến nhanh thế nào. Vì mọi thứ là hạ tầng dạng mã, thay đổi hành vi của tác nhân chỉ là một lần chỉnh sửa cộng một lệnh `cdk deploy`.

#### Ví dụ 1 — Đổi tính cách

Mở `infra/agent/instruction.txt` và thu hẹp tác nhân vào một thị trường ngách. Ví dụ, thêm dòng này vào yêu cầu brief:

```text
6. Sustainability - ước tính tỷ lệ vật liệu tái chế/phân hủy sinh học và cách xử lý cuối vòng đời.
```

Triển khai lại riêng agent stack:

```bash
cdk deploy ProductDesignerAgentStack --require-approval never
```

> 💡 **Điểm nhấn:** Chỉ tài nguyên `AWS::Bedrock::Agent` thay đổi; CloudFormation cập nhật tại chỗ và `auto_prepare` chuẩn bị lại tác nhân. Chạy lại bài test 5.4 và brief giờ sẽ có mục Sustainability.

#### Ví dụ 2 — Tinh chỉnh phong cách ảnh

Trong `infra/lambda/generate_image/handler.py`, đổi cấu hình mặc định cho mỗi prompt (ví dụ, ép một phong cách catalog nhất quán):

```python
body = {
    "prompt": text[:2000],
    "mode": "text-to-image",
    "aspect_ratio": "4:5",          # khung dọc kiểu catalog
    "output_format": "png",
}
```

`cdk deploy ProductDesignerAgentStack` đẩy mã Lambda mới trong vài giây.

#### Ví dụ 3 — Đổi mô hình nền tảng

Mô hình của tác nhân có thể cấu hình qua CDK context — không cần sửa mã:

```bash
cdk deploy ProductDesignerAgentStack -c agentModel=us.anthropic.claude-haiku-4-5-20251001-v1:0
```

Dùng mô hình nhỏ hơn (Haiku) cho bản nháp nhanh và rẻ; mô hình lớn hơn (Sonnet) cho brief phong phú hơn.

#### Ví dụ 4 — Thêm công cụ thứ hai

Thêm một hàm `saveDesignBrief` vào action group để ghi brief vào S3 dưới dạng Markdown, rồi cấp cho Lambda quyền `s3:PutObject`. Tác nhân sẽ bắt đầu đề nghị lưu brief khi công cụ tồn tại và chỉ dẫn có nhắc tới nó.

---

**Trước:** [5.5 Tích hợp Ứng dụng Client](../5.5-client-integration/) | **Tiếp theo:** [5.7 Dọn dẹp Tài nguyên](../5.7-cleanup/)
