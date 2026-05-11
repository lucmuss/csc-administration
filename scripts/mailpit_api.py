#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


DEFAULT_BASE_URL = os.getenv("MAILPIT_API_URL", "http://localhost:8025/api/v1").rstrip("/")
VERIFICATION_CODE_PATTERN = re.compile(r"\b(\d{6})\b")


@dataclass
class MailpitMessage:
    message_id: str
    subject: str
    to: list[str]
    from_address: str
    created: str


def _get_json(url: str) -> dict[str, Any]:
    with urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _list_messages(base_url: str, limit: int) -> list[MailpitMessage]:
    payload = _get_json(f"{base_url}/messages?limit={limit}")
    messages = payload.get("messages", []) or []
    result: list[MailpitMessage] = []
    for item in messages:
        to = []
        for recipient in item.get("To", []) or []:
            address = recipient.get("Address")
            if address:
                to.append(address)
        result.append(
            MailpitMessage(
                message_id=item.get("ID", ""),
                subject=item.get("Subject", ""),
                to=to,
                from_address=(item.get("From") or {}).get("Address", ""),
                created=item.get("Created", ""),
            )
        )
    return result


def _get_message_text(base_url: str, message_id: str) -> str:
    payload = _get_json(f"{base_url}/message/{message_id}")
    text = payload.get("Text") or ""
    if text:
        return text
    html = payload.get("HTML") or ""
    return html


def _find_message(messages: list[MailpitMessage], *, recipient: str | None, subject_contains: str | None) -> MailpitMessage | None:
    for message in messages:
        if recipient and recipient not in message.to:
            continue
        if subject_contains and subject_contains.lower() not in message.subject.lower():
            continue
        return message
    return None


def cmd_list(args: argparse.Namespace) -> int:
    messages = _list_messages(args.base_url, args.limit)
    if args.json:
        print(json.dumps([message.__dict__ for message in messages], ensure_ascii=False, indent=2))
        return 0
    for message in messages:
        recipients = ", ".join(message.to) if message.to else "-"
        print(f"{message.created} | {message.message_id} | {message.subject} | to={recipients}")
    return 0


def cmd_wait_code(args: argparse.Namespace) -> int:
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        messages = _list_messages(args.base_url, args.limit)
        message = _find_message(messages, recipient=args.recipient, subject_contains=args.subject_contains)
        if message:
            body = _get_message_text(args.base_url, message.message_id)
            match = VERIFICATION_CODE_PATTERN.search(body)
            if match:
                code = match.group(1)
                if args.json:
                    print(
                        json.dumps(
                            {
                                "code": code,
                                "message_id": message.message_id,
                                "subject": message.subject,
                                "recipient": args.recipient,
                            },
                            ensure_ascii=False,
                        )
                    )
                else:
                    print(code)
                return 0
        time.sleep(args.poll_interval)

    print("Kein Verifizierungscode gefunden (Timeout).", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mailpit API helper fuer Agenten-Tests.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Mailpit API URL, z.B. http://localhost:8025/api/v1")

    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="Letzte Nachrichten auflisten")
    list_parser.add_argument("--limit", type=int, default=20)
    list_parser.add_argument("--json", action="store_true")
    list_parser.set_defaults(func=cmd_list)

    wait_parser = subparsers.add_parser("wait-code", help="Auf Verifizierungscode warten")
    wait_parser.add_argument("--recipient", default=None, help="Empfaenger-Adresse zum Filtern")
    wait_parser.add_argument("--subject-contains", default="Verifizierung", help="Betreff-Teilstring")
    wait_parser.add_argument("--timeout", type=int, default=90)
    wait_parser.add_argument("--poll-interval", type=float, default=2.0)
    wait_parser.add_argument("--limit", type=int, default=50)
    wait_parser.add_argument("--json", action="store_true")
    wait_parser.set_defaults(func=cmd_wait_code)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"Mailpit API nicht erreichbar: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
