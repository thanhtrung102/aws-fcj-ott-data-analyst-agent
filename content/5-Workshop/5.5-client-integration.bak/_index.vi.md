---
title: "Tích hợp Ứng dụng Client"
date: "2026-05-27"
weight: 5
chapter: false
pre: " <b> 5.5. </b> "
---

### Mục tiêu

Đặt một giao diện trình duyệt trước tác nhân. Web app **không giữ thông tin xác thực AWS** — nó gọi một endpoint serverless, và endpoint này gọi tác nhân thay cho nó.

#### Tại sao dùng Lambda Function URL (không phải API Gateway)?

> 💡 **Điểm nhấn:** Vòng lặp suy luận-rồi-tạo-ảnh của tác nhân mất **~35–45 giây**. Amazon API Gateway có giới hạn timeout tích hợp **cứng 30 giây**, nên một lời gọi đồng bộ qua nó sẽ trả về `503` trước khi ảnh kịp tạo xong. Một **Lambda Function URL** không có giới hạn đó — nó tuân theo timeout của chính Lambda (chúng ta đặt 120s). Đó là lý do `ProductDesignerApiStack` dùng Function URL.

#### 1. Triển khai API và web stack

```bash
cd infra
source .venv/Scripts/activate
cdk deploy ProductDesignerApiStack ProductDesignerWebStack --require-approval never
```

Output:

```
ProductDesignerApiStack.ApiUrl = https://<id>.lambda-url.us-west-2.on.aws/
ProductDesignerWebStack.WebUrl = https://<dist>.cloudfront.net
```

#### 2. Kiểm thử nhanh API

```bash
curl -s -X POST "<ApiUrl>" \
  -H "content-type: application/json" \
  -d '{"prompt":"Design a compact foldable solar phone charger for street vendors"}' \
  --max-time 120 | python -m json.tool
```

Phản hồi là JSON với trường `answer` chứa bản brief thiết kế và một liên kết ảnh Markdown tới mockup được tạo, cùng một `sessionId`.

#### 3. Dùng web app

Mở `WebUrl` trong trình duyệt, nhập một ý tưởng sản phẩm, và bấm **Design it**. Sau ~30–45s bạn nhận được brief và mockup được tạo, hiển thị ngay trong trang.

> ✅ **Kiểm chứng end-to-end:** Lệnh `curl` tới Function URL trả về **HTTP 200 sau 30.5s** với bản brief đầy đủ (concept → 6 tính năng → bảng vật liệu → accessibility) và URL mockup được tạo trên CloudFront ảnh — vượt qua giới hạn 30s cũ của API Gateway, với lời gọi công cụ của tác nhân hoàn tất trong cùng một request.

#### Luồng request

```
Trình duyệt ──fetch POST──> Lambda Function URL ──InvokeAgent──> Bedrock Agent
                                                                     │
                                                       (action group → Stability → S3)
                                                                     │
Trình duyệt <──── JSON {answer, sessionId} ◄─────────────────────────┘
Tài nguyên tĩnh: Trình duyệt ──> CloudFront ──> S3 (index.html, app.js, config.js)
```

`config.js` (tệp duy nhất phụ thuộc môi trường) được sinh ra lúc triển khai với Function URL, nên cùng một bộ tài nguyên tĩnh hoạt động cho mọi lần triển khai.

> ⚠️ **Lưu ý bảo mật:** Để đơn giản cho workshop, Function URL dùng `AuthType: NONE` và CORS mở. Với môi trường production, hãy đặt endpoint sau Amazon Cognito (hoặc IAM auth) và giới hạn CORS theo domain của bạn.

---

**Trước:** [5.4 Kiểm thử Tác nhân](../5.4-test-agent/) | **Tiếp theo:** [5.6 Cập nhật & Mở rộng](../5.6-update-extend/)
