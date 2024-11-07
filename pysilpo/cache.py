import pickle
import sqlite3
from datetime import UTC, datetime
from pathlib import Path


class SQLiteCache:
    def __init__(self, db_name="cache.db", use_pickle=True):
        """Initialize with optional pickle support and a database name."""

        user_data_dir = Path.home() / ".pysilpo"
        user_data_dir.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
        self.db_name = user_data_dir / db_name

        self.conn = sqlite3.connect(str(self.db_name))
        self.cursor = self.conn.cursor()

        # Create the cache table with columns for key, value, and expiry time
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS cache (
                                key TEXT PRIMARY KEY,
                                value BLOB,  -- Store value as a binary blob
                                expiry REAL)"""
        )
        self.conn.commit()

        self.use_pickle = use_pickle  # Whether to use pickle for serialization

    def __del__(self):
        """Automatically close the SQLite connection when the object is deleted."""

        if self.conn:
            self.conn.close()

    def _check_expiry(self, key):
        """Check if the cache entry has expired."""
        self.cursor.execute("SELECT expiry FROM cache WHERE key = ?", (key,))
        result = self.cursor.fetchone()
        if result:
            expiry_time = result[0]
            now = datetime.now(tz=UTC).timestamp()
            return expiry_time < now  # Return True if expired
        return False

    def get(self, key):
        """Retrieve a cached value, or None if expired or not found."""
        # Check if the key exists and if it's expired
        if self._check_expiry(key):
            self.remove(key)  # Remove expired entry
            return None  # Expired

        self.cursor.execute("SELECT value FROM cache WHERE key = ?", (key,))
        result = self.cursor.fetchone()
        if result:
            value = result[0]
            if self.use_pickle:
                return pickle.loads(value)  # Deserialize using pickle
            return value
        return None  # Not found

    def set(self, key, value, expires_in: datetime | int):
        """Store a value in the cache with an optional TTL."""
        if isinstance(expires_in, int):
            expiry_time = expires_in
        else:
            expiry_time = round(expires_in.timestamp())  # Convert datetime to Unix timestamp
        # Serialize the value if using pickle
        if self.use_pickle:
            value = pickle.dumps(value)  # Serialize using pickle

        self.cursor.execute(
            "REPLACE INTO cache (key, value, expiry) VALUES (?, ?, ?)",
            (key, value, expiry_time),
        )
        self.conn.commit()

    def remove(self, key):
        """Remove a key-value pair from the cache."""
        self.cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
        self.conn.commit()

    def clear(self):
        """Clear the entire cache."""
        self.cursor.execute("DELETE FROM cache")
        self.conn.commit()

    def exists(self, key):
        """Check if a key exists in the cache (even if expired)."""
        self.cursor.execute("SELECT 1 FROM cache WHERE key = ?", (key,))
        return self.cursor.fetchone() is not None

    def get_all(self):
        """Retrieve all keys and values from the cache."""
        # TODO: Fix ttl check
        self.cursor.execute("SELECT key, value FROM cache")
        rows = self.cursor.fetchall()
        # If using pickle, deserialize each value
        if self.use_pickle:
            return [(key, pickle.loads(value)) for key, value in rows]
        return rows

    def close(self):
        """Close the SQLite database connection."""
        self.conn.close()
