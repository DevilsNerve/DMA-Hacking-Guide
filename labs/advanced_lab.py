#!/usr/bin/env python3
"""Decode, compare, and replay synthetic OBS2 observations. No live memory access."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
import hashlib
import math
from pathlib import Path
import struct
import sys

MAX_IMAGE = 4096
MAX_ENTITIES = 64
MAX_NAME_UNITS = 64
HEADER = struct.Struct("<4sHHQIIII")
ENTITY = struct.Struct("<Ifff")
LABEL = "Pilot \U0001f9ed"
CASES = ("before", "relocated", "after")


class DecodeError(ValueError):
    """The supplied bytes do not satisfy the OBS2 format."""


@dataclass(frozen=True)
class Entity:
    identifier: int
    health: float
    x: float
    y: float


@dataclass(frozen=True)
class Snapshot:
    label: str
    generation: int
    entities: tuple[Entity, ...]


def read_payload(data: bytes, offset: int, size: int) -> bytes:
    if offset < HEADER.size or size < 0 or offset > len(data) or size > len(data) - offset:
        raise DecodeError(f"unavailable payload range: offset={offset} size={size}")
    return data[offset:offset + size]


def decode(data: bytes) -> Snapshot:
    if not HEADER.size <= len(data) <= MAX_IMAGE:
        raise DecodeError("image size must be from 32 through 4096 bytes")
    magic, version, header_size, generation, count, units, name_at, entities_at = HEADER.unpack_from(data)
    if magic != b"OBS2":
        raise DecodeError("observation magic mismatch")
    if version != 2:
        raise DecodeError(f"unsupported observation version: {version}")
    if header_size != HEADER.size:
        raise DecodeError("observation header size mismatch")
    if count > MAX_ENTITIES:
        raise DecodeError("entity count exceeds limit 64")
    if units > MAX_NAME_UNITS:
        raise DecodeError("name length exceeds limit 64 UTF-16 code units")
    name_size, entities_size = units * 2, count * ENTITY.size
    name_bytes = read_payload(data, name_at, name_size)
    entity_bytes = read_payload(data, entities_at, entities_size)
    if name_size and entities_size and max(name_at, entities_at) < min(name_at + name_size, entities_at + entities_size):
        raise DecodeError("active payload ranges overlap")
    try:
        label = name_bytes.decode("utf-16-le", errors="strict")
    except UnicodeDecodeError as error:
        raise DecodeError("malformed UTF-16 name") from error
    entities = []
    identifiers: set[int] = set()
    for offset in range(0, len(entity_bytes), ENTITY.size):
        identifier, health, x, y = ENTITY.unpack_from(entity_bytes, offset)
        if identifier == 0 or identifier in identifiers:
            raise DecodeError("entity IDs must be nonzero and unique")
        if not all(math.isfinite(value) for value in (health, x, y)):
            raise DecodeError("entity fields must be finite")
        if not 0 <= health <= 100:
            raise DecodeError("health must be from 0 through 100")
        identifiers.add(identifier)
        entities.append(Entity(identifier, health, x, y))
    return Snapshot(label, generation, tuple(entities))


def encode(snapshot: Snapshot, padding: int = 0) -> bytes:
    """Serialize a teaching fixture; offsets refer to this file, never process RAM."""
    if not 0 <= snapshot.generation < (1 << 64):
        raise DecodeError("generation outside uint64 range")
    if not 0 <= padding <= 256:
        raise DecodeError("fixture padding must be from 0 through 256 bytes")
    if len(snapshot.entities) > MAX_ENTITIES:
        raise DecodeError("entity count exceeds limit 64")
    try:
        name = snapshot.label.encode("utf-16-le", errors="strict")
        if len(name) // 2 > MAX_NAME_UNITS:
            raise DecodeError("name length exceeds limit 64 UTF-16 code units")
        payload = b"".join(ENTITY.pack(item.identifier, item.health, item.x, item.y)
                           for item in snapshot.entities)
    except (UnicodeError, struct.error, OverflowError) as error:
        raise DecodeError("fixture value cannot be represented in OBS2") from error
    name_at = HEADER.size + padding
    entities_at = name_at + len(name)
    data = HEADER.pack(b"OBS2", 2, HEADER.size, snapshot.generation,
                       len(snapshot.entities), len(name) // 2, name_at, entities_at)
    data += bytes(padding) + name + payload
    decode(data)  # Apply the same public format invariants before writing a fixture.
    return data


def make_case(case: str) -> bytes:
    before = Snapshot(LABEL, 2, (Entity(10, 87.5, 1, 2), Entity(20, 100, 10, 12), Entity(40, 50, -1, 3)))
    if case == "before":
        return encode(before)
    if case == "relocated":
        return encode(replace(before, entities=tuple(reversed(before.entities))), padding=16)
    if case == "after":
        return encode(Snapshot(LABEL, 4, (Entity(20, 100, 10, 13), Entity(10, 60, 1, 2), Entity(30, 75, 100, 101))), padding=16)
    raise DecodeError(f"unknown fixture case: {case}")


def semantic_view(snapshot: Snapshot) -> tuple[str, tuple[Entity, ...]]:
    return snapshot.label, tuple(sorted(snapshot.entities, key=lambda item: item.identifier))


@dataclass(frozen=True)
class Comparison:
    before_generation: int
    after_generation: int
    label_changed: bool
    added: tuple[int, ...]
    removed: tuple[int, ...]
    changed: tuple[str, ...]

    def lines(self) -> list[str]:
        return [f"generations={self.before_generation}->{self.after_generation}",
                f"label_changed={'yes' if self.label_changed else 'no'}",
                f"added={list(self.added)} removed={list(self.removed)}",
                f"changed={list(self.changed)}"]


def compare(before: Snapshot, after: Snapshot) -> Comparison:
    old = {item.identifier: item for item in before.entities}
    new = {item.identifier: item for item in after.entities}
    changes = []
    for identifier in sorted(old.keys() & new.keys()):
        for field in ("health", "x", "y"):
            left, right = getattr(old[identifier], field), getattr(new[identifier], field)
            if left != right:
                changes.append(f"{identifier}.{field}:{left:g}->{right:g}")
    return Comparison(before.generation, after.generation, before.label != after.label,
                      tuple(sorted(new.keys() - old.keys())), tuple(sorted(old.keys() - new.keys())),
                      tuple(changes))


class ReplayMonitor:
    """A policy for one declared session, driven by observations and supplied times."""

    def __init__(self, progress_budget_ms: int = 100):
        if type(progress_budget_ms) is not int or progress_budget_ms < 0:
            raise ValueError("progress budget must be a nonnegative integer")
        self.progress_budget_ms = progress_budget_ms
        self.last_observation_ms: int | None = None
        self.last_progress_ms: int | None = None
        self.accepted: Snapshot | None = None

    def observe(self, at_ms: int, data: bytes | None) -> str:
        if type(at_ms) is not int or at_ms < 0 or self.last_observation_ms is not None and at_ms < self.last_observation_ms:
            raise ValueError("observation times must be nonnegative, nondecreasing integers")
        self.last_observation_ms = at_ms
        if data is None:
            return "unavailable"
        try:
            snapshot = decode(data)
        except DecodeError:
            return "invalid"
        if self.accepted is None or snapshot.generation > self.accepted.generation:
            self.accepted, self.last_progress_ms = snapshot, at_ms
            return "accepted"
        if snapshot.generation < self.accepted.generation:
            return "regressed"
        if semantic_view(snapshot) != semantic_view(self.accepted):
            return "inconsistent"
        assert self.last_progress_ms is not None
        if at_ms - self.last_progress_ms > self.progress_budget_ms:
            return "no-progress"
        return "duplicate"


def replay_events() -> list[tuple[int, bytes | None]]:
    before, after = make_case("before"), make_case("after")
    invalid = bytearray(before)
    struct.pack_into("<H", invalid, 4, 3)
    snapshot = decode(after)
    conflicting = replace(snapshot, entities=tuple(
        replace(item, health=55) if item.identifier == 10 else item for item in snapshot.entities))
    return [(0, before), (10, before), (20, None), (30, bytes(invalid)),
            (40, after), (50, before), (60, encode(conflicting)), (200, after)]


def read_file(path: Path) -> bytes:
    with path.open("rb") as source:
        data = source.read(MAX_IMAGE + 1)
    if len(data) > MAX_IMAGE:
        raise DecodeError("image exceeds 4096-byte limit")
    return data


def show(snapshot: Snapshot) -> None:
    print(f"label={ascii(snapshot.label)} generation={snapshot.generation} entities={len(snapshot.entities)}")
    print(f"ids={[item.identifier for item in snapshot.entities]}")
    for item in snapshot.entities:
        print(f"id={item.identifier} health={item.health:g} x={item.x:g} y={item.y:g}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo")
    commands.add_parser("replay")
    create = commands.add_parser("create")
    create.add_argument("path", type=Path)
    create.add_argument("--case", choices=CASES, default="before")
    create.add_argument("--force", action="store_true", help="replace an existing fixture file")
    inspect = commands.add_parser("inspect")
    inspect.add_argument("path", type=Path)
    comparison = commands.add_parser("compare")
    comparison.add_argument("before", type=Path)
    comparison.add_argument("after", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            data = make_case(args.case)
            args.path.parent.mkdir(parents=True, exist_ok=True)
            with args.path.open("wb" if args.force else "xb") as target:
                target.write(data)
            print(f"created {ascii(str(args.path))} bytes={len(data)}")
            print(f"sha256={hashlib.sha256(data).hexdigest()}")
        elif args.command == "inspect":
            show(decode(read_file(args.path)))
        elif args.command == "compare":
            before, after = decode(read_file(args.before)), decode(read_file(args.after))
            print("\n".join(compare(before, after).lines()))
        elif args.command == "replay":
            monitor = ReplayMonitor()
            for at_ms, data in replay_events():
                print(f"{at_ms:3d} ms {monitor.observe(at_ms, data)}")
        else:
            before = decode(make_case("before"))
            show(before)
            print("\n".join(compare(before, decode(make_case("after"))).lines()))
        return 0
    except FileExistsError:
        print("error: output exists; choose another path or pass --force", file=sys.stderr)
    except (DecodeError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
