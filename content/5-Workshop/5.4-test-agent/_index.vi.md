---
title: "Kiểm thử Tác nhân"
date: "2026-05-28"
weight: 4
chapter: false
pre: " <b> 5.4. </b> "
---

### Mục tiêu

Xác nhận tác nhân vừa **suy luận** (viết SQL Athena hợp lệ dựa trên schema trong chỉ dẫn) vừa **hành động** (gọi `athena_query`, nhận dòng dữ liệu thật, trình bày).

#### Phương án A — Bedrock console

1. Mở **Amazon Bedrock → Agents → OttDataAnalyst** ở `ap-southeast-1`.
2. Trong panel **Test** bên phải, đảm bảo alias là **live**, rồi nhập:
   > *Top 10 từ khóa tìm kiếm trong cửa sổ 14 ngày, gộp mọi thể loại. Hiện số đếm.*
3. Nhấn **Show trace**. Bạn sẽ thấy các bước điều phối: mô hình tạo lý lẽ, rồi **Action group invocation** của `athena_query` (với SQL nó tự sinh), rồi observation (các dòng trả về), rồi câu trả lời cuối.

> 💡 **Điểm nhấn:** Trace là bằng chứng đây là *tác nhân*: chú ý action `athena_query` rõ ràng nằm giữa suy nghĩ và câu trả lời. SQL được **mô hình tự viết**, không phải hardcode.

#### Phương án B — Headless invoke (CLI)

Từ `infra/`, với venv đang active:

```bash
python scripts/invoke_agent.py "Top 10 từ khóa tìm kiếm trong cửa sổ 14 ngày, gộp mọi thể loại. Hiện số đếm."
```

Script đọc `AgentId`/`AgentAliasId` từ stack outputs và gọi `bedrock-agent-runtime:InvokeAgent`. Kết quả thật (đã rút gọn):

```
Here are the **top 10 search keywords** across all genres for June 1–14, 2022:

| Rank | Keyword | Search Count |
|------|---------|--------------|
| 1 | liên minh công lý: phiên bản của zack snyder (Zack Snyder's Justice League) | 10,253 |
| 2 | fairy tail | 8,579 |
| 3 | thiên nga bóng đêm (Black Swan) | 7,183 |
| 4 | sao bằng (Shooting Star) | 6,339 |
| 5 | nữ thanh tra tài ba (Smart Investigator) | 6,276 |
| 6 | bắt ma phá án (Ghost Hunt) | 6,019 |
| 7 | running man | 5,659 |
| 8 | naruto | 5,465 |
| 9 | siêu nhân (Superhero) | 4,450 |
| 10 | yêu nhầm chị đầu (Falling In Love By Mistake) | 4,422 |

The most-searched keyword is **"Liên minh công lý: Phiên bản của Zack Snyder"** (Zack Snyder's Justice League) with 10,253 searches. The top 10 mix Vietnamese titles, anime (Fairy Tail, Naruto), and Korean/international content.

**Follow-up questions you could explore:**
- Which genres dominate these top keywords?
- How do search patterns differ by platform (mobile vs. web vs. TV)?
```

Tác nhân tự viết và thực thi SQL này phía sau:

```sql
SELECT 
  keyword_norm,
  COUNT(*) as search_count
FROM fpt_ott_searchevents_analytics.curated
WHERE dt BETWEEN '2022-06-01' AND '2022-06-14'
  AND keyword_norm IS NOT NULL
GROUP BY keyword_norm
ORDER BY search_count DESC
LIMIT 10
```

#### Kiểm tra kết quả trực tiếp trên Athena

Bạn có thể chạy chính SQL đó qua Athena console hoặc CLI và xác nhận các dòng khớp:

```bash
aws athena start-query-execution \
  --query-string "$(echo SELECT 
  keyword_norm,
  COUNT(*) as search_count
FROM fpt_ott_searchevents_analytics.curated
WHERE dt BETWEEN '2022-06-01' AND '2022-06-14'
  AND keyword_norm IS NOT NULL
GROUP BY keyword_norm
ORDER BY search_count DESC
LIMIT 10 | sed 's/"/\\"/g')" \
  --query-execution-context Database=fpt_ott_searchevents_analytics \
  --result-configuration OutputLocation=s3://ottdataanalystagentstack-resultsbucket-rcoyosyqkjgw/manual/ \
  --region ap-southeast-1
```

Rồi poll `get-query-execution` đến khi thành công và dùng `get-query-results` để lấy các dòng. Tác nhân làm trọn vòng lặp này thay bạn.

#### Đào sâu trace

Mỗi lần gọi `invoke_agent` trả về một luồng sự kiện. Với `enableTrace=True` bạn cũng nhận được:

- `orchestrationTrace.rationale.text` — lý lẽ của mô hình trước khi hành động.
- `orchestrationTrace.invocationInput.actionGroupInvocationInput` — tên công cụ + tham số (SQL).
- `orchestrationTrace.observation.actionGroupInvocationOutput.text` — JSON mà Lambda công cụ trả về.

Trong cửa sổ 14 ngày, độ trễ thường thấy là **8–25 giây** cho một câu hỏi phân tích: ~2s đọc Glue catalog, ~3-8s Athena scan, ~5-12s suy luận + viết câu trả lời.

---

**Trước:** [5.3 Triển khai Tác nhân](../5.3-deploy-agent/) | **Tiếp:** [5.5 Tích hợp Client](../5.5-client-integration/)
