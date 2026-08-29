"""Local-only Zotero Desktop importer.

Uses the Connector service exposed by a running Zotero Desktop instance on
127.0.0.1. No Zotero Web API key and no internet connection are required.
Select the destination library or collection in Zotero before importing.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any


BASE_URL = "http://127.0.0.1:23119"
HEADERS = {"X-Zotero-Connector-API-Version": "3"}


def request(path: str, *, payload: Any | None = None, content_type: str = "application/json") -> Any:
    body = None
    headers = dict(HEADERS)
    if payload is not None:
        body = payload.encode("utf-8") if isinstance(payload, str) else json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = content_type
    try:
        with urllib.request.urlopen(
            urllib.request.Request(BASE_URL + path, data=body, headers=headers, method="POST" if payload is not None else "GET"),
            timeout=15,
        ) as response:
            text = response.read().decode("utf-8", errors="replace")
            try:
                return json.loads(text) if text else {}
            except json.JSONDecodeError:
                return {"response": text}
    except urllib.error.URLError as exc:
        raise RuntimeError("Zotero Desktop or its local Connector service is not available on this computer.") from exc
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"Zotero Connector returned HTTP {exc.code}: {detail}") from exc


def show(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def selected_target() -> dict[str, Any]:
    result = request("/connector/getSelectedCollection", payload={})
    if not isinstance(result, dict):
        raise RuntimeError("Zotero Connector did not return a selected target.")
    return result


def status(_: argparse.Namespace) -> None:
    ping = request("/connector/ping", payload={})
    target = selected_target()
    show({
        "connector": "ready",
        "ping": ping,
        "selected_library": target.get("libraryName"),
        "selected_collection": target.get("name"),
        "editable": bool(target.get("editable")),
        "files_editable": bool(target.get("filesEditable")),
    })


def target(_: argparse.Namespace) -> None:
    show(selected_target())


def import_records(args: argparse.Namespace) -> None:
    source = Path(args.file)
    text = source.read_text(encoding="utf-8")
    if not text.strip():
        raise RuntimeError("The selected import file is empty.")
    destination = selected_target()
    plan = {
        "action": "import_records_into_current_zotero_target",
        "format": args.format,
        "source_file": str(source.resolve()),
        "characters": len(text),
        "selected_library": destination.get("libraryName"),
        "selected_collection": destination.get("name"),
        "target_editable": bool(destination.get("editable")),
    }
    if not args.apply:
        show({"dry_run": True, "plan": plan, "next_step": "Review the selected collection, then repeat with --apply."})
        return
    if not destination.get("editable"):
        raise RuntimeError("The currently selected Zotero target is not editable.")
    session = f"local-zotero-{uuid.uuid4().hex}"
    response = request(f"/connector/import?{urllib.parse.urlencode({'session': session})}", payload=text, content_type="text/plain")
    show({"imported": True, "plan": plan, "connector_response": response})


def main() -> int:
    parser = argparse.ArgumentParser(description="Local-only Zotero Connector importer; select destination in Zotero first.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status").set_defaults(run=status)
    commands.add_parser("selected-target").set_defaults(run=target)
    imported = commands.add_parser("import")
    imported.add_argument("--format", choices=("bibtex", "ris"), required=True)
    imported.add_argument("--file", required=True)
    imported.add_argument("--apply", action="store_true")
    imported.set_defaults(run=import_records)
    args = parser.parse_args()
    try:
        args.run(args)
        return 0
    except (OSError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

