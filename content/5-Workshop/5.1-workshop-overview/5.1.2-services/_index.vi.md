---
title: "Các dịch vụ sử dụng"
date: "2026-05-28"
weight: 2
chapter: false
pre: " <b> 5.1.2. </b> "
---

### Các dịch vụ sử dụng

| Dịch vụ | Lý do sử dụng | Mô hình chi phí |
|---------|----------------|-----------|
| **Amazon Bedrock — Agents** | Lưu trữ tác nhân OTT Data Analyst và điều phối vòng lặp suy luận–hành động | Theo lượt gọi tác nhân (tính như token mô hình) |
| **Amazon Bedrock — Anthropic Claude Haiku 4.5** (`global.anthropic.claude-haiku-4-5-20251001-v1:0`) | Mô hình suy luận viết SQL và tóm tắt kết quả | Theo token vào/ra (~$0.0008/1k input, ~$0.004/1k output) |
| **AWS Glue Data Catalog** | Metadata cho các bảng OTT có sẵn; cung cấp công cụ `get_tables`/`get_table` | Miễn phí (trong giới hạn API hợp lý) |
| **Amazon Athena** | Presto/Trino serverless trên S3; thực thi SQL mà tác nhân viết | **$5 mỗi TB scan** — truy vấn workshop scan KB đến MB, tốn < $0.01 |
| **AWS Lambda** | Chạy các công cụ action group (`get_tables`, `get_table`, `athena_query`) và API công khai `invoke_agent` | Theo request + thời lượng (thân thiện free-tier) |
| **Amazon S3** | Lưu kết quả Athena (lifecycle 14 ngày) và web app tĩnh | Theo GB + request (vài xu) |
| **Amazon CloudFront** | CDN phục vụ web app qua HTTPS | Theo GB truyền tải (gần như $0 khi idle) |
| **AWS IAM** | Vai trò đặc quyền tối thiểu cho tác nhân và Lambda | Miễn phí |
| **AWS Lake Formation** | Cần cho Lambda action group đọc các bảng OTT (LF-managed) | Miễn phí |
| **AWS CDK (Python)** | Hạ tầng dạng mã — một lệnh để triển khai và xóa | Miễn phí (dùng CloudFormation) |

#### Lưu ý về Region

> 💡 **Điểm nhấn:** Workshop này triển khai tại **`ap-southeast-1` (Singapore)**. Đây là nơi pipeline SDLF thượng nguồn của FPT Play (và Glue catalog `fpt_ott_searchevents_analytics`) đã hoạt động. Anthropic Claude Haiku 4.5 có sẵn ở đây qua **global inference profile** `global.anthropic.claude-haiku-4-5-20251001-v1:0` — profile Claude duy nhất hiện route được tới apse1, nên ta dùng nó.

#### Những thứ bạn KHÔNG cần

- **Không cần Docker.** Mọi Lambda được đóng gói dưới dạng ZIP thuần (dependency runtime duy nhất là `boto3`, có sẵn trong Lambda runtime).
- **Không cần quản lý máy chủ.** Mọi thành phần đều serverless hoặc fully managed.
- **Không cần vector database / knowledge base.** Schema `curated` 17 cột đủ nhỏ để inline vào chỉ dẫn của tác nhân; không cần RAG.
- **Không cần data pipeline mới.** Workshop *tiêu thụ* bảng `curated` có sẵn; không xây lại pipeline.
