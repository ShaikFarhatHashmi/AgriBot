"""
app/models/chat_history.py
==========================
SQLite-based chat history storage.

Tables:
  conversations — one row per session (sidebar titles)
  messages      — all messages belonging to a conversation

User identity: session['user_email'] (matches your auth system)
"""
import sqlite3
import uuid
from datetime import datetime
from settings import AppConfig


def get_db():
    """Get a SQLite connection. Creates the DB file if it doesn't exist."""
    conn = sqlite3.connect(AppConfig.CHAT_DB_PATH)
    conn.row_factory = sqlite3.Row   # access columns by name
    return conn


def init_db():
    """
    Create tables on first run.
    Safe to call on every Flask startup — uses IF NOT EXISTS.
    """
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS conversations (
            id           TEXT PRIMARY KEY,
            user_email   TEXT NOT NULL,
            title        TEXT NOT NULL,
            created_at   TEXT NOT NULL,
            updated_at   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id              TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role            TEXT NOT NULL,
            content         TEXT NOT NULL,
            lang            TEXT DEFAULT 'en',
            created_at      TEXT NOT NULL,
            FOREIGN KEY (conversation_id)
                REFERENCES conversations(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS detection_results (
            id              TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            disease         TEXT NOT NULL,
            display_name    TEXT NOT NULL,
            confidence      REAL NOT NULL,
            reliable        INTEGER NOT NULL,
            rag_answer      TEXT,
            lang            TEXT DEFAULT 'en',
            created_at      TEXT NOT NULL,
            FOREIGN KEY (conversation_id)
                REFERENCES conversations(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()
    print("[AgriBot] Chat history DB initialised.")


# ── Conversation operations ───────────────────────────────────

def create_conversation(user_email, first_message):
    """
    Create a new conversation session.
    Title auto-generated from first message — exactly like ChatGPT.
    Returns the new conversation ID.
    """
    conv_id = str(uuid.uuid4())
    title   = first_message[:45] + ("..." if len(first_message) > 45 else "")
    now     = datetime.now().isoformat()

    conn = get_db()
    conn.execute(
        "INSERT INTO conversations VALUES (?,?,?,?,?)",
        (conv_id, user_email, title, now, now)
    )
    conn.commit()
    conn.close()
    return conv_id


def get_conversations(user_email, limit=40):
    """
    Get all conversations for a user, newest first.
    Used to populate the sidebar.
    """
    conn = get_db()
    rows = conn.execute("""
        SELECT   id, title, updated_at
        FROM     conversations
        WHERE    user_email = ?
        ORDER BY updated_at DESC
        LIMIT    ?
    """, (user_email, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_conversation(conv_id, user_email):
    """
    Delete a conversation and all its messages.
    Verifies ownership via user_email before deleting.
    """
    conn = get_db()
    # Delete child rows first (messages + detection results)
    conn.execute(
        "DELETE FROM messages WHERE conversation_id = ?", (conv_id,)
    )
    conn.execute(
        "DELETE FROM detection_results WHERE conversation_id = ?", (conv_id,)
    )
    # Delete the conversation itself — only if it belongs to this user
    conn.execute(
        "DELETE FROM conversations WHERE id = ? AND user_email = ?",
        (conv_id, user_email)
    )
    conn.commit()
    conn.close()


def rename_conversation(conv_id, user_email, new_title):
    """Rename a conversation (user double-clicks the title)."""
    conn = get_db()
    conn.execute(
        "UPDATE conversations SET title = ? WHERE id = ? AND user_email = ?",
        (new_title.strip()[:60], conv_id, user_email)
    )
    conn.commit()
    conn.close()


# ── Message operations ────────────────────────────────────────

def save_message(conversation_id, role, content, lang="en"):
    """
    Save a single message to a conversation.
    role: 'user' or 'bot'
    Also updates the conversation's updated_at timestamp.
    """
    msg_id = str(uuid.uuid4())
    now    = datetime.now().isoformat()

    conn = get_db()
    conn.execute(
        "INSERT INTO messages VALUES (?,?,?,?,?,?)",
        (msg_id, conversation_id, role, content, lang, now)
    )
    conn.execute(
        "UPDATE conversations SET updated_at = ? WHERE id = ?",
        (now, conversation_id)
    )
    conn.commit()
    conn.close()


def get_messages(conversation_id):
    """
    Get all messages for a conversation, oldest first.
    Returns list of dicts: {role, content, lang, created_at}
    """
    conn = get_db()
    rows = conn.execute("""
        SELECT role, content, lang, created_at
        FROM   messages
        WHERE  conversation_id = ?
        ORDER  BY created_at ASC
    """, (conversation_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Disease detection history ─────────────────────────────────

def save_detection(conversation_id, result, rag_answer, lang="en"):
    """
    Save a disease detection result to history.
    Called from image_controller after successful prediction.
    """
    det_id = str(uuid.uuid4())
    now    = datetime.now().isoformat()

    conn = get_db()
    conn.execute(
        "INSERT INTO detection_results VALUES (?,?,?,?,?,?,?,?,?)",
        (
            det_id,
            conversation_id,
            result["disease"],
            result["display_name"],
            result["confidence"],
            1 if result["reliable"] else 0,
            rag_answer,
            lang,
            now
        )
    )
    conn.execute(
        "UPDATE conversations SET updated_at = ? WHERE id = ?",
        (now, conversation_id)
    )
    conn.commit()
    conn.close()


def get_detections(conversation_id):
    """Get all detection results for a conversation."""
    conn = get_db()
    rows = conn.execute("""
        SELECT display_name, confidence, reliable,
               rag_answer, lang, created_at
        FROM   detection_results
        WHERE  conversation_id = ?
        ORDER  BY created_at ASC
    """, (conversation_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]