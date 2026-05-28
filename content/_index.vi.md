---
title: "Tác nhân Phân tích Dữ liệu AI cho Sự kiện Tìm kiếm OTT"
description: "Workshop FCJ — Xây dựng Tác nhân Phân tích Dữ liệu AI trên Amazon Bedrock trả lời câu hỏi tự nhiên về 14 ngày dữ liệu sự kiện tìm kiếm OTT của FPT Play năm 2022"
---

# Tác nhân Phân tích Dữ liệu AI cho Sự kiện Tìm kiếm OTT trên Amazon Bedrock

Workshop First Cloud Journey (FCJ). Bạn sẽ xây dựng và triển khai **một tác nhân phân tích dữ liệu AI tạo sinh** trên **Amazon Bedrock**. Tác nhân cho phép stakeholder đặt câu hỏi bằng ngôn ngữ tự nhiên ("top từ khóa tuần 1 theo thể loại", "giờ nào có nhiều tìm kiếm bị bỏ dở nhất") trên một cửa sổ 14 ngày dữ liệu thực sự kiện tìm kiếm OTT FPT Play — tác nhân tự viết SQL, chạy trên Amazon Athena, và trả lời tóm tắt kèm bảng kết quả.

{{% notice info %}}
Workshop này triển khai hoàn toàn trên cloud (AWS CDK Python) và **không cần Docker**. Thời gian dự kiến: **60–90 phút**. Chi phí dự kiến nếu dọn sạch nhanh: **dưới $1**.
{{% /notice %}}

## Bạn sẽ xây dựng

- Một **Bedrock Agent** ("OttDataAnalyst") chạy trên Anthropic Claude Haiku 4.5, lập luận trên schema và viết SQL Presto/Trino.
- Một **action group** với ba công cụ chỉ đọc — `get_tables`, `get_table`, `athena_query` — phỏng theo [aws-samples/sample-Agentic-Ai-Data-Operations](https://github.com/aws-samples/sample-Agentic-Ai-Data-Operations) (`mcp-servers/glue-athena-server/`).
- Một **Lambda Function URL + SPA tĩnh** (S3 + CloudFront) để người dùng không kỹ thuật cũng có thể chat với tác nhân.
- Tất cả trỏ tới Glue catalog có sẵn `fpt_ott_searchevents_analytics.curated` (~1.15 triệu dòng curated, 17 cột + partition `dt`/`derived_genre`) tại `ap-southeast-1`.

Bắt đầu tại → [5. Workshop](5-workshop/)
