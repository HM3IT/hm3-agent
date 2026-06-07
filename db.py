import sqlite3

from datetime import datetime

from pathlib import Path
from typing import Optional

from config import TZ


class StateStore:
    def __init__(self, db_path: Path) -> None:
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS processed_files (
                source_key TEXT PRIMARY KEY,
                file_unique_id TEXT,
                update_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                filename TEXT,
                status TEXT NOT NULL,
                error TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS pending_manual_entries (
                chat_id INTEGER PRIMARY KEY,
                created_at TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def get_next_offset(self) -> Optional[int]:
        row = self.connection.execute(
            "SELECT value FROM settings WHERE key = 'next_offset'"
        ).fetchone()
        return int(row["value"]) if row else None

    def set_next_offset(self, value: int) -> None:
        self.connection.execute(
            """
            INSERT INTO settings(key, value) VALUES('next_offset', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (str(value),),
        )
        self.connection.commit()

    def file_status(self, source_key: str) -> Optional[str]:
        row = self.connection.execute(
            "SELECT status FROM processed_files WHERE source_key = ?",
            (source_key,),
        ).fetchone()
        return row["status"] if row else None

    def mark_started(
        self,
        source_key: str,
        file_unique_id: str,
        update_id: int,
        chat_id: int,
        message_id: int,
        filename: str,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO processed_files(
                source_key, file_unique_id, update_id, chat_id, message_id,
                filename, status, error, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 'processing', NULL, ?)
            ON CONFLICT(source_key) DO UPDATE SET
                status = 'processing',
                error = NULL,
                update_id = excluded.update_id,
                chat_id = excluded.chat_id,
                message_id = excluded.message_id,
                filename = excluded.filename
            """,
            (
                source_key,
                file_unique_id,
                update_id,
                chat_id,
                message_id,
                filename,
                datetime.now(TZ).isoformat(),
            ),
        )
        self.connection.commit()

    def mark_completed(self, source_key: str) -> None:
        self.connection.execute(
            """
            UPDATE processed_files
            SET status = 'completed', error = NULL, completed_at = ?
            WHERE source_key = ?
            """,
            (datetime.now(TZ).isoformat(), source_key),
        )
        self.connection.commit()

    def mark_failed(self, source_key: str, error: str) -> None:
        self.connection.execute(
            """
            UPDATE processed_files
            SET status = 'failed', error = ?
            WHERE source_key = ?
            """,
            (error[:2000], source_key),
        )
        self.connection.commit()

    def start_manual_entry(self, chat_id: int) -> None:
        self.connection.execute(
            """
            INSERT INTO pending_manual_entries(chat_id, created_at)
            VALUES (?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                created_at = excluded.created_at
            """,
            (
                chat_id,
                datetime.now(TZ).isoformat(),
            ),
        )
        self.connection.commit()


    def is_manual_entry_pending(self, chat_id: int) -> bool:
        row = self.connection.execute(
            """
            SELECT chat_id
            FROM pending_manual_entries
            WHERE chat_id = ?
            """,
            (chat_id,),
        ).fetchone()

        return row is not None


    def clear_manual_entry(self, chat_id: int) -> None:
        self.connection.execute(
            """
            DELETE FROM pending_manual_entries
            WHERE chat_id = ?
            """,
            (chat_id,),
        )
        self.connection.commit()