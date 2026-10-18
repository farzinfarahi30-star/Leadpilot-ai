#!/usr/bin/env python3
"""NOVA outreach safety gate (stdlib-only, no network or email sends).

Use one shared SQLite database per sending environment. Every outbound cold outreach
worker MUST call 'reserve' before sending and 'confirm-sent' after successful send.
A reservation is never automatically cleared; ambiguous delivery stays blocked.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_DB = Path.home() / ".nova" / "outreach_guard.sqlite3"
EMAIL_RE = re.compile(r"^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$")


def canon(email: str) -> str:
    value = email.strip().lower()
    if not EMAIL_RE.fullmatch(value) or len(value) > 254:
        raise ValueError("invalid recipient email")
    return value


def connect(path: str | Path) -> sqlite3.Connection:
    db = Path(path).expanduser()
    db.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(db, timeout=30, isolation_level=None)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA busy_timeout=30000")
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript("""
        CREATE TABLE IF NOT EXISTS suppressions (
            recipient TEXT PRIMARY KEY,
            reason TEXT NOT NULL,
            recorded_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS attempts (
            token TEXT PRIMARY KEY,
            recipient TEXT NOT NULL,
            campaign TEXT NOT NULL,
            body_sha256 TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('reserved','sent','cancelled')),
            reserved_at TEXT NOT NULL,
            sent_at TEXT,
            CHECK(length(body_sha256)=64)
        );
        CREATE INDEX IF NOT EXISTS attempts_contact ON attempts(recipient,status,reserved_at);
    """)
    return c


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def check_block(c: sqlite3.Connection, recipient: str, days: int) -> str | None:
    if days < 1 or days > 3650:
        raise ValueError("cooldown-days must be from 1 to 3650")
    suppressed = c.execute("SELECT reason FROM suppressions WHERE recipient=?", (recipient,)).fetchone()
    if suppressed:
        return "suppressed: " + suppressed["reason"]
    if c.execute("SELECT 1 FROM attempts WHERE recipient=? AND status='reserved' LIMIT 1", (recipient,)).fetchone():
        return "outstanding_reservation"
    since = (utc_now() - timedelta(days=days)).isoformat()
    if c.execute("SELECT 1 FROM attempts WHERE recipient=? AND status='sent' AND sent_at>=? LIMIT 1", (recipient, since)).fetchone():
        return "cooldown_active"
    return None


def reserve(c: sqlite3.Connection, email: str, campaign: str, body: str, days: int = 30) -> dict:
    recipient = canon(email)
    campaign = campaign.strip()
    if not campaign or len(campaign) > 120 or not body.strip():
        raise ValueError("campaign and nonempty message body are required")
    c.execute("BEGIN IMMEDIATE")
    try:
        reason = check_block(c, recipient, days)
        if reason:
            c.execute("ROLLBACK")
            return {"allowed": False, "recipient": recipient, "reason": reason}
        token = str(uuid.uuid4())
        digest = hashlib.sha256(body.strip().encode("utf-8")).hexdigest()
        c.execute("INSERT INTO attempts(token,recipient,campaign,body_sha256,status,reserved_at) VALUES(?,?,?,?,'reserved',?)", (token, recipient, campaign, digest, utc_now().isoformat()))
        c.execute("COMMIT")
        return {"allowed": True, "recipient": recipient, "reservation_token": token, "status": "reserved", "note": "Not sent. Send externally only after additional full-thread and consent checks; then confirm-sent."}
    except Exception:
        c.execute("ROLLBACK")
        raise


def suppress(c: sqlite3.Connection, email: str, reason: str) -> dict:
    recipient = canon(email)
    if not reason.strip():
        raise ValueError("reason is required")
    c.execute("BEGIN IMMEDIATE")
    try:
        c.execute("INSERT INTO suppressions(recipient,reason,recorded_at) VALUES(?,?,?) ON CONFLICT(recipient) DO UPDATE SET reason=excluded.reason, recorded_at=excluded.recorded_at", (recipient, reason.strip(), utc_now().isoformat()))
        c.execute("COMMIT")
    except Exception:
        c.execute("ROLLBACK")
        raise
    return {"recipient": recipient, "suppressed": True}


def finalize(c: sqlite3.Connection, token: str, action: str) -> dict:
    if action not in ("sent", "cancelled"):
        raise ValueError("invalid action")
    c.execute("BEGIN IMMEDIATE")
    try:
        row = c.execute("SELECT recipient,status FROM attempts WHERE token=?", (token,)).fetchone()
        if not row:
            c.execute("ROLLBACK")
            return {"ok": False, "reason": "unknown_reservation_token"}
        if row["status"] != "reserved":
            c.execute("ROLLBACK")
            return {"ok": False, "reason": "already_finalized", "status": row["status"]}
        if action == "sent":
            c.execute("UPDATE attempts SET status='sent',sent_at=? WHERE token=?", (utc_now().isoformat(), token))
        else:
            c.execute("UPDATE attempts SET status='cancelled' WHERE token=?", (token,))
        c.execute("COMMIT")
        return {"ok": True, "recipient": row["recipient"], "status": action}
    except Exception:
        c.execute("ROLLBACK")
        raise


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Local-only NOVA outreach guard. NEVER sends email.")
    ap.add_argument("--db", default=os.environ.get("NOVA_OUTREACH_GUARD_DB", str(DEFAULT_DB)))
    sub = ap.add_subparsers(dest="command", required=True)
    x = sub.add_parser("suppress", help="Persistently block a recipient")
    x.add_argument("email"); x.add_argument("--reason", required=True)
    x = sub.add_parser("check", help="Read-only preliminary check; not authorization to send")
    x.add_argument("email"); x.add_argument("--cooldown-days", type=int, default=30)
    x = sub.add_parser("reserve", help="Atomically reserve recipient before sending")
    x.add_argument("email"); x.add_argument("--campaign", required=True); x.add_argument("--body-file", required=True)
    x.add_argument("--cooldown-days", type=int, default=30)
    x = sub.add_parser("confirm-sent", help="Mark a reservation sent only after verified sending")
    x.add_argument("token")
    x = sub.add_parser("cancel", help="Release only when email definitely was NOT sent")
    x.add_argument("token")
    args = ap.parse_args(argv)
    try:
        c = connect(args.db)
        if args.command == "suppress":
            data = suppress(c, args.email, args.reason)
        elif args.command == "check":
            e = canon(args.email); reason = check_block(c, e, args.cooldown_days)
            data = {"allowed_for_reservation": not bool(reason), "recipient": e, "reason": reason}
        elif args.command == "reserve":
            body = Path(args.body_file).read_text(encoding="utf-8")
            data = reserve(c, args.email, args.campaign, body, args.cooldown_days)
        else:
            data = finalize(c, args.token, "sent" if args.command == "confirm-sent" else "cancelled")
        print(json.dumps(data, ensure_ascii=False))
        if data.get("allowed") is False or data.get("allowed_for_reservation") is False or data.get("ok") is False:
            return 2
        return 0
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
