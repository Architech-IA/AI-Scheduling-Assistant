"""
Gestión de sesiones de conversación.
Usa Redis si está disponible, SQLite como fallback.
"""
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

try:
    import redis
    from config.settings import settings
    _redis = redis.from_url(settings.redis_url, decode_responses=True)
    _redis.ping()
    USE_REDIS = True
    logger.info("Sesiones: usando Redis")
except Exception:
    USE_REDIS = False
    logger.warning("Redis no disponible — usando SQLite como fallback")

# SQLite fallback
DB_PATH = "data/sessions.db"

def _init_sqlite():
    import os
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            data       TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

if not USE_REDIS:
    _init_sqlite()


def get_session(session_id: str) -> dict:
    """Recupera la sesión. Retorna dict vacío si no existe."""
    if USE_REDIS:
        raw = _redis.get(f"session:{session_id}")
        return json.loads(raw) if raw else {}
    else:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT data FROM sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        conn.close()
        return json.loads(row[0]) if row else {}


def save_session(session_id: str, data: dict) -> None:
    """Guarda o actualiza la sesión."""
    from config.settings import settings
    ttl_seconds = settings.session_ttl_days * 86400

    if USE_REDIS:
        _redis.setex(
            f"session:{session_id}",
            ttl_seconds,
            json.dumps(data, ensure_ascii=False)
        )
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            INSERT INTO sessions (session_id, data, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                data=excluded.data,
                updated_at=excluded.updated_at
        """, (session_id, json.dumps(data, ensure_ascii=False), datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()


def delete_session(session_id: str) -> None:
    if USE_REDIS:
        _redis.delete(f"session:{session_id}")
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))
        conn.commit()
        conn.close()


def get_history(session_id: str) -> list[dict]:
    """Retorna el historial de mensajes de la sesión."""
    session = get_session(session_id)
    return session.get("history", [])


def append_message(session_id: str, role: str, content: str) -> list[dict]:
    """Agrega un mensaje al historial y recorta si supera max_turns."""
    from config.settings import settings
    session = get_session(session_id)
    history = session.get("history", [])
    history.append({"role": role, "content": content})

    # Recortar historial para controlar costos — conservar últimos N turnos
    max_messages = settings.max_history_turns * 2  # cada turno = user + assistant
    if len(history) > max_messages:
        history = history[-max_messages:]

    session["history"] = history
    session["updated_at"] = datetime.utcnow().isoformat()
    save_session(session_id, session)
    return history


def get_metadata(session_id: str) -> dict:
    """Recupera metadata del caso (área, urgencia, etc.)."""
    return get_session(session_id).get("metadata", {})


def save_metadata(session_id: str, metadata: dict) -> None:
    session = get_session(session_id)
    session["metadata"] = {**session.get("metadata", {}), **metadata}
    save_session(session_id, session)
