"""
database.py
Logika bazy danych SQLite: tworzenie tabel, zapis pomiarow,
odczyt historii sesji, eksport do CSV i usuwanie sesji.
"""

import csv
import sqlite3


class TimegrapherDB:
    def __init__(self, db_path="timegrapher_history.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._init_tables()

    def _init_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT (datetime('now','localtime')),
                target_bph INTEGER,
                watch_name TEXT DEFAULT '',
                lift_angle REAL DEFAULT 52.0
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp DATETIME DEFAULT (datetime('now','localtime')),
                rate REAL,
                beat_error REAL,
                bph INTEGER,
                amplitude REAL,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
        """)
        self.conn.commit()

        # Migracja: jesli baza istniala juz wczesniej bez tych kolumn, dodaj je bezpiecznie
        self._ensure_column("sessions", "watch_name", "TEXT DEFAULT ''")
        self._ensure_column("sessions", "lift_angle", "REAL DEFAULT 52.0")

    def _ensure_column(self, table: str, column: str, col_type: str):
        """Dodaje kolumne do istniejacej tabeli, jesli jeszcze jej nie ma."""
        self.cursor.execute(f"PRAGMA table_info({table})")
        existing_columns = [row[1] for row in self.cursor.fetchall()]
        if column not in existing_columns:
            self.cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            self.conn.commit()

    def create_session(self, target_bph: int, watch_name: str = "", lift_angle: float = 52.0) -> int:
        """Tworzy nowa sesje pomiarowa i zwraca jej ID."""
        self.cursor.execute(
            "INSERT INTO sessions (target_bph, watch_name, lift_angle) VALUES (?, ?, ?)",
            (target_bph, watch_name, lift_angle)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def save_measurement(self, session_id, rate, beat_error, bph, amplitude):
        self.cursor.execute(
            "INSERT INTO measurements (session_id, rate, beat_error, bph, amplitude) VALUES (?, ?, ?, ?, ?)",
            (session_id, rate, beat_error, bph, amplitude)
        )
        self.conn.commit()

    def get_sessions_summary(self):
        """Zwraca liste sesji z liczba zarejestrowanych pomiarow dla kazdej z nich."""
        self.cursor.execute("""
            SELECT s.id, s.timestamp, s.watch_name, s.target_bph, COUNT(m.id)
            FROM sessions s
            LEFT JOIN measurements m ON s.id = m.session_id
            GROUP BY s.id
            ORDER BY s.id DESC
        """)
        return self.cursor.fetchall()

    def export_session_to_csv(self, session_id, path):
        self.cursor.execute("""
            SELECT timestamp, rate, beat_error, bph, amplitude
            FROM measurements
            WHERE session_id = ?
            ORDER BY id ASC
        """, (session_id,))
        rows = self.cursor.fetchall()

        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Rate [s/d]", "Beat Error [ms]", "BPH", "Amplitude [°]"])
            writer.writerows(rows)

    def delete_session(self, session_id):
        self.cursor.execute("DELETE FROM measurements WHERE session_id = ?", (session_id,))
        self.cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()
