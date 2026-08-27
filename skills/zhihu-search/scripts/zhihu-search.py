#!/usr/bin/env python3
"""Zhihu search skill script (Python stdlib only)."""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Dict, NoReturn
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://developer.zhihu.com"
REQUEST_TIMEOUT_SECONDS = 5


def print_usage() -> None:
    print(
        "Usage:\n"
        "  python3 zhihu-search.py "
        '\'{"query":"如何理解 rave 文化","count":5}\'\n\n'
        "Environment:\n"
        "  ZHIHU_ACCESS_SECRET      Bearer auth token\n"
        "  ZHIHU_OPENAPI_BASE_URL   Optional, default https://developer.zhihu.com\n"
        "  ZHIHU_ZHIHU_SEARCH_URL   Optional full endpoint override\n"
    )


def die(message: str, *, body: Any | None = None) -> NoReturn:
    payload: Dict[str, Any] = {"error": message, "exit_code": 1}
    if body is not None:
        payload["body"] = body
    print(json.dumps(payload, ensure_ascii=False))
    raise SystemExit(1)


def emit_raw(body_text: str) -> None:
    secret = os.getenv("ZHIHU_ACCESS_SECRET", "")
    if secret:
        body_text = body_text.replace(secret, "***")
    sys.stdout.write(body_text)
    if not body_text.endswith("\n"):
        sys.stdout.write("\n")


def die_http(err: HTTPError) -> NoReturn:
    body_text = err.read().decode("utf-8", errors="replace")
    if body_text:
        emit_raw(body_text)
        raise SystemExit(1)
    die(f"HTTP {err.code}")


def parse_payload(raw: str) -> Dict[str, Any]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        die("Invalid JSON payload")
    if not isinstance(data, dict):
        die("Invalid JSON payload")
    return data


def parse_query(payload: Dict[str, Any]) -> str:
    query = payload.get("query") or payload.get("Query") or ""
    if not isinstance(query, str) or not query.strip():
        die("query is required")
    query = query.strip()
    return query


def parse_count(payload: Dict[str, Any]) -> int:
    raw = payload.get("count", payload.get("Count", 10))
    try:
        count = int(raw)
    except (TypeError, ValueError):
        count = 10
    return max(1, min(10, count))


def get_endpoint() -> str:
    explicit = os.getenv("ZHIHU_ZHIHU_SEARCH_URL", "").strip()
    if explicit:
        return explicit
    base_url = os.getenv("ZHIHU_OPENAPI_BASE_URL", DEFAULT_BASE_URL).strip()
    return f"{base_url.rstrip('/')}/api/v1/content/zhihu_search"


def request_zhihu(query: str, count: int) -> str:
    secret = os.getenv("ZHIHU_ACCESS_SECRET", "").strip()
    if not secret:
        die("Set ZHIHU_ACCESS_SECRET first (Bearer auth only)")

    params = urlencode({"Query": query, "Count": str(count)})
    url = f"{get_endpoint()}?{params}"
    req = Request(
        url=url,
        method="GET",
        headers={
            "Authorization": f"Bearer {secret}",
            "X-Request-Timestamp": str(int(time.time())),
        },
    )

    try:
        with urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            body_text = resp.read().decode("utf-8", errors="replace")
    except HTTPError as err:
        die_http(err)
    except (URLError, TimeoutError):
        die("HTTP request failed (timeout or network error)")

    try:
        json.loads(body_text)
    except json.JSONDecodeError:
        die("Non-JSON response from API")
    return body_text


def main() -> None:
    if len(sys.argv) >= 2 and sys.argv[1] in {"-h", "--help"}:
        print_usage()
        return

    if len(sys.argv) < 2:
        print_usage()
        raise SystemExit(1)

    payload = parse_payload(sys.argv[1])
    query = parse_query(payload)
    count = parse_count(payload)

    emit_raw(request_zhihu(query, count))


if __name__ == "__main__":
    main()
