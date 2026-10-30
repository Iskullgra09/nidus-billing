"""Simulate B8 inbound mailbox webhook. Usage: python scripts/simulate_inbound_mailbox.py --to ADDR"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_XML = ROOT / "scripts" / "fixtures" / "sample-inbound-mailbox.xml"
DEFAULT_ENV = ROOT / ".env"
DEFAULT_API = "http://localhost:8001/api/v1"


def _load_secret(env_path: Path) -> str:
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("INBOUND_MAILBOX_WEBHOOK_SECRET="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(f"Missing INBOUND_MAILBOX_WEBHOOK_SECRET in {env_path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", required=True, help="Mailbox address from Facturas de compra")
    parser.add_argument("--xml", type=Path, default=DEFAULT_XML)
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--api-base", default=DEFAULT_API)
    args = parser.parse_args()

    if not args.xml.is_file():
        raise SystemExit(f"XML not found: {args.xml}")
    secret = _load_secret(args.env)
    if not secret:
        raise SystemExit("INBOUND_MAILBOX_WEBHOOK_SECRET is empty")

    xml = args.xml.read_text(encoding="utf-8")
    payload = {
        "to": args.to,
        "from": "proveedor@example.com",
        "subject": "FE test local B8",
        "attachments": [{"filename": "fe.xml", "content": xml}],
    }
    body = json.dumps(payload).encode("utf-8")
    url = f"{args.api_base.rstrip('/')}/webhooks/inbound-mailbox"
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Nidus-Mailbox-Secret": secret,
        },
    )
    print(f"POST {url}")
    print(f"to={args.to}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            print(f"HTTP {resp.status}")
            print(raw)
            return 0
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code}")
        print(raw)
        return 1


if __name__ == "__main__":
    sys.exit(main())
