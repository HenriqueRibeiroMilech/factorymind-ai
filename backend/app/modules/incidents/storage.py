import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from flask import current_app

from app.errors import AppError


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connection():
    db = sqlite3.connect(current_app.config["DATABASE_PATH"], timeout=10)
    db.row_factory = sqlite3.Row
    try:
        with db:
            yield db
    finally:
        db.close()


def init_db():
    Path(current_app.config["DATABASE_PATH"]).parent.mkdir(parents=True, exist_ok=True)
    with connection() as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("""CREATE TABLE IF NOT EXISTS incidents (
            id TEXT PRIMARY KEY, request_id TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL, reference TEXT NOT NULL,
            relevant_risk INTEGER NOT NULL, complement TEXT NOT NULL DEFAULT '',
            measurements TEXT, suggested_category TEXT, confidence REAL, jev_model TEXT,
            category TEXT, review TEXT, status TEXT NOT NULL,
            report TEXT, last_error TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            operation_id TEXT, processing_since TEXT
        )""")


def recover_stale(db):
    """A crashed synchronous request can be resumed after its short lease expires."""
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=current_app.config["PROCESSING_TIMEOUT"])).isoformat()
    error = json.dumps({"code": "interrupted", "message": "A tentativa foi interrompida. Seus dados estão salvos; tente novamente."})
    db.execute("""UPDATE incidents SET status = CASE WHEN status = 'triaging'
                  THEN 'triage_failed' ELSE 'analysis_failed' END,
                  operation_id = NULL, processing_since = NULL, last_error = ?, updated_at = ?
                  WHERE status IN ('triaging', 'analyzing') AND processing_since < ?""", (error, now(), cutoff))


def decode(row):
    item = dict(row)
    for key in ("measurements", "review", "report", "last_error"):
        item[key] = json.loads(item[key]) if item[key] is not None else None
    item["relevant_risk"] = bool(item["relevant_risk"])
    item.pop("request_id")
    item.pop("operation_id")
    item.pop("processing_since")
    return item


def get(incident_id):
    with connection() as db:
        recover_stale(db)
        row = db.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    if row is None:
        raise AppError("Ocorrência não encontrada.", "not_found", 404)
    return decode(row)


def create(data):
    with connection() as db:
        # The unique request ID also protects retries after a lost HTTP response.
        db.execute("""INSERT OR IGNORE INTO incidents
            (id, request_id, description, reference, relevant_risk, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'pending_triage', ?, ?)""",
                   (str(uuid4()), str(data.request_id), data.description, data.reference, int(data.relevant_risk), now(), now()))
        row = db.execute("SELECT * FROM incidents WHERE request_id = ?", (str(data.request_id),)).fetchone()
        if (row["description"], row["reference"], bool(row["relevant_risk"])) != (data.description, data.reference, data.relevant_risk):
            raise AppError("Este envio já foi usado por outro relato. Inicie um novo registro.", "request_conflict", 409)
    return get(row["id"])


def list_incidents(query, status, page):
    clauses, params = [], []
    if query:
        clauses.append("(instr(lower(description), lower(?)) > 0 OR instr(lower(reference), lower(?)) > 0 OR instr(id, ?) > 0)")
        params += [query, query, query]
    if status == "completed":
        clauses.append("status = 'completed'")
    elif status == "pending":
        clauses.append("status != 'completed'")
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with connection() as db:
        recover_stale(db)
        total = db.execute("SELECT count(*) FROM incidents" + where, params).fetchone()[0]
        rows = db.execute("SELECT * FROM incidents" + where + " ORDER BY created_at DESC LIMIT 20 OFFSET ?", params + [(page - 1) * 20]).fetchall()
    items = [decode(row) for row in rows]
    for item in items:
        item.pop("report")
    return {"items": items, "total": total, "page": page, "page_size": 20}


def editable_row(db, incident_id):
    recover_stale(db)
    row = db.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    if row is None:
        raise AppError("Ocorrência não encontrada.", "not_found", 404)
    if row["status"] in ("triaging", "analyzing", "completed"):
        raise AppError("Esta ocorrência está em processamento ou já foi concluída. Reabra o registro para consultar.", "state_conflict", 409)
    return row


def update_context(incident_id, data):
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        row = editable_row(db, incident_id)
        if data.measurements and row["category"] != "equipment":
            raise AppError("Medições de ML são usadas apenas em Produção e equipamentos.", "measurements_not_applicable", 422)
        measurements = data.measurements.model_dump_json() if data.measurements else None
        db.execute("UPDATE incidents SET complement = ?, measurements = ?, updated_at = ? WHERE id = ?",
                   (data.complement, measurements, now(), incident_id))
    return get(incident_id)


def save_review(incident_id, data):
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        row = editable_row(db, incident_id)
        if not row["suggested_category"]:
            raise AppError("Tente a classificação do Jev antes de revisar a categoria.", "triage_required", 409)
        review = json.dumps({"category": data.category, "justification": data.justification, "reviewed_at": now()}, ensure_ascii=False)
        db.execute("""UPDATE incidents SET category = ?, review = ?, status = 'ready', last_error = NULL,
                      measurements = CASE WHEN ? = 'equipment' THEN measurements ELSE NULL END,
                      updated_at = ? WHERE id = ?""", (data.category, review, data.category, now(), incident_id))
    return get(incident_id)


def claim(incident_id, action):
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        row = editable_row(db, incident_id)
        allowed = ("pending_triage", "triage_failed") if action == "triaging" else ("ready", "analysis_failed")
        if row["status"] not in allowed:
            raise AppError("Conclua a classificação e a revisão necessária antes da análise.", "state_conflict", 409)
        token = str(uuid4())
        db.execute("UPDATE incidents SET status = ?, operation_id = ?, processing_since = ?, last_error = NULL, updated_at = ? WHERE id = ?",
                   (action, token, now(), now(), incident_id))
    return token


def finish(incident_id, token, **fields):
    # Field names are internal constants; all user values use SQL parameters.
    permitted = {"status", "category", "suggested_category", "confidence", "jev_model", "report", "last_error"}
    if not fields.keys() <= permitted:
        raise ValueError("Invalid internal update")
    with connection() as db:
        assignments = ", ".join(f"{key} = ?" for key in fields)
        values = [json.dumps(value, ensure_ascii=False) if isinstance(value, dict) else value for value in fields.values()]
        cursor = db.execute(f"UPDATE incidents SET {assignments}, updated_at = ?, operation_id = NULL, processing_since = NULL WHERE id = ? AND operation_id = ?",
                            values + [now(), incident_id, token])
        if cursor.rowcount != 1:
            raise AppError("A tentativa expirou. Reabra a ocorrência.", "state_conflict", 409)
