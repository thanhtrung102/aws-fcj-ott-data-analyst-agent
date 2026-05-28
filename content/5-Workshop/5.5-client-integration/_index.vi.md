---
title: "Tích hợp Ứng dụng Client"
date: "2026-05-28"
weight: 5
chapter: false
pre: " <b> 5.5. </b> "
---

### Mục tiêu

Đặt giao diện trình duyệt phía trước tác nhân để analyst và PM không biết SQL cũng đặt được câu hỏi. Web app **không giữ AWS credentials** — nó gọi một endpoint serverless để tác nhân được gọi thay.

#### Tại sao dùng Lambda Function URL (không phải API Gateway)?

> 💡 **Điểm nhấn:** Vòng lặp suy luận + chạy Athena của tác nhân thường mất **15–30 giây** ở cold path và có thể vượt 60s khi scan nhiều partition. Amazon API Gateway có integration timeout **cứng 30 giây**, gọi đồng bộ qua đó sẽ 503 giữa truy vấn. **Lambda Function URL** không có giới hạn này — nó tôn trọng timeout của chính Lambda (đặt 120s). Đó là lý do `OttDataAnalystApiStack` dùng Function URL.

#### 1. Triển khai API và Web stacks

```bash
cd infra
source .venv/Scripts/activate
cdk deploy OttDataAnalystApiStack OttDataAnalystWebStack --require-approval never
```

Outputs:

```
OttDataAnalystApiStack.ApiUrl = https://6xfis6ttruifkbaxtemu3evwde0bkfyc.lambda-url.ap-southeast-1.on.aws/
OttDataAnalystWebStack.WebUrl = https://d31ailu10g1wh5.cloudfront.net
```

#### 2. Smoke-test API

```bash
curl -s -X POST "https://6xfis6ttruifkbaxtemu3evwde0bkfyc.lambda-url.ap-southeast-1.on.aws/" \
  -H "content-type: application/json" \
  -d '{"prompt":"Top 10 từ khóa tìm kiếm trong cửa sổ 14 ngày, gộp mọi thể loại. Hiện số đếm."}' \
  --max-time 120 | python -m json.tool
```

Phản hồi là JSON với trường `answer` chứa tóm tắt + bảng Markdown, và `sessionId` để truyền vào lượt sau giữ ngữ cảnh hội thoại.

> ✅ **Đã kiểm chứng end-to-end:** `curl` vào Function URL trả **HTTP 200 trong 8.96s** với câu trả lời analyst đầy đủ và các dòng Athena — qua rào 30s của API Gateway cũ.

#### 3. Dùng web app

Mở `WebUrl` trong trình duyệt, gõ câu hỏi, nhấn **Ask**. Sau ~15-30s bạn nhận được tóm tắt, bảng kết quả, và 1-2 gợi ý câu hỏi tiếp.

Các câu hỏi mẫu trong SPA:

- *Top 10 từ khóa tìm kiếm trong cửa sổ 14 ngày*
- *Tỷ trọng thể loại khác biệt thế nào giữa mobile và TV?*
- *Ngày nào có nhiều tìm kiếm bị bỏ dở nhất và tại sao?*
- *Liệt kê top UNKNOWN keywords theo tần suất*
- *Giờ nào trong ngày có lượng tìm kiếm cao nhất?*

#### Luồng request

```
Browser ──fetch POST──> Lambda Function URL ──InvokeAgent──> Bedrock Agent
                                                                  │
                                              (action group → Glue/Athena → result rows)
                                                                  │
Browser <──── JSON {answer, sessionId} ◄──────────────────────────┘
Static: Browser ──> CloudFront ──> S3 (index.html, app.js, config.js)
```

`config.js` được sinh ở deploy time với Function URL qua `BucketDeployment(Source.data(...))`; `app.js` đọc `window.API_URL` và POST tới đó.

> ⚠️ **Lưu ý bảo mật:** Function URL dùng `AuthType: NONE` và CORS rộng cho workshop đơn giản. Production cần Cognito (hoặc IAM auth) và CORS hạn chế theo domain. Role Lambda chỉ được cấp `bedrock:InvokeAgent` trên alias ARN cụ thể, nên kể cả gọi lạc cũng không gọi được agent khác.

---

**Trước:** [5.4 Kiểm thử Tác nhân](../5.4-test-agent/) | **Tiếp:** [5.6 Cập nhật & Mở rộng](../5.6-update-extend/)
