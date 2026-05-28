---
title: "Dọn dẹp Tài nguyên"
date: "2026-05-28"
weight: 7
chapter: false
pre: " <b> 5.7. </b> "
---

### Mục tiêu

Xóa mọi thứ bạn đã tạo để không phát sinh chi phí. Bản thân Bedrock tính theo lượt dùng (không có gì để xóa), nhưng S3 (kết quả Athena + web SPA), CloudFront, Lambda và tác nhân sẽ được CDK gỡ bỏ. **Pipeline dữ liệu OTT thượng nguồn không bị động đến** — chỉ ba stack của workshop bị gỡ.

> ✅ **Đã kiểm chứng đầy đủ:** Ba stack được xóa theo thứ tự (Web → Api → Agent) và đều đạt `DELETE_COMPLETE`. Các S3 bucket được tự làm trống bởi `auto_delete_objects`, không cần dọn dẹp thủ công.

#### Các bước (theo thứ tự)

1. **Hủy toàn bộ stack (CDK):**
   ```bash
   cd infra
   cdk destroy --all --force
   ```
   Lệnh này gỡ Web → Api → Agent theo thứ tự dependency ngược.

2. **Phương án ít bộ nhớ** (nếu `cdk destroy` OOM):
   ```bash
   for STACK in OttDataAnalystWebStack OttDataAnalystApiStack OttDataAnalystAgentStack; do
     aws cloudformation delete-stack --stack-name $STACK --region ap-southeast-1
     aws cloudformation wait stack-delete-complete --stack-name $STACK --region ap-southeast-1
   done
   ```

3. **Kiểm tra** trong CloudFormation console rằng mọi stack `OttDataAnalyst*` đã biến mất:
   ```bash
   aws cloudformation list-stacks --region ap-southeast-1 \
     --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
     --query "StackSummaries[?starts_with(StackName,'OttDataAnalyst')].StackName" \
     --output text
   ```

4. (Tùy chọn) Revoke Lake Formation grant ở 5.2 #6 nếu không còn cần:
   ```bash
   aws lakeformation revoke-permissions \
     --principal DataLakePrincipalIdentifier=<ROLE_ARN_TỪ_5.2> \
     --resource "{\"Table\":{\"DatabaseName\":\"fpt_ott_searchevents_analytics\",\"Name\":\"curated\"}}" \
     --permissions SELECT --region ap-southeast-1
   ```

5. (Tùy chọn) Tắt quyền truy cập mô hình Bedrock nếu không còn cần.

#### Danh sách kiểm tra dọn dẹp

- [ ] S3 bucket kết quả Athena đã trống và bị xóa
- [ ] S3 bucket web đã trống và bị xóa
- [ ] CloudFront distribution web đã bị xóa
- [ ] Bedrock Agent + alias đã bị xóa
- [ ] Ba hàm Lambda + IAM role đã bị xóa (`GlueAthenaToolsFn`, `InvokeAgentFn`, hai Lambda custom-resource)
- [ ] Không còn stack `OttDataAnalyst*` trong CloudFormation
- [ ] `fpt_ott_searchevents_analytics.curated` thượng nguồn **vẫn khỏe mạnh** (kiểm tra bằng cách mở lại dashboard tại CloudFront URL SDLF)

#### Những thứ KHÔNG bị dọn dẹp (cố ý)

Workshop **không bao giờ ghi vào S3 bucket raw hay curated của OTT**, **không sửa Glue catalog**, **không gọi Lambda hay Step Functions của pipeline thượng nguồn**. Sau khi dọn dẹp, data lake OTT vẫn nguyên trạng như khi bạn bắt đầu.

---

**Trước:** [5.6 Cập nhật & Mở rộng](../5.6-update-extend/)
