from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Request
from databricks.sdk.service.sql import StatementParameterListItem

from ..auth import obo_client

router = APIRouter(prefix="/api/external", tags=["external"])

CATALOG = os.environ["CAPSTONE_CATALOG"]
SCHEMA = os.environ.get("CAPSTONE_SCHEMA", "gold")
WAREHOUSE_ID = os.environ["WAREHOUSE_ID"]


@router.get("/customers/{customer_id}")
def external_get_customer(customer_id: str, request: Request):
    w = obo_client(request)

    prof = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        catalog=CATALOG,
        schema=SCHEMA,
        statement="""
            SELECT customer_id, first_name, last_name, email, phone, country, city,
                   gender, age, signup_date, last_purchase_date, segment_id,
                   lifetime_value, churn_score
            FROM customers WHERE customer_id = :cid
        """,
        parameters=[StatementParameterListItem(name="cid", value=customer_id)],
        wait_timeout="30s",
    )
    if not (prof.result and prof.result.data_array):
        raise HTTPException(status_code=404, detail="customer not found")
    pcols = [c.name for c in prof.manifest.schema.columns]
    profile = dict(zip(pcols, prof.result.data_array[0]))

    txn = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        catalog=CATALOG,
        schema=SCHEMA,
        statement="""
            SELECT transaction_id, product_id, transaction_date, channel, status, amount
            FROM transactions WHERE customer_id = :cid
            ORDER BY transaction_date DESC LIMIT 20
        """,
        parameters=[StatementParameterListItem(name="cid", value=customer_id)],
        wait_timeout="30s",
    )
    tcols = [c.name for c in txn.manifest.schema.columns]
    rows = txn.result.data_array if txn.result and txn.result.data_array else []
    transactions = [dict(zip(tcols, r)) for r in rows]

    return {"profile": profile, "transactions": transactions}
