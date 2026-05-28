---
title: "Bedrock Agent là gì?"
date: "2026-05-28"
weight: 1
chapter: false
pre: " <b> 5.1.1. </b> "
---

### Amazon Bedrock Agent là gì?

Một **mô hình nền tảng (FM)** như Anthropic Claude có thể *tạo ra văn bản*, nhưng tự nó không thể *làm* gì — không thể lấy dữ liệu hay truy vấn cơ sở dữ liệu. **Amazon Bedrock Agent** lấp đầy khoảng trống đó. Nó kết hợp ba thứ:

- **Một chỉ dẫn (instruction)** — mô tả ngôn ngữ tự nhiên về vai trò (ở đây: một nhà phân tích dữ liệu OTT FPT Play, đã có sẵn schema và cửa sổ truy vấn 14 ngày).
- **Một mô hình nền tảng** — bộ máy suy luận (ở đây: Anthropic Claude Haiku 4.5 qua inference profile `global.anthropic.*`).
- **Các action group** — công cụ mà tác nhân có thể gọi. Mỗi action group trỏ tới một **hàm Lambda** và một schema mô tả thao tác cho phép mô hình gọi.

> 💡 **Điểm nhấn:** Bạn không bao giờ gọi Lambda trực tiếp. Bạn gửi câu hỏi tới tác nhân; mô hình *quyết định* gọi công cụ nào (thường `get_table` trước, rồi `athena_query`), Bedrock gọi Lambda của bạn, đưa kết quả về cho mô hình, mô hình viết câu trả lời tóm tắt.

#### Vòng lặp suy luận – hành động cho câu hỏi phân tích

```
Người dùng: "Top 10 từ khóa tìm kiếm PHIM_HAN tuần 1 tháng 6/2022?"
        │
        ▼
  Bedrock Agent (Claude Haiku 4.5)
   1. Suy nghĩ: Đã có schema trong chỉ dẫn. Có thể viết SQL ngay.
   2. Hành động: athena_query(query="SELECT keyword_norm, COUNT(*) AS n
                                    FROM fpt_ott_searchevents_analytics.curated
                                    WHERE dt BETWEEN '2022-06-01' AND '2022-06-07'
                                      AND derived_genre = 'PHIM_HAN'
                                      AND keyword_norm IS NOT NULL
                                    GROUP BY keyword_norm
                                    ORDER BY n DESC
                                    LIMIT 10",
                            database="fpt_ott_searchevents_analytics")
        │
        ▼
  Action Group Lambda  ──>  Athena.StartQueryExecution  ──>  poll  ──>  GetQueryResults
        │
        ▼
   3. Đọc kết quả công cụ: 10 dòng {keyword_norm, n}
   4. Trả lời: tường thuật + bảng Markdown + gợi ý câu hỏi tiếp
```

#### Tại sao dùng tác nhân (chứ không chỉ chatbot)?

Chatbot chỉ có thể mô tả những truy vấn *có thể*. Tác nhân của chúng ta **tạo ra một artifact** — kết quả truy vấn thực trên dữ liệu thực — bằng cách gọi công cụ. Đó là bản chất AI *agentic*: mô hình ngôn ngữ thực hiện hành động qua các API bạn kiểm soát.

Đó cũng là lý do kiến trúc này mở rộng được: thay công cụ Athena bằng công cụ DynamoDB, hoặc thêm công cụ vẽ biểu đồ, tác nhân có thêm năng lực mà không cần đổi mô hình.

#### Từ vựng quan trọng

| Thuật ngữ | Ý nghĩa |
|------|---------|
| **Instruction** | Vai trò, kiến thức schema, quy tắc phạm vi — bằng ngôn ngữ tự nhiên |
| **Action group** | Tập hợp thao tác có thể gọi, được hỗ trợ bởi Lambda + function schema |
| **Function schema** | `name`, `description`, `parameters` cho từng hàm để mô hình biết cách gọi |
| **Agent alias** | Con trỏ có phiên bản, ổn định, dùng để gọi tác nhân từ ứng dụng |
| **Orchestration** | Vòng lặp tích hợp sẵn của Bedrock quyết định khi nào gọi công cụ và khi nào trả lời |
