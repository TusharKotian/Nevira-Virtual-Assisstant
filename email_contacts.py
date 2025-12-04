import sqlite3
import threading
import os
from typing import List, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), "nevira_contacts.db")
_db_lock = threading.Lock()

def _get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db() -> None:
    with _db_lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE COLLATE NOCASE,
                    email TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

def add_contact(name: str, email: str) -> str:
    name_clean = (name or "").strip()
    email_clean = (email or "").strip()
    if not name_clean or not email_clean:
        return "Please provide both a name and an email address."

    with _db_lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO contacts (name, email) VALUES (?, ?)", (name_clean, email_clean))
                conn.commit()
                return f"Saved contact {name_clean} with email {email_clean}."
            except sqlite3.IntegrityError:
                return f"A contact named {name_clean} already exists. Use update to change the email."
        finally:
            conn.close()

def update_contact(name: str, email: str) -> str:
    name_clean = (name or "").strip()
    email_clean = (email or "").strip()
    if not name_clean or not email_clean:
        return "Please provide both the contact name and the new email address."

    with _db_lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute("UPDATE contacts SET email = ? WHERE name = ?", (email_clean, name_clean))
            conn.commit()
            if cur.rowcount == 0:
                return f"No contact named {name_clean} was found."
            return f"Updated {name_clean}'s email to {email_clean}."
        finally:
            conn.close()

def delete_contact(name: str) -> str:
    name_clean = (name or "").strip()
    if not name_clean:
        return "Please provide the name of the contact to delete."

    with _db_lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM contacts WHERE name = ?", (name_clean,))
            conn.commit()
            if cur.rowcount == 0:
                return f"No contact named {name_clean} was found."
            return f"Deleted contact {name_clean}."
        finally:
            conn.close()

def get_contact_email(name: str) -> Optional[str]:
    name_clean = (name or "").strip()
    if not name_clean:
        return None

    with _db_lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT email FROM contacts WHERE name = ? COLLATE NOCASE", (name_clean,))
            row = cur.fetchone()
            if row:
                return row[0]
            return None
        finally:
            conn.close()

def list_contacts() -> List[Tuple[str, str]]:
    with _db_lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT name, email FROM contacts ORDER BY name COLLATE NOCASE")
            rows = cur.fetchall()
            return [(r[0], r[1]) for r in rows]
        finally:
            conn.close()
