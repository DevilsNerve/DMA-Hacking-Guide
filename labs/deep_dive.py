#!/usr/bin/env python3
"""Reproduce Chapters 16–20 calculations; synthetic inputs only, no live reads."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import struct
import sys

# Allow both `python labs/deep_dive.py ...` and `python -m labs.deep_dive ...`.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from labs.advanced_lab import (  # noqa: E402
    CASES, Entity, ReplayMonitor, Snapshot, compare, decode, make_case, replay_events,
)

ADDRESS_LIMIT = 1 << 32
MAX_SECTIONS = 96


class MappingError(ValueError):
    """The restricted section model cannot map the complete request."""


@dataclass(frozen=True)
class Section:
    name: str
    rva: int
    virtual_size: int
    raw_at: int
    raw_size: int


SECTIONS = (Section("code", 0x1000, 0x600, 0x400, 0x400),
            Section("data", 0x2000, 0x300, 0x800, 0x200),
            Section("state", 0x3000, 0x100, 0, 0))
REQUESTS = ((0x1250, 4), (0x13F8, 8), (0x13F8, 16),
            (0x1450, 4), (0x2100, 16), (0x3000, 1))


def uint32(value: int, field: str) -> None:
    if type(value) is not int or not 0 <= value < ADDRESS_LIMIT:
        raise MappingError(f"{field} must be a uint32")


def map_range(sections: tuple[Section, ...], file_size: int, rva: int, length: int) -> int:
    """Map a positive range using Chapter 16's model, not general PE semantics.

    This model permits 1..96 nonempty virtual sections, bounded uint32 metadata,
    and nonoverlapping virtual ranges. Each declared raw range must fit the file.
    Unmapped headers, raw alignment, directories and loader behavior are omitted.
    """
    uint32(file_size, "file size")
    if not 1 <= len(sections) <= MAX_SECTIONS:
        raise MappingError("section count must be from 1 through 96")
    for section in sections:
        for field in ("rva", "virtual_size", "raw_at", "raw_size"):
            uint32(getattr(section, field), field)
        if section.virtual_size == 0 or section.virtual_size > ADDRESS_LIMIT - section.rva:
            raise MappingError("invalid virtual extent")
        if section.raw_at > file_size or section.raw_size > file_size - section.raw_at:
            raise MappingError("declared raw range exceeds file")
    ordered = sorted(sections, key=lambda section: section.rva)
    for left, right in zip(ordered, ordered[1:]):
        if left.virtual_size > right.rva - left.rva:
            raise MappingError("ambiguous overlapping virtual ranges")
    uint32(rva, "request RVA")
    uint32(length, "request length")
    if length == 0 or length > ADDRESS_LIMIT - rva:
        raise MappingError("request must be nonempty and fit address width")
    for section in ordered:
        if rva < section.rva:
            continue
        delta = rva - section.rva
        if delta >= section.virtual_size or length > section.virtual_size - delta:
            continue
        if delta >= section.raw_size or length > section.raw_size - delta:
            raise MappingError("virtual range has no complete stored counterpart")
        # Metadata validation above proves raw_at + delta + length fits the file.
        return section.raw_at + delta
    raise MappingError("no section contains the complete virtual request")


def precision_values() -> tuple[float, float]:
    return tuple(struct.unpack("<f", bytes.fromhex(raw))[0]
                 for raw in ("cdcccc3d", "cecccc3d"))


def trace() -> list[dict]:
    monitor = ReplayMonitor()
    rows = []
    for at_ms, data in replay_events():
        status = monitor.observe(at_ms, data)
        rows.append({"at_ms": at_ms, "status": status,
                     "input_bytes": len(data) if data is not None else None,
                     "input_sha256": hashlib.sha256(data).hexdigest() if data is not None else None,
                     "accepted_generation": monitor.accepted.generation if monitor.accepted else None,
                     "last_observation_ms": monitor.last_observation_ms,
                     "last_progress_ms": monitor.last_progress_ms})
    return rows


def evidence() -> dict:
    cases = {case: make_case(case) for case in CASES}
    decoded = {case: decode(data) for case, data in cases.items()}
    return {
        "evidence_kind": "generated synthetic OBS2 fixtures; no capture backend",
        "schema": "OBS2 version 2",
        "identity_scope": "one declared synthetic session; unique entity IDs",
        "comparison_policy": "complete inputs; exact finite numeric equality; match by ID",
        "fixtures": {case: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                            "generation": decoded[case].generation,
                            "storage_ids": [item.identifier for item in decoded[case].entities]}
                     for case, data in cases.items()},
        "before_to_relocated": compare(decoded["before"], decoded["relocated"]).lines(),
        "before_to_after": compare(decoded["before"], decoded["after"]).lines(),
        "replay": trace(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("sections", "precision", "trace", "evidence"))
    args = parser.parse_args(argv)
    if args.command == "sections":
        for rva, length in REQUESTS:
            prefix = f"rva=0x{rva:x} length={length}"
            try:
                offset = map_range(SECTIONS, 4096, rva, length)
            except MappingError as error:
                print(f"{prefix} rejected: {error}")
            else:
                print(f"{prefix} file=0x{offset:x}")
    elif args.command == "precision":
        before, after = precision_values()
        for value in (before, after):
            print(f"bytes={struct.pack('<f', value).hex()} decoded={value:.17g} display={value:.9g}")
        result = compare(Snapshot("", 1, (Entity(1, before, 0, 0),)),
                         Snapshot("", 2, (Entity(1, after, 0, 0),)))
        print(result.changed[0])
    elif args.command == "trace":
        print("at_ms status accepted_generation last_observation_ms last_progress_ms")
        for row in trace():
            print(" ".join(str(row[key]) for key in
                           ("at_ms", "status", "accepted_generation", "last_observation_ms", "last_progress_ms")))
    else:
        print(json.dumps(evidence(), indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
