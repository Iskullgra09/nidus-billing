from __future__ import annotations

import secrets
from datetime import datetime


def build_consecutive(
    *,
    branch_code: str,
    terminal: str = "00001",
    document_type: str,
    sequence: int,
) -> str:
    branch = "".join(ch for ch in (branch_code or "001") if ch.isdigit()) or "001"
    branch = branch.zfill(3)[-3:]
    term = "".join(ch for ch in terminal if ch.isdigit()) or "00001"
    term = term.zfill(5)[-5:]
    doc = document_type.zfill(2)[-2:]
    number = f"{max(sequence, 1):010d}"[-10:]
    return f"{branch}{term}{doc}{number}"


def build_clave(
    *,
    issued_at: datetime,
    emitter_id: str,
    consecutive: str,
    supply_situation: str = "1",
    security_code: str | None = None,
) -> str:
    day = issued_at.strftime("%d")
    month = issued_at.strftime("%m")
    year = issued_at.strftime("%y")
    cedula = "".join(ch for ch in emitter_id if ch.isdigit()).zfill(12)[-12:]
    situation = supply_situation if supply_situation in {"1", "2", "3"} else "1"
    security = security_code or f"{secrets.randbelow(100_000_000):08d}"
    if len(security) != 8 or not security.isdigit():
        security = f"{secrets.randbelow(100_000_000):08d}"
    clave = f"506{day}{month}{year}{cedula}{consecutive}{situation}{security}"
    if len(clave) != 50:
        raise ValueError("Generated Hacienda clave must be exactly 50 digits")
    return clave
