---
title: "Workshop"
date: "2026-05-28"
weight: 5
chapter: false
pre: " <b> 5. </b> "
---

# Xây dựng Tác nhân Phân tích Dữ liệu AI trên Amazon Bedrock

#### Tổng quan

**Amazon Bedrock Agents** cho phép bạn xây dựng ứng dụng AI tạo sinh có thể suy luận về một tác vụ và **thực hiện hành động** bằng cách gọi API của bạn (các hàm Lambda). Trong workshop này, bạn sẽ xây dựng một **tác nhân Phân tích Dữ liệu OTT**: đặt câu hỏi bằng ngôn ngữ tự nhiên về dữ liệu sự kiện tìm kiếm của FPT Play, tác nhân sẽ tự viết SQL Presto/Trino, chạy trên **Amazon Athena**, rồi tóm tắt câu trả lời kèm bảng kết quả.

> Một *tác nhân (agent)* khác với chatbot thông thường: nó được cấp một **chỉ dẫn** (vai trò), một **mô hình nền tảng** (bộ não suy luận), và một hoặc nhiều **action group** (công cụ có thể gọi). Bedrock điều phối vòng lặp "suy nghĩ → gọi công cụ → đọc kết quả → trả lời".

Bốn thành phần tạo nên quy trình serverless này:

- **Mô hình nền tảng (Anthropic Claude Haiku 4.5)** — bộ não suy luận, diễn giải câu hỏi và viết SQL.
- **Bedrock Agent + Action Group** — bọc mô hình với chỉ dẫn và ba công cụ: `get_tables`, `get_table`, `athena_query`.
- **AWS Glue Data Catalog + Amazon Athena** — metastore và SQL engine serverless trên dữ liệu 14 ngày sự kiện tìm kiếm OTT có sẵn trong S3.
- **Phân phối serverless (Lambda Function URL + S3/CloudFront)** — cách gọi tác nhân từ trình duyệt mà không cần Docker.

Mã action group phỏng theo [aws-samples/sample-Agentic-Ai-Data-Operations](https://github.com/aws-samples/sample-Agentic-Ai-Data-Operations) (`mcp-servers/glue-athena-server/lambda_handler.py`), được rút gọn còn ba công cụ chỉ đọc cần cho Q&A.

#### Tập dữ liệu

Tác nhân truy vấn một Glue catalog có sẵn (đã được pipeline SDLF của FPT Play điền dữ liệu):

- **Database**: `fpt_ott_searchevents_analytics`
- **Bảng**: `curated` — 17 cột + partition `dt`, `derived_genre`
- **Phạm vi**: 14 ngày **2022-06-01 → 2022-06-14** (~750K sự kiện thực trong khung này)
- **Region**: `ap-southeast-1`

#### Kết quả đạt được

Kết thúc workshop bạn sẽ có:

- Một Bedrock Agent đã triển khai, biến câu hỏi ngôn ngữ tự nhiên thành truy vấn Athena.
- Một S3 bucket lưu kết quả với lifecycle xóa sau 14 ngày.
- Một web app tĩnh cho phép người không biết SQL khám phá cùng tập dữ liệu.
- Mọi thứ được định nghĩa bằng **AWS CDK (Python)** và có thể xóa bằng `cdk destroy`.

#### Nội dung

1. [Tổng quan Workshop](5.1-workshop-overview/)
2. [Chuẩn bị](5.2-prerequisite/)
3. [Triển khai Tác nhân](5.3-deploy-agent/)
4. [Kiểm thử Tác nhân](5.4-test-agent/)
5. [Tích hợp Ứng dụng Client](5.5-client-integration/)
6. [Cập nhật & Mở rộng](5.6-update-extend/)
7. [Dọn dẹp Tài nguyên](5.7-cleanup/)
