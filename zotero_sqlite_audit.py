"""Read-only structural audit for a closed Zotero SQLite database."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


INVALID_KEY_CHARS = "01IO"


def count(connection: sqlite3.Connection, sql: str) -> int:
    return int(connection.execute(sql).fetchone()[0])


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Zotero SQLite audit; Zotero must be closed.")
    parser.add_argument("--database", required=True, type=Path)
    args = parser.parse_args()
    if not args.database.is_file():
        raise SystemExit("Database file not found.")
    uri = f"file:{args.database.resolve().as_posix()}?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True)
        connection.execute("PRAGMA query_only=ON")
        report = {
            "database_integrity": [row[0] for row in connection.execute("PRAGMA integrity_check")],
            "foreign_key_violations": len(connection.execute("PRAGMA foreign_key_check").fetchall()),
            "active_collections": count(connection, "SELECT COUNT(*) FROM collections WHERE collectionID NOT IN (SELECT collectionID FROM deletedCollections)"),
            "active_items": count(connection, "SELECT COUNT(*) FROM items WHERE itemID NOT IN (SELECT itemID FROM deletedItems)"),
            "attachment_records": count(connection, "SELECT COUNT(*) FROM itemAttachments"),
            "orphan_collection_memberships": count(connection, "SELECT COUNT(*) FROM collectionItems ci LEFT JOIN collections c ON c.collectionID=ci.collectionID LEFT JOIN items i ON i.itemID=ci.itemID WHERE c.collectionID IS NULL OR i.itemID IS NULL"),
        }
        for table, label in (("collections", "unsafe_unsynced_collection_keys"), ("items", "unsafe_unsynced_item_keys")):
            rows = connection.execute(f"SELECT key FROM {table} WHERE synced=0 AND (key GLOB '*0*' OR key GLOB '*1*' OR key GLOB '*I*' OR key GLOB '*O*')").fetchall()
            report[label] = [row[0] for row in rows]
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except sqlite3.OperationalError as exc:
        raise SystemExit(f"Audit could not obtain a safe read-only database view: {exc}") from exc
    finally:
        if "connection" in locals():
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())

