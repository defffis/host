#!/usr/bin/env python3
"""Normalize HOSTS sources into one 'IP hostname' pair per line."""

from __future__ import annotations

import argparse
import ipaddress
import os
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

MAX_SOURCE_SIZE = 20 * 1024 * 1024
LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


def is_hostname(value: str) -> bool:
    return (
        1 <= len(value) <= 253
        and all(1 <= len(label) <= 63 and LABEL.fullmatch(label) for label in value.split("."))
    )


def normalize_hosts(content: str) -> tuple[str, int]:
    """Return normalized file and number of rejected tokens/lines.

    Only publicly routable IPs are accepted. Exact duplicate IP/host pairs
    are removed. Multiple IPs per hostname, input order, and publicly routed
    IPv4/IPv6 entries are preserved.
    """
    records: list[str] = []
    seen: set[tuple[str, str]] = set()
    rejected = 0

    for raw_line in content.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        fields = line.split()
        if len(fields) < 2:
            rejected += 1
            continue
        try:
            address = ipaddress.ip_address(fields[0])
        except ValueError:
            rejected += 1
            continue
        # A HOSTS feed must not override loopback, private, link-local,
        # multicast, reserved or other non-public destinations.
        # Python's is_global also returns True for multicast addresses,
        # so reject multicast explicitly (IPv4 224/4 and IPv6 ff00::/8).
        if not address.is_global or address.is_multicast or address.is_reserved:
            rejected += 1
            continue
        ip = str(address)
        for token in fields[1:]:
            hostname = token.lower().rstrip(".")
            if not is_hostname(hostname):
                rejected += 1
                continue
            pair = (ip, hostname)
            if pair not in seen:
                records.append(f"{ip} {hostname}")
                seen.add(pair)

    if not records:
        raise ValueError("Source contains no valid IP hostname records; existing file is preserved")
    return "\n".join(records) + "\n", rejected


def fetch_source(source_url: str) -> str:
    parsed = urlsplit(source_url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("SOURCE_URL must be an HTTPS URL without embedded credentials")
    request = urllib.request.Request(source_url, headers={"User-Agent": "hosts-normalizer/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        source = response.read(MAX_SOURCE_SIZE + 1)
    if len(source) > MAX_SOURCE_SIZE:
        raise ValueError("Source is larger than 20 MiB")
    return source.decode("utf-8-sig")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-url", default=os.getenv("SOURCE_URL"), help="HTTPS URL of source hosts file")
    parser.add_argument("--output", default="comss/hosts", help="Output hosts file")
    args = parser.parse_args()
    if not args.source_url:
        parser.error("Set SOURCE_URL environment variable or --source-url")

    try:
        source = fetch_source(args.source_url)
        output, rejected = normalize_hosts(source)
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_text(encoding="utf-8") == output:
            print(f"Unchanged: {len(output.splitlines())} records; rejected: {rejected}")
            return 0
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_text(output, encoding="utf-8", newline="\n")
        temporary.replace(target)
        print(f"Updated {target}: {len(output.splitlines())} records; rejected: {rejected}")
        return 0
    except (OSError, UnicodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
