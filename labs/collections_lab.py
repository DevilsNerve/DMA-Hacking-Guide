#!/usr/bin/env python3
"""Chapter 15 text, layout and bounded-traversal experiments; synthetic data only."""

from __future__ import annotations

import argparse
import codecs
from dataclasses import replace
from pathlib import Path
import struct
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from labs.advanced_lab import (  # noqa: E402
    HEADER, ENTITY, DecodeError, decode, encode, make_case, semantic_view,
)

TEXT_SAMPLES = (("ascii", "A"), ("precomposed", "\u00e9"),
                ("combining", "e\u0301"), ("compass", "\U0001f9ed"),
                ("embedded-nul", "A\x00B"), ("leading-feff", "\ufeffA"))


def text_image(raw: bytes, units: int) -> bytes:
    """Build a counted-text OBS2 input directly, including deliberately bad text."""
    return HEADER.pack(b"OBS2", 2, 32, 0, 0, units, 32, 32 + len(raw)) + raw


def change_u32(data: bytes, offset: int, value: int) -> bytes:
    result = bytearray(data)
    struct.pack_into("<I", result, offset, value)
    return bytes(result)


def array_first() -> bytes:
    snapshot = decode(make_case("before"))
    name = snapshot.label.encode("utf-16-le")
    records = b"".join(ENTITY.pack(item.identifier, item.health, item.x, item.y)
                       for item in snapshot.entities)
    return (HEADER.pack(b"OBS2", 2, 32, snapshot.generation, len(snapshot.entities),
                        len(name) // 2, 32 + len(records), 32) + records + name)


def layout_cases() -> list[dict]:
    baseline = decode(make_case("before"))
    inputs = (("baseline", make_case("before")), ("array-first", array_first()),
              ("unaligned", encode(baseline, padding=1)),
              ("reordered", encode(replace(baseline, entities=tuple(reversed(baseline.entities))), padding=16)))
    rows = []
    for name, data in inputs:
        _, _, _, _, _, _, name_at, entities_at = HEADER.unpack_from(data)
        rows.append({"case": name, "bytes": len(data), "name_at": name_at, "entities_at": entities_at,
                     "equal": semantic_view(decode(data)) == semantic_view(baseline)})
    return rows


def decoder_cases() -> list[dict]:
    baseline = make_case("before")
    empty = text_image(b"", 0)
    inputs = [
        ("empty", empty, None),
        ("empty-offset-zero", change_u32(empty, 28, 0), "payload range"),
        ("empty-offset-past-end", change_u32(empty, 28, 33), "payload range"),
        ("exact-end", baseline, None),
        ("missing-last-byte", baseline[:-1], "payload range"),
        ("array-first", array_first(), None),
        ("unaligned", encode(decode(baseline), padding=1), None),
        ("overlap", change_u32(baseline, 24, 48), "overlap"),
        ("count-65", change_u32(baseline, 16, 65), "entity count"),
        ("units-65", change_u32(baseline, 20, 65), "name length"),
        ("high-surrogate", text_image(bytes.fromhex("00d8"), 1), "malformed UTF-16"),
        ("low-surrogate", text_image(bytes.fromhex("00dc"), 1), "malformed UTF-16"),
        ("high-then-ascii", text_image(bytes.fromhex("00d84100"), 2), "malformed UTF-16"),
        ("reversed-pair", text_image(bytes.fromhex("eddd3ed8"), 2), "malformed UTF-16"),
        ("partial-unit", text_image(bytes.fromhex("3e"), 1), "payload range"),
        ("duplicate-id", change_u32(baseline, 64, 10), "nonzero and unique"),
        ("zero-id", change_u32(baseline, 48, 0), "nonzero and unique"),
        ("nan-health", change_u32(baseline, 52, 0x7FC00000), "must be finite"),
        ("infinite-x", change_u32(baseline, 56, 0x7F800000), "must be finite"),
    ]
    for name, label in (("ascii-64", "A" * 64), ("compass-32", "\U0001f9ed" * 32),
                        ("mixed-64-units", "A" * 62 + "\U0001f9ed"),
                        ("mixed-65-units", "A" * 63 + "\U0001f9ed"),
                        ("embedded-nul", "A\x00B"), ("leading-feff", "\ufeffA")):
        raw = label.encode("utf-16-le")
        inputs.append((name, text_image(raw, len(raw) // 2), "name length" if len(raw) > 128 else None))
    rows = []
    for name, data, expected_error in inputs:
        try:
            result = decode(data)
        except DecodeError as error:
            detail = str(error)
            passed = expected_error is not None and expected_error in detail
            outcome = "rejected"
        else:
            detail = f"label={ascii(result.label)} entities={len(result.entities)}"
            passed = expected_error is None
            outcome = "accepted"
        rows.append({"case": name, "outcome": outcome, "detail": detail, "passed": passed})
    return rows


class TraversalError(ValueError):
    """A synthetic index chain violates its termination, range or work contract."""


def walk_chain(links: tuple[int, ...], start: int, budget: int) -> tuple[int, ...]:
    """Follow one index chain, with -1 as the only end marker and no legal cycles.

    This is an immutable index-table exercise, not an OBS2 or live-pointer layout.
    """
    if type(budget) is not int or not 0 <= budget <= 1024 or len(links) > 1024:
        raise TraversalError("table and visit budget must be bounded by 1024")
    order, visited = [], set()
    current = start
    while True:
        if type(current) is not int:
            raise TraversalError("link index must be an integer")
        if current == -1:
            return tuple(order)
        if not 0 <= current < len(links):
            raise TraversalError(f"index out of range: {current}")
        if current in visited:
            raise TraversalError(f"cycle at index {current}")
        if len(order) >= budget:
            raise TraversalError("visit budget exhausted")
        visited.add(current)
        order.append(current)
        current = links[current]


def traversal_cases() -> list[dict]:
    cases = (("chain", (1, 2, -1), 0, 3, (0, 1, 2)),
             ("empty", (), -1, 0, ()),
             ("cycle", (1, 0), 0, 4, "cycle at index 0"),
             ("invalid-link", (3, -1), 0, 4, "index out of range: 3"),
             ("budget", (1, 2, -1), 0, 2, "visit budget exhausted"))
    rows = []
    for name, links, start, budget, expected in cases:
        try:
            order = walk_chain(links, start, budget)
        except TraversalError as error:
            detail = str(error)
            passed = isinstance(expected, str) and detail == expected
        else:
            detail = f"order={list(order)}"
            passed = order == expected
        rows.append({"case": name, "detail": detail, "passed": passed})
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("text", "cases", "layouts", "traversal"))
    args = parser.parse_args(argv)
    if args.command == "text":
        for name, value in TEXT_SAMPLES:
            raw = value.encode("utf-16-le")
            print(f"{name} text={ascii(value)} points={len(value)} units={len(raw) // 2} utf8={len(value.encode('utf-8'))} utf16={len(raw)} hex={raw.hex()}")
        decoder = codecs.getincrementaldecoder("utf-16-le")(errors="strict")
        for raw in (bytes.fromhex("3e"), bytes.fromhex("d8ed"), bytes.fromhex("dd")):
            print(f"chunk={raw.hex()} text={ascii(decoder.decode(raw, final=False))}")
        print(f"final text={ascii(decoder.decode(b'', final=True))}")
        return 0
    if args.command == "layouts":
        rows = layout_cases()
        for row in rows:
            print(f"{row['case']} bytes={row['bytes']} name={row['name_at']} array={row['entities_at']} equal={str(row['equal']).lower()}")
        return 0 if all(row["equal"] for row in rows) else 1
    rows = decoder_cases() if args.command == "cases" else traversal_cases()
    for row in rows:
        status = "PASS" if row["passed"] else "FAIL"
        outcome = f"{row['outcome']}: " if "outcome" in row else ""
        print(f"{status} {row['case']} {outcome}{row['detail']}")
    passed = sum(row["passed"] for row in rows)
    print(f"checks={len(rows)} passed={passed} failed={len(rows) - passed}")
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
