# Capstone Submission — Customer 360 on Databricks Apps + Lakebase

## Links

- **Repo:** https://github.com/ysjeon7/customer360-capstone (public)
- **Live app:** https://customer360-7474651289964952.aws.databricksapps.com
  (deployed as a **git-source app** via `databricks bundle deploy` + `bundle run`)
- **Demo recording:** [`demo/capstone-demo.mp4`](./demo/capstone-demo.mp4)
  (customer list → detail all tabs → add note → override segment → genie →
  dashboard → run forward-ETL)

## Task completion (T1–T9)

| Task | What | Status |
|---|---|---|
| T1 | Reverse ETL: 3 synced tables (customers/transactions CONTINUOUS, products TRIGGERED) + 3 staging tables | ✅ |
| T2 | Auth: `obo_client` (SQL/Genie) + `sp_client` (Lakebase/jobs); no `lakebase_obo` (OBO unsupported) | ✅ |
| T3 | 5 API endpoints + React list/detail; server-side pagination; transactional audited writes | ✅ |
| T3a | External M2M API — SP client_credentials → gold via warehouse OBO (never Lakebase) | ✅ |
| T4 | AI/BI dashboard embed (`/api/config` + iframe) | ✅ |
| T5 | Genie chat — floating widget, 3 OBO endpoints, poll loop | ✅ |
| T6 | `app.yaml` — env wiring + `user_authorization: [sql, dashboards.genie]` | ✅ |
| T7 | Forward ETL (Pattern A): psycopg + MERGE INTO gold, idempotent via `processed` flag | ✅ |
| T8 | DABs git-source app: `databricks.yml` + `resources/{app,jobs,lakebase}.yml` | ✅ |
| T9a | Branch + PITR (screenshots) | ✅ |
| T9b | Query insights: index on `customer_audit_log(actor_email)` | ✅ |

## T3a — M2M output

See [`examples/m2m_test_output.txt`](./examples/m2m_test_output.txt) —
`GET /api/external/customers/{id}` returns **200** + customer JSON via the
service-principal OAuth `client_credentials` flow (bearer minted against
`/oidc/v1/token`, forwarded by the Apps proxy, warehouse query attributed to the
SP).

## T9 evidence

- **T9a — Branch + PITR:** created child branch `pitr-test`, ran
  `DELETE FROM customer_notes_staging` on the branch, restored via PITR (Lakebase
  restore creates a new branch at the chosen timestamp), confirmed restored row
  count. (Screenshots attached separately.)
- **T9b — Query insights** (`customer_audit_log`, 50k rows, 100 runs of
  `WHERE actor_email = …`):

  | | Plan | p50 | **p95** | max |
  |---|---|---|---|---|
  | Before index | Seq Scan | 3.42 ms | **9.79 ms** | 13.87 ms |
  | After `CREATE INDEX … (actor_email)` | Bitmap Index Scan | 0.04 ms | **0.16 ms** | 2.67 ms |

  → **~61× p95 improvement.**

## Reflection

See [`REFLECTION.md`](./REFLECTION.md) — sync-mode rationale per synced table
and the optimizations implemented (server-side pagination, TanStack Query
caching, read/write split, per-connection token minting, transactional writes)
plus what I'd add next (connection pool, keyset pagination, server-side TTL cache).
