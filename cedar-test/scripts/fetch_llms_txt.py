#!/usr/bin/env python3
"""
Fetch llms-full.txt from Cedar and/or Mastra and save locally with conditional requests.

Examples:
  # Fetch both Cedar and Mastra docs (default)
  python scripts/fetch_llms_txt.py
  
  # Fetch only Cedar docs
  python scripts/fetch_llms_txt.py --cedar-only
  
  # Fetch only Mastra docs  
  python scripts/fetch_llms_txt.py --mastra-only
  
  # Custom URL and output (legacy mode)
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
    # Determine user agent based on source
    if "mastra.ai" in url:
        user_agent = "mastra-llms-fetcher/1.0 (+https://mastra.ai)"
    else:
        user_agent = "cedar-llms-fetcher/1.0 (+https://docs.cedarcopilot.com)"
    
    headers = {
        "User-Agent": user_agent,
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


def fetch_single_doc(url: str, out_path: Path, source_name: str) -> bool:
    """Fetch a single documentation file. Returns True if successful."""
    # Enforce llms-full.txt; allow root URLs and auto-append
    if not url.endswith("/llms-full.txt"):
        if url.endswith("/llms.txt"):
            print(f"Error: This script is restricted to llms-full.txt for {source_name}.", file=sys.stderr)
            return False
        # Append llms-full.txt for convenience
        if url.endswith("/"):
            url = url + "llms-full.txt"
        else:
            url = url.rstrip("/") + "/llms-full.txt"
    
    meta_path = out_path.with_suffix(out_path.suffix + ".meta.json")
    meta = read_meta(meta_path)
    etag = meta.get("etag")
    last_modified = meta.get("last_modified")

    try:
        body, fetch_info = fetch_url(url, etag, last_modified)
        if body is None and fetch_info.get("status") == 304:
            print(f"{source_name}: Not modified (304). No update needed.")
            return True

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
            print(f"{source_name}: Updated {out_path}")
        else:
            print(f"{source_name}: No content change detected.")
        return True
    except Exception as e:
        print(f"{source_name}: Failed to fetch - {e}", file=sys.stderr)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch llms-full.txt from Cedar and/or Mastra")
    
    # Mode selection arguments
    parser.add_argument("--cedar-only", action="store_true",
                        help="Fetch only Cedar documentation")
    parser.add_argument("--mastra-only", action="store_true",
                        help="Fetch only Mastra documentation")
    
    # Legacy single-source mode
    parser.add_argument("--url", 
                        help="Custom URL (legacy mode - use for single source)")
    parser.add_argument("--out", 
                        help="Custom output path (legacy mode - use with --url)")
    
    args = parser.parse_args()
    
    # Resolve paths relative to project root (cedar-test directory)
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent  # Go up from scripts/ to cedar-test/
    
    # Legacy mode: single URL specified
    if args.url:
        if not args.out:
            print("Error: --out is required when using --url", file=sys.stderr)
            return 1
            
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = project_root / out_path
            
        # Determine source name from URL
        if "cedar" in args.url.lower():
            source_name = "Cedar"
        elif "mastra" in args.url.lower():
            source_name = "Mastra"
        else:
            source_name = "Custom"
            
        success = fetch_single_doc(args.url, out_path, source_name)
        return 0 if success else 1
    
    # Default mode: fetch both or selected sources
    sources = []
    
    if not args.mastra_only:  # Fetch Cedar unless --mastra-only
        sources.append({
            "name": "Cedar",
            "url": "https://docs.cedarcopilot.com/llms-full.txt",
            "out": project_root / "docs" / "cedar_llms_full.txt"
        })
    
    if not args.cedar_only:  # Fetch Mastra unless --cedar-only
        sources.append({
            "name": "Mastra",
            "url": "https://mastra.ai/llms-full.txt",
            "out": project_root / "docs" / "mastra_llms_full.txt"
        })
    
    if not sources:
        print("Error: Cannot specify both --cedar-only and --mastra-only", file=sys.stderr)
        return 1
    
    print(f"Fetching documentation from {len(sources)} source(s)...")
    print("-" * 50)
    
    success_count = 0
    for source in sources:
        if fetch_single_doc(source["url"], source["out"], source["name"]):
            success_count += 1
    
    print("-" * 50)
    print(f"Successfully fetched {success_count}/{len(sources)} documentation sources.")
    
    return 0 if success_count == len(sources) else 1


if __name__ == "__main__":
    sys.exit(main())


