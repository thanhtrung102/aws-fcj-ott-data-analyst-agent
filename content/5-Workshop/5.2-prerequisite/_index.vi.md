---
title: "Chuẩn bị"
date: "2026-05-28"
weight: 2
chapter: false
pre: " <b> 5.2. </b> "
---

### Chuẩn bị

Bạn cần một tài khoản AWS có quyền quản trị, Glue catalog OTT có sẵn, và vài công cụ cục bộ. **Không cần Docker.**

#### 1. Pipeline dữ liệu OTT có sẵn

Workshop này *tiêu thụ* một Glue catalog đã được pipeline SDLF thượng nguồn điền dữ liệu. Trước khi bắt đầu, kiểm tra ở `ap-southeast-1`:

```bash
aws glue get-table \
  --database-name fpt_ott_searchevents_analytics \
  --name curated \
  --region ap-southeast-1 \
  --query "Table.[Name,PartitionKeys[].Name]" \
  --output text
```

Kết quả mong đợi:

```
curated
dt   derived_genre
```

Và cửa sổ 14 ngày phải tồn tại:

```bash
aws athena start-query-execution \
  --query-string "SELECT MIN(dt), MAX(dt), COUNT(DISTINCT dt) FROM fpt_ott_searchevents_analytics.curated WHERE dt BETWEEN '2022-06-01' AND '2022-06-14'" \
  --query-execution-context Database=fpt_ott_searchevents_analytics \
  --result-configuration OutputLocation=s3://aws-athena-query-results-<ACCT>-ap-southeast-1/ \
  --region ap-southeast-1
```

Kết quả phải báo ít nhất 14 ngày partition trong khoảng đó.

#### 2. Bật quyền truy cập mô hình Amazon Bedrock

Trong AWS Console, chuyển sang **`ap-southeast-1` (Singapore)**, mở **Amazon Bedrock → Model access**, yêu cầu quyền:

- **Anthropic — Claude Haiku 4.5** qua **global inference profile** `global.anthropic.claude-haiku-4-5-20251001-v1:0`.

> 💡 **Điểm nhấn:** apse1 chưa host Anthropic Claude trực tiếp. Inference profile `global.anthropic.*` **route cross-region** và là Claude duy nhất hiện hoạt động ở apse1. Marketplace agreement phải được chấp nhận một lần (`bedrock create-foundation-model-agreement` với policy `AWSMarketplaceManageSubscriptions`).

Kiểm tra:

```bash
aws bedrock get-inference-profile \
  --inference-profile-identifier global.anthropic.claude-haiku-4-5-20251001-v1:0 \
  --region ap-southeast-1 \
  --query "[inferenceProfileName,status]" --output text
```

Mong đợi: `Claude Haiku 4.5 ACTIVE`.

#### 3. Công cụ cần thiết

| Công cụ | Phiên bản tối thiểu | Kiểm tra |
|------|-----------------|-------|
| AWS CLI v2 | 2.15+ | `aws --version` |
| Node.js | 20.19+ | `node --version` |
| AWS CDK | 2.1000+ | `cdk --version` |
| Python | 3.11+ | `python --version` |
| Git | bất kỳ | `git --version` |

```bash
npm install -g aws-cdk
```

#### 4. Cấu hình thông tin xác thực

```bash
aws configure
# Access key / secret cho IAM user quản trị
# Default region name: ap-southeast-1
# Default output format: json
```

#### 5. Lấy mã nguồn và bootstrap CDK

```bash
git clone --recurse-submodules https://github.com/thanhtrung102/aws-fcj-ott-data-analyst-agent.git
cd aws-fcj-ott-data-analyst-agent/infra
python -m venv .venv
source .venv/Scripts/activate    # Windows Git Bash; macOS/Linux dùng source .venv/bin/activate
pip install -r requirements.txt
cdk bootstrap aws://<ACCOUNT_ID>/ap-southeast-1
```

> 💡 **Điểm nhấn:** `--recurse-submodules` kéo theme Hugo (~1.1 GB lịch sử). Bỏ flag nếu chỉ cần triển khai CDK. Trên Windows Git Bash, `cdk` CLI ở `~/AppData/Roaming/npm/`, có thể không có trong `PATH` bash; thêm một lần: `export PATH="$APPDATA/npm:$PATH"`.

#### 6. Lake Formation grant (bắt buộc nếu bảng curated được LF-managed)

Nếu pipeline OTT thượng nguồn dùng Lake Formation, role Lambda mới do `cdk deploy` tạo cần SELECT trên `fpt_ott_searchevents_analytics.curated`:

```bash
aws lakeformation grant-permissions \
  --principal DataLakePrincipalIdentifier=arn:aws:iam::<ACCT>:role/OttDataAnalystAgentStack-GlueAthenaToolsFnServiceRole-XXXXX \
  --resource "{\"Table\":{\"DatabaseName\":\"fpt_ott_searchevents_analytics\",\"Name\":\"curated\"}}" \
  --permissions SELECT \
  --region ap-southeast-1
```

Tên role chính xác xuất hiện trong output CDK ở 5.3.

#### Trạng thái mong đợi sau khi chuẩn bị

- `aws sts get-caller-identity` trả về tài khoản.
- Global inference profile **Claude Haiku 4.5** đã được **cấp** ở `ap-southeast-1`.
- `cdk --version` chạy được và `cdk bootstrap` đã tạo CDK toolkit ở apse1.
- `fpt_ott_searchevents_analytics.curated` truy cập được từ CLI user.

#### Xử lý sự cố — máy ít bộ nhớ

> ⚠️ `aws-cdk-lib` nặng; `cdk synth/deploy` có thể cần ~1.5 GB RAM peak. Máy có **< 2 GB RAM trống** sẽ gặp `MemoryError` hoặc Node exit 134 trong lúc synth.
>
> **Cách giải quyết:** synth một lần khi đủ bộ nhớ, rồi deploy từng stack bằng AWS CLI:
>
> ```bash
> cdk synth
> for STACK in OttDataAnalystAgentStack OttDataAnalystApiStack OttDataAnalystWebStack; do
>   aws cloudformation deploy --template-file cdk.out/$STACK.template.json \
>     --stack-name $STACK --region ap-southeast-1 \
>     --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
> done
> ```
>
> Nếu cả `cdk synth` cũng OOM: asset hash là content-addressed — sau khi upload assets lên `cdk-hnb659fds-assets-<acct>-ap-southeast-1` một lần, lần redeploy sau có thể tái sử dụng mà không cần synth lại.

---

**Tiếp theo:** [5.3 Triển khai Tác nhân](../5.3-deploy-agent/)
