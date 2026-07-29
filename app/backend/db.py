from __future__ import annotations

import os
import uuid

import psycopg

from .auth import sp_client

PGHOST = os.environ["PGHOST"]
PGDATABASE = os.environ.get("PGDATABASE", "capstone_db")
PGPORT = int(os.environ.get("PGPORT", "5432"))
PG_INSTANCE_NAME = os.environ["PG_INSTANCE_NAME"]


def lakebase_sp() -> psycopg.Connection:
    w = sp_client()
    cred = w.database.generate_database_credential(
        request_id=str(uuid.uuid4()),
        instance_names=[PG_INSTANCE_NAME],
    )
    return psycopg.connect(
        host=PGHOST,
        port=PGPORT,
        dbname=PGDATABASE,
        user=w.current_user.me().user_name,
        password=cred.token,
        sslmode="require",
    )
