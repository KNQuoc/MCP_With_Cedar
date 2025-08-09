#!/usr/bin/env python3
"""
Fetch only Mintlify llms-full.txt and save locally with conditional requests.

Example:
  python scripts/fetch_llms_txt.py \
    --url https://docs.cedarcopilot.com/llms-full.txt \
    --out docs/cedar_llms_full.txt
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

import requests


def read_meta(meta_path: Path) -> dict:
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def write_meta(meta_path: Path, data: dict) -> None:
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def fetch_url(url: str, etag: Optional[str], last_modified: Optional[str]) -> Tuple[Optional[str], dict]:
    headers = {
        "User-Agent": "cedar-llms-fetcher/1.0 (+https://docs.cedarcopilot.com)",
        "Accept": "text/plain,*/*;q=0.8",
    }
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified

    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 304:
        return None, {"status": 304}
    resp.raise_for_status()
    return resp.text, {
        "status": resp.status_code,
        "etag": resp.headers.get("ETag"),
        "last_modified": resp.headers.get("Last-Modified"),
        "content_type": resp.headers.get("Content-Type"),
    }


def compute_sha256(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def maybe_write_text(output_path: Path, body: str, header_meta: dict) -> bool:
    header_lines = [
        f"Source: {header_meta.get('source_url')}",
        f"Fetched: {header_meta.get('fetched_at_iso')}",
        f"ETag: {header_meta.get('etag')}",
        f"Last-Modified: {header_meta.get('last_modified')}",
        "",
    ]
    full = "\n".join(header_lines) + body.rstrip() + "\n"
    prev = output_path.read_text(encoding="utf-8") if output_path.exists() else None
    if prev is not None and compute_sha256(prev) == compute_sha256(full):
        return False
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(full, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Mintlify llms-full txt file")
    parser.add_argument("--url", required=True, help="URL ending with /llms-full.txt or site root to auto-append")
    parser.add_argument("--out", required=True, help="Output file path")
    args = parser.parse_args()

    url = args.url
    # Enforce llms-full.txt; allow root URLs and auto-append
    if not url.endswith("/llms-full.txt"):
        if url.endswith("/llms.txt"):
            print("Error: This script is restricted to llms-full.txt. Use the /llms-full.txt endpoint.", file=sys.stderr)
            return 2
        # Append llms-full.txt for convenience
        if url.endswith("/"):
            url = url + "llms-full.txt"
        else:
            url = url.rstrip("/") + "/llms-full.txt"
    out_path = Path(args.out)
    meta_path = out_path.with_suffix(out_path.suffix + ".meta.json")

    meta = read_meta(meta_path)
    etag = meta.get("etag")
    last_modified = meta.get("last_modified")

    body, fetch_info = fetch_url(url, etag, last_modified)
    if body is None and fetch_info.get("status") == 304:
        print("Not modified (304). No update needed.")
        return 0

    fetched_at = datetime.now(timezone.utc).isoformat()
    header_meta = {
        "source_url": url,
        "fetched_at_iso": fetched_at,
        "etag": fetch_info.get("etag"),
        "last_modified": fetch_info.get("last_modified"),
    }

    changed = maybe_write_text(out_path, body, header_meta)
    meta.update({
        "source_url": url,
        "etag": fetch_info.get("etag"),
        "last_modified": fetch_info.get("last_modified"),
        "fetched_at_iso": fetched_at,
        "output": str(out_path),
        "hash": compute_sha256(body),
        "content_type": fetch_info.get("content_type"),
    })
    write_meta(meta_path, meta)

    if changed:
        print(f"Updated: {out_path}")
    else:
        print("No content change detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())


