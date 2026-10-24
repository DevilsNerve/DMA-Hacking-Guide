#!/usr/bin/env python3
"""A bounded reader for the book's invented byte-image format, not live memory."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import math
from pathlib import Path
import re
import struct
import sys

MAX_IMAGE = 1024 * 1024
MAX_ITEMS = 16
MAX_PATTERN = 128
MAX_MATCHES = 1024
DEFAULT_PATTERN = "44 4D 41 4C ?? ?? 20 00"
FAULTS = (
    "null-root", "bad-magic", "bad-version", "bad-size", "bad-count",
    "odd-sequence", "mismatched-sequence", "nan-health", "dangling-items",
    "truncated",
)


class LabError(ValueError):
    """An input violates the declared fixture contract."""


def default_base(bits: int) -> int:
    if bits not in (32, 64):
        raise LabError("pointer bits must be 32 or 64")
    return 0x00400000 if bits == 32 else 0x140000000


@dataclass(frozen=True)
class Image:
    data: bytes
    base: int
    bits: int = 64

    def __post_init__(self) -> None:
        default_base(self.bits)
        if not 0 <= self.base < (1 << self.bits):
            raise LabError("base outside target address space")
        if len(self.data) > MAX_IMAGE:
            raise LabError("image exceeds 1 MiB teaching limit")
        if self.base + len(self.data) > (1 << self.bits):
            raise LabError("image exceeds target address space")

    def read_exact(self, address: int, size: int) -> bytes:
        if size < 0 or size > MAX_IMAGE:
            raise LabError("invalid read size")
        if not 0 <= address < (1 << self.bits):
            raise LabError("address outside target address space")
        if address + size > (1 << self.bits):
            raise LabError("read exceeds target address space")
        offset = address - self.base
        if offset < 0 or offset > len(self.data) or size > len(self.data) - offset:
            raise LabError(f"unavailable range: address=0x{address:X} size={size}")
        return self.data[offset:offset + size]

    def pointer(self, address: int) -> int:
        return int.from_bytes(self.read_exact(address, self.bits // 8), "little")


@dataclass(frozen=True)
class Observation:
    address: int
    sequence: int
    health: float
    items: tuple[int, ...]


def decode(image: Image) -> Observation:
    root = image.pointer(image.base + 0x40)
    if root == 0:
        raise LabError("null root pointer")
    record = image.read_exact(root, 32)
    magic, version, size = struct.unpack_from("<4sHH", record)
    if magic != b"DMAL":
        raise LabError("record magic mismatch")
    if version != 1:
        raise LabError(f"unsupported record version: {version}")
    if size != 32:
        raise LabError(f"record size mismatch: {size}")
    start, health, count = struct.unpack_from("<IfI", record, 8)
    end = struct.unpack_from("<I", record, 28)[0]
    if start & 1 or start != end:
        raise LabError("inconsistent sequence: require equal even markers")
    if not math.isfinite(health) or not 0 <= health <= 100:
        raise LabError("invalid health: require finite value from 0 through 100")
    if count > MAX_ITEMS:
        raise LabError(f"item count exceeds limit {MAX_ITEMS}: {count}")
    width = image.bits // 8
    pointer = int.from_bytes(record[20:20 + width], "little")
    if count and not pointer:
        raise LabError("null item pointer for nonempty list")
    payload = image.read_exact(pointer, count * 2) if count else b""
    items = struct.unpack(f"<{count}H", payload) if count else ()
    return Observation(root, start, health, items)


def create_fixture(bits: int = 64, fault: str | None = None) -> Image:
    base = default_base(bits)
    if fault is not None and fault not in FAULTS:
        raise LabError(f"unknown fault: {fault}")
    width = bits // 8
    data = bytearray(512)
    data[0x40:0x40 + width] = (base + 0x100).to_bytes(width, "little")
    struct.pack_into("<4sHHIfI", data, 0x100, b"DMAL", 1, 32, 2, 87.5, 3)
    data[0x114:0x114 + width] = (base + 0x180).to_bytes(width, "little")
    struct.pack_into("<I", data, 0x11C, 2)
    struct.pack_into("<3H", data, 0x180, 10, 20, 30)
    if fault == "null-root":
        data[0x40:0x40 + width] = bytes(width)
    elif fault == "bad-magic":
        data[0x100:0x104] = b"NOPE"
    elif fault == "bad-version":
        struct.pack_into("<H", data, 0x104, 2)
    elif fault == "bad-size":
        struct.pack_into("<H", data, 0x106, 64)
    elif fault == "bad-count":
        struct.pack_into("<I", data, 0x110, MAX_ITEMS + 1)
    elif fault == "odd-sequence":
        struct.pack_into("<I", data, 0x108, 3)
        struct.pack_into("<I", data, 0x11C, 3)
    elif fault == "mismatched-sequence":
        struct.pack_into("<I", data, 0x11C, 4)
    elif fault == "nan-health":
        struct.pack_into("<f", data, 0x10C, float("nan"))
    elif fault == "dangling-items":
        data[0x114:0x114 + width] = (base + 0x300).to_bytes(width, "little")
    elif fault == "truncated":
        del data[0x182:]
    return Image(bytes(data), base, bits)


def parse_pattern(pattern: str) -> tuple[int | None, ...]:
    tokens = pattern.split()
    if not 1 <= len(tokens) <= MAX_PATTERN:
        raise LabError(f"pattern must contain 1 through {MAX_PATTERN} bytes")
    result = []
    for token in tokens:
        if token in ("?", "??"):
            result.append(None)
        elif re.fullmatch(r"[0-9a-fA-F]{2}", token):
            result.append(int(token, 16))
        else:
            raise LabError(f"invalid pattern token: {token!r}")
    if all(value is None for value in result):
        raise LabError("pattern must contain at least one fixed byte")
    return tuple(result)


def find_pattern(data: bytes, pattern: str, chunk_size: int = 64) -> list[int]:
    """Scan one contiguous, available image; return offsets, not virtual addresses."""
    needle = parse_pattern(pattern)
    if not 1 <= chunk_size <= MAX_IMAGE:
        raise LabError("chunk size must be from 1 through 1048576")
    if len(data) > MAX_IMAGE:
        raise LabError("image exceeds 1 MiB teaching limit")
    matches: list[int] = []
    tail = b""
    for start in range(0, len(data), chunk_size):
        window = tail + data[start:start + chunk_size]
        window_base = start - len(tail)
        for offset in range(len(window) - len(needle) + 1):
            absolute = window_base + offset
            # A match ending before this chunk was already reported.
            if absolute + len(needle) <= start:
                continue
            if all(value is None or value == window[offset + i]
                   for i, value in enumerate(needle)):
                if len(matches) == MAX_MATCHES:
                    raise LabError(f"match count exceeds limit {MAX_MATCHES}")
                matches.append(absolute)
        tail = window[-(len(needle) - 1):] if len(needle) > 1 else b""
    return matches


def load_image(path: Path, bits: int) -> Image:
    # Bound the read itself, rather than trusting a prior stat of a changing file.
    with path.open("rb") as source:
        data = source.read(MAX_IMAGE + 1)
    return Image(data, default_base(bits), bits)


def show(image: Image) -> None:
    result = decode(image)
    print(f"pointer_bits={image.bits} base=0x{image.base:X}")
    print(f"record=0x{result.address:X} sequence={result.sequence}")
    print(f"health={result.health:g} items={list(result.items)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("demo", "create", "inspect", "scan"):
        child = commands.add_parser(name)
        child.add_argument("--bits", type=int, choices=(32, 64), default=64)
        if name != "demo":
            child.add_argument("path", type=Path)
        if name == "create":
            child.add_argument("--fault", choices=FAULTS)
            child.add_argument("--force", action="store_true", help="replace an existing fixture file")
        if name == "scan":
            child.add_argument("--pattern", default=DEFAULT_PATTERN)
            child.add_argument("--chunk-size", type=int, default=64)
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            image = create_fixture(args.bits, args.fault)
            args.path.parent.mkdir(parents=True, exist_ok=True)
            with args.path.open("wb" if args.force else "xb") as output:
                output.write(image.data)
            print(f"created {args.path} ({len(image.data)} bytes, {args.bits}-bit)")
        elif args.command == "scan":
            image = load_image(args.path, args.bits)
            matches = [f"0x{image.base + n:X}" for n in find_pattern(image.data, args.pattern, args.chunk_size)]
            print(f"signature_matches={matches}")
        else:
            image = create_fixture(args.bits) if args.command == "demo" else load_image(args.path, args.bits)
            show(image)
            if args.command == "demo":
                matches = [f"0x{image.base + n:X}" for n in find_pattern(image.data, DEFAULT_PATTERN)]
                print(f"signature_matches={matches}")
        return 0
    except FileExistsError:
        print("error: output exists; choose another path or pass --force", file=sys.stderr)
    except (LabError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
