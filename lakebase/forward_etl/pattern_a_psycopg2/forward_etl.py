# Databricks notebook source
# MAGIC %md
# MAGIC # Forward ETL (Pattern A) — Lakebase staging → Delta gold
# MAGIC
# MAGIC Reads unprocessed rows from Lakebase staging tables via psycopg (as the
# MAGIC app SP), MERGEs them into Delta gold, then marks the source rows
# MAGIC `processed = true`. Idempotent: re-running with no new rows is a no-op.

# COMMAND ----------

# MAGIC %pip install --quiet --upgrade databricks-sdk psycopg2-binary

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog", "oneenv_lakebase_capstone_catalog", "UC catalog (gold)")
dbutils.widgets.text("schema", "gold", "Gold schema")
dbutils.widgets.text("instance_name", "capstone-pg", "Lakebase instance")
dbutils.widgets.text("database_name", "capstone_db", "Postgres database")

CAT = dbutils.widgets.get("catalog")
SCH = dbutils.widgets.get("schema")
INSTANCE = dbutils.widgets.get("instance_name")
DB_NAME = dbutils.widgets.get("database_name")

# COMMAND ----------

# MAGIC %md ## 1. Ensure gold destination tables exist

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CAT}.{SCH}.customer_notes (
    note_id STRING, customer_id STRING, author_email STRING,
    note_text STRING, sentiment FLOAT, created_at TIMESTAMP
) USING DELTA
""")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CAT}.{SCH}.customer_segment_overrides (
    override_id STRING, customer_id STRING, override_segment STRING,
    reason STRING, author_email STRING, created_at TIMESTAMP
) USING DELTA
""")

# COMMAND ----------

# MAGIC %md ## 2. Connect to Lakebase as the SP

# COMMAND ----------

import psycopg2
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
ENDPOINT = f"projects/{INSTANCE}/branches/production/endpoints/primary"
host = w.postgres.get_endpoint(name=ENDPOINT).status.hosts.host
me = w.current_user.me().user_name
token = w.postgres.generate_database_credential(endpoint=ENDPOINT).token

conn = psycopg2.connect(host=host, port=5432, dbname=DB_NAME, user=me,
                        password=token, sslmode="require")
conn.autocommit = False
cur = conn.cursor()

# COMMAND ----------

# MAGIC %md ## 3. Notes: read unprocessed → MERGE → mark processed

# COMMAND ----------

cur.execute("""
    SELECT note_id::text, customer_id, author_email, note_text, sentiment, created_at
    FROM customer_notes_staging WHERE processed = false
""")
rows = cur.fetchall()

if rows:
    df = spark.createDataFrame(rows,
        ["note_id", "customer_id", "author_email", "note_text", "sentiment", "created_at"])
    df.createOrReplaceTempView("_notes_src")
    spark.sql(f"""
        MERGE INTO {CAT}.{SCH}.customer_notes t
        USING _notes_src s ON t.note_id = s.note_id
        WHEN NOT MATCHED THEN INSERT *
    """)
    ids = [r[0] for r in rows]
    cur.execute(
        "UPDATE customer_notes_staging SET processed = true, processed_at = now() "
        "WHERE note_id::text = ANY(%s)", (ids,))

print(f"notes processed: {len(rows)}")

# COMMAND ----------

# MAGIC %md ## 4. Segment overrides: read unprocessed → MERGE → mark processed

# COMMAND ----------

cur.execute("""
    SELECT override_id::text, customer_id, override_segment, reason, author_email, created_at
    FROM customer_segment_overrides_staging WHERE processed = false
""")
srows = cur.fetchall()

if srows:
    sdf = spark.createDataFrame(srows,
        ["override_id", "customer_id", "override_segment", "reason", "author_email", "created_at"])
    sdf.createOrReplaceTempView("_ovr_src")
    spark.sql(f"""
        MERGE INTO {CAT}.{SCH}.customer_segment_overrides t
        USING _ovr_src s ON t.customer_id = s.customer_id
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
    """)
    oids = [r[0] for r in srows]
    cur.execute(
        "UPDATE customer_segment_overrides_staging SET processed = true, processed_at = now() "
        "WHERE override_id::text = ANY(%s)", (oids,))

print(f"overrides processed: {len(srows)}")

# COMMAND ----------

conn.commit()
cur.close()
conn.close()

dbutils.notebook.exit(f'{{"notes": {len(rows)}, "overrides": {len(srows)}}}')
