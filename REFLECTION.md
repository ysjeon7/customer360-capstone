# Reflection

## English

I chose **CONTINUOUS** sync for `customers_synced` and `transactions_synced`
because both drive the primary rep-facing views (customer list, profile, and
the last-20 activity feed) where freshness matters — a segment change or a new
transaction should surface within seconds, and CONTINUOUS keeps the Lakebase
copy in near-real-time step with gold. I chose **TRIGGERED (hourly)** for
`products_synced` because the product catalog is slow-changing (name, category,
price rarely move intra-day), so a standing streaming pipeline would burn
compute for almost no delta; an hourly batch is more than fresh enough.

On optimizations, I implemented **server-side pagination** on the customer list
(page/page_size with a hard cap of 100, rejecting larger values with 422) so the
app never ships 10k rows; **client-side caching with TanStack Query** plus
`invalidateQueries` after each write so notes/segment edits reflect immediately
without over-fetching; a clear **read/write split** — sub-10ms reads from
Lakebase synced tables via the app SP, heavy cross-table aggregates from the SQL
warehouse via the caller's OBO identity; **fresh Lakebase OAuth tokens minted per
connection** to handle ~1h token expiry; and **transactional writes** that insert
the staging row and the audit-log row atomically. Given more time I would add a
**psycopg connection pool** (currently a fresh connection per request), **keyset
pagination** to replace OFFSET once the dataset grows, and a small **server-side
TTL cache** for the rarely-changing config/segments/products lookups.

## 한국어 (이해용)

**CONTINUOUS**를 `customers_synced`·`transactions_synced`에 선택한 이유는, 둘 다
담당자가 실제로 보는 핵심 화면(고객 목록·프로필·최근 20건 활동)을 구동하고 신선도가
중요하기 때문입니다. 세그먼트 변경이나 새 거래는 수 초 안에 반영돼야 하고,
CONTINUOUS가 Lakebase 복제본을 gold와 거의 실시간으로 맞춰줍니다. 반면
`products_synced`는 **TRIGGERED(시간별)** 로 했는데, 상품 카탈로그는 느리게 변하는
데이터(이름·카테고리·가격이 하루 중 거의 안 바뀜)라 상시 스트리밍 파이프라인은 변경분
없이 컴퓨트만 낭비합니다. 시간별 배치로도 충분히 신선합니다.

최적화로는 **서버 사이드 페이지네이션**(page/page_size, 상한 100 초과 시 422)을 넣어
1만 행을 한 번에 안 보내게 했고, **TanStack Query 클라이언트 캐싱** + 쓰기 후
`invalidateQueries`로 노트·세그먼트 편집이 즉시 반영되게 했습니다. **읽기/쓰기 경로
분리**(Lakebase synced를 앱 SP로 sub-10ms 읽기, 여러 테이블 집계는 SQL warehouse를
호출자 OBO 신원으로), **커넥션마다 fresh Lakebase OAuth 토큰 발급**(~1시간 만료 대응),
**staging INSERT와 audit-log INSERT를 한 트랜잭션으로 원자적 처리**도 구현했습니다.
시간이 더 있다면 **psycopg 커넥션 풀**(현재는 요청마다 새 연결), 데이터가 커지면 OFFSET을
대체할 **keyset 페이지네이션**, 거의 안 바뀌는 config/segments/products 조회용 **서버측
TTL 캐시**를 추가하겠습니다.
