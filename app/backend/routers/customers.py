from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from ..auth import obo_client, sp_client
from ..db import lakebase_sp

router = APIRouter(prefix="/api/customers", tags=["customers"])

CATALOG = os.environ["CAPSTONE_CATALOG"]
SCHEMA = os.environ.get("CAPSTONE_SCHEMA", "gold")
WAREHOUSE_ID = os.environ["WAREHOUSE_ID"]

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100


class NoteIn(BaseModel):
    note_text: str


class SegmentIn(BaseModel):
    override_segment: str
    reason: str | None = None


@router.get("")
def list_customers(
    segment: str | None = None,
    min_ltv: float | None = None,
    max_churn: float | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1),
):
    if page_size > MAX_PAGE_SIZE:
        raise HTTPException(status_code=422, detail=f"page_size exceeds {MAX_PAGE_SIZE}")

    where = []
    params: list = []
    if segment:
        where.append("segment_id = %s")
        params.append(segment)
    if min_ltv is not None:
        where.append("lifetime_value >= %s")
        params.append(min_ltv)
    if max_churn is not None:
        where.append("churn_score <= %s")
        params.append(max_churn)
    clause = ("WHERE " + " AND ".join(where)) if where else ""
    offset = (page - 1) * page_size

    with lakebase_sp() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM customers_synced {clause}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""SELECT customer_id, first_name, last_name, email, country, city,
                       segment_id, lifetime_value, churn_score
                FROM customers_synced {clause}
                ORDER BY lifetime_value DESC
                LIMIT %s OFFSET %s""",
            params + [page_size, offset],
        )
        cols = [d[0] for d in cur.description]
        items = [dict(zip(cols, row)) for row in cur.fetchall()]

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{customer_id}")
def get_customer(customer_id: str):
    with lakebase_sp() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT customer_id, first_name, last_name, email, phone, country, city,
                      gender, age, signup_date, last_purchase_date, segment_id,
                      lifetime_value, churn_score
               FROM customers_synced WHERE customer_id = %s""",
            [customer_id],
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="customer not found")
        cols = [d[0] for d in cur.description]
        profile = dict(zip(cols, row))

        cur.execute(
            """SELECT transaction_id, product_id, transaction_date, channel, status, amount
               FROM transactions_synced WHERE customer_id = %s
               ORDER BY transaction_date DESC LIMIT 20""",
            [customer_id],
        )
        tcols = [d[0] for d in cur.description]
        transactions = [dict(zip(tcols, r)) for r in cur.fetchall()]

    return {"profile": profile, "transactions": transactions}


@router.get("/{customer_id}/metrics")
def get_metrics(customer_id: str, request: Request):
    w = obo_client(request)

    stmt = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        catalog=CATALOG,
        schema=SCHEMA,
        statement="""
            SELECT
              (SELECT COALESCE(sum(amount), 0) FROM transactions
                 WHERE customer_id = :cid AND status = 'completed') AS lifetime_spend,
              (SELECT COALESCE(sum(amount), 0) FROM transactions
                 WHERE customer_id = :cid AND status = 'completed'
                   AND transaction_date >= current_date() - INTERVAL 30 DAYS) AS spend_30d,
              (SELECT COALESCE(sum(amount), 0) FROM transactions
                 WHERE customer_id = :cid AND status = 'completed'
                   AND transaction_date >= current_date() - INTERVAL 90 DAYS) AS spend_90d,
              (SELECT count(*) FROM support_tickets
                 WHERE customer_id = :cid AND status <> 'closed') AS open_tickets,
              (SELECT avg(csat_score) FROM support_tickets
                 WHERE customer_id = :cid) AS avg_csat
        """,
        parameters=[{"name": "cid", "value": customer_id}],
        wait_timeout="30s",
    )
    row = stmt.result.data_array[0] if stmt.result and stmt.result.data_array else []
    scalar_cols = ["lifetime_spend", "spend_30d", "spend_90d", "open_tickets", "avg_csat"]
    metrics = dict(zip(scalar_cols, row))

    top = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        catalog=CATALOG,
        schema=SCHEMA,
        statement="""
            SELECT p.category, sum(t.amount) AS spend
            FROM transactions t JOIN products p ON t.product_id = p.product_id
            WHERE t.customer_id = :cid AND t.status = 'completed'
            GROUP BY p.category ORDER BY spend DESC LIMIT 5
        """,
        parameters=[{"name": "cid", "value": customer_id}],
        wait_timeout="30s",
    )
    rows = top.result.data_array if top.result and top.result.data_array else []
    metrics["top_categories"] = [{"category": r[0], "spend": r[1]} for r in rows]

    return metrics


@router.post("/{customer_id}/notes")
def add_note(customer_id: str, body: NoteIn, request: Request):
    actor = request.headers.get("X-Forwarded-Email") or "unknown"
    with lakebase_sp() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO customer_notes_staging (customer_id, author_email, note_text)
               VALUES (%s, %s, %s) RETURNING note_id""",
            [customer_id, actor, body.note_text],
        )
        note_id = cur.fetchone()[0]
        cur.execute(
            """INSERT INTO customer_audit_log (customer_id, action, actor_email, payload)
               VALUES (%s, %s, %s, %s)""",
            [customer_id, "add_note", actor, f'{{"note_id": "{note_id}"}}'],
        )
        conn.commit()
    return {"note_id": str(note_id)}


@router.post("/{customer_id}/segment")
def override_segment(customer_id: str, body: SegmentIn, request: Request):
    actor = request.headers.get("X-Forwarded-Email") or "unknown"
    with lakebase_sp() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO customer_segment_overrides_staging
                   (customer_id, override_segment, reason, author_email)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (customer_id) DO UPDATE
                   SET override_segment = EXCLUDED.override_segment,
                       reason = EXCLUDED.reason,
                       author_email = EXCLUDED.author_email,
                       created_at = now(),
                       processed = false""",
            [customer_id, body.override_segment, body.reason, actor],
        )
        cur.execute(
            """INSERT INTO customer_audit_log (customer_id, action, actor_email, payload)
               VALUES (%s, %s, %s, %s)""",
            [customer_id, "override_segment", actor, f'{{"segment": "{body.override_segment}"}}'],
        )
        conn.commit()
    return {"customer_id": customer_id, "override_segment": body.override_segment}
