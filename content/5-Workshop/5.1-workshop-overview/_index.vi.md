---
title: "Tổng quan Workshop"
date: "2026-05-28"
weight: 1
chapter: false
pre: " <b> 5.1. </b> "
---

### Tổng quan

Trong workshop này, bạn sẽ xây dựng một **tác nhân Phân tích Dữ liệu AI** cho FPT Play OTT — trợ lý AI tạo sinh nhận một câu hỏi ngôn ngữ tự nhiên và trả về:

1. Một câu trả lời tường thuật ngắn (2–4 câu) tóm tắt phát hiện.
2. **Bảng kết quả Athena** kèm theo (top 10 dòng đầu của truy vấn SQL thực).
3. Một hoặc hai gợi ý **câu hỏi tiếp theo** mà người dùng có thể đặt.

Tác nhân hoàn toàn **serverless** và **có thể tái tạo**: được định nghĩa bằng AWS CDK, triển khai bằng một lệnh, và gỡ bỏ bằng một lệnh.

> 💡 **Điểm nhấn:** Tác nhân không chỉ *nói* về dữ liệu — nó **hành động**, viết SQL Presto/Trino và thực thi trên Amazon Athena. Vòng lặp "suy luận + hành động + đọc + trả lời" chính là điều biến nó thành *tác nhân* chứ không phải chatbot.

#### Kiến trúc tổng quát

| Tầng | Dịch vụ | Vai trò |
|-------|---------|------|
| Suy luận | Anthropic Claude Haiku 4.5 trên Amazon Bedrock | Diễn giải câu hỏi và viết SQL |
| Điều phối | Amazon Bedrock Agent + Action Group | Bọc mô hình với chỉ dẫn và ba công cụ |
| Catalog | AWS Glue Data Catalog | Metadata cho bảng `curated` có sẵn |
| SQL engine | Amazon Athena | Presto/Trino serverless trên S3 |
| Lưu trữ | Amazon S3 (kết quả Athena, lifecycle 14 ngày) | Cache kết quả truy vấn |
| API | AWS Lambda + Lambda Function URL | Tầng mỏng, không Docker, gọi tác nhân |
| Giao diện | Web app tĩnh trên S3 + CloudFront | Giao diện trình duyệt trò chuyện với tác nhân |

#### Tập dữ liệu phân tích

Tác nhân trỏ tới một Glue catalog có sẵn đã được pipeline SDLF thượng nguồn điền dữ liệu:

| | |
|---|---|
| Database | `fpt_ott_searchevents_analytics` |
| Bảng | `curated` |
| Partition | `dt` (YYYY-MM-DD), `derived_genre` |
| Số dòng | ~1.15 triệu dòng curated |
| Phạm vi workshop | **2022-06-01 → 2022-06-14** (14 ngày) |
| Mã thể loại | `PHIM_TRUNG`, `PHIM_VIET`, `PHIM_HAN`, `PHIM_AU_MY`, `ANIME`, `THE_THAO`, `NHAC`, `TRUYEN_HINH`, `UNKNOWN` |

#### Các bước thực hiện

1. [Bedrock Agent là gì?](5.1.1-what-is-a-bedrock-agent/)
2. [Các dịch vụ sử dụng](5.1.2-services/)
