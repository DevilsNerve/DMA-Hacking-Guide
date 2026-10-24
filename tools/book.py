#!/usr/bin/env python3
"""Synchronize book navigation and check the repository's Markdown conventions."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {".git", ".venv", "out", "__pycache__"}


@dataclass
class Document:
    anchors: set[str]
    links: list[tuple[int, str]]
    errors: list[str]


class AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.anchors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if value and (name == "id" or tag == "a" and name == "name"):
                self.anchors.append(value)


def prose_lines(text: str) -> tuple[list[str], list[str]]:
    """Remove fenced code while retaining line numbers; reject unfinished fences."""
    result = []
    fence: str | None = None
    length = 0
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence is None and marker:
            fence, length = marker[1][0], len(marker[1])
            result.append("")
        elif fence is not None:
            if marker and marker[1][0] == fence and len(marker[1]) >= length and not marker[2].strip():
                fence = None
            result.append("")
        else:
            result.append(line)
    return result, ["unclosed code fence"] if fence else []


def slug(text: str) -> str:
    text = re.sub(r"<[^>]*>", "", html.unescape(text)).strip().lower()
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    return "".join(char for char in text
                   if char in "_- " or unicodedata.category(char)[0] not in "PS").replace(" ", "-")


def parse_document(text: str) -> Document:
    lines, errors = prose_lines(text)
    anchors: set[str] = set()
    heading_ids: set[str] = set()
    links: list[tuple[int, str]] = []
    references: dict[str, str] = {}
    definitions: set[int] = set()
    for number, line in enumerate(lines, 1):
        definition = re.match(r'^ {0,3}\[([^]]+)\]:\s*(?:<([^>]+)>|(\S+))(?:\s+.*)?$', line)
        if definition:
            key = " ".join(definition[1].lower().split())
            if key in references:
                errors.append(f"line {number}: duplicate reference definition {key}")
            references[key] = definition[2] or definition[3]
            definitions.add(number)
    for number, line in enumerate(lines, 1):
        heading = re.match(r"^ {0,3}#{1,6}\s+(.+?)(?:\s+#+)?\s*$", line)
        if heading:
            base = slug(heading[1])
            identifier = base
            suffix = 0
            while identifier in heading_ids:
                suffix += 1
                identifier = f"{base}-{suffix}"
            heading_ids.add(identifier)
            if identifier in anchors:
                errors.append(f"line {number}: duplicate anchor {identifier}")
            anchors.add(identifier)
        inline_free = re.sub(r"(`+)(.*?)\1", "", line)
        parser = AnchorParser()
        parser.feed(inline_free)
        for identifier in parser.anchors:
            if identifier in anchors:
                errors.append(f"line {number}: duplicate anchor {identifier}")
            anchors.add(identifier)
        if number in definitions:
            continue
        inline = re.compile(r'!?\[[^]\n]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+"[^"]*")?\s*\)')
        for match in inline.finditer(inline_free):
            links.append((number, html.unescape(match[1] or match[2])))
        remaining = inline.sub("", inline_free)
        reference_pattern = re.compile(r"!?\[([^]\n]+)\]\[([^]\n]*)\]")
        for match in reference_pattern.finditer(remaining):
            key = " ".join((match[2] or match[1]).lower().split())
            if key not in references:
                errors.append(f"line {number}: undefined reference {key}")
            else:
                links.append((number, references[key]))
        remaining = reference_pattern.sub("", remaining)
        # Shortcut references resolve only when a matching definition exists.
        for match in re.finditer(r"\[([^]\n]+)\]", remaining):
            key = " ".join(match[1].lower().split())
            if key in references:
                links.append((number, references[key]))
    return Document(anchors, links, errors)


def relative(source: str, target: str) -> str:
    return Path(os.path.relpath(target, Path(source).parent)).as_posix()


def replace_block(text: str, name: str, content: str) -> str:
    start, end = f"<!-- BOOK:{name}:START -->", f"<!-- BOOK:{name}:END -->"
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"expected one pair of {name} markers")
    before, remainder = text.split(start)
    old, after = remainder.split(end)
    return before + start + "\n" + content + "\n" + end + after


def navigation_changes(root: Path) -> dict[Path, str]:
    chapters = json.loads((root / "book.json").read_text(encoding="utf-8"))
    if not isinstance(chapters, list) or not chapters:
        raise ValueError("book.json must contain a nonempty chapter list")
    paths = [chapter["file"] for chapter in chapters]
    if len(set(paths)) != len(paths):
        raise ValueError("duplicate chapter path")
    changes = {}
    table = ["", "| Chapter | What you will learn |", "| --- | --- |"]
    for index, chapter in enumerate(chapters):
        filename, title = chapter["file"], chapter["title"]
        path = (root / filename).resolve()
        if not path.is_relative_to(root.resolve()) or path.suffix.lower() != ".md":
            raise ValueError(f"invalid chapter path: {filename}")
        text = path.read_text(encoding="utf-8")
        if not text.startswith(f"# Chapter {index + 1}: {title}\n"):
            raise ValueError(f"chapter heading does not match manifest: {filename}")
        previous = chapters[index - 1] if index else None
        following = chapters[index + 1] if index + 1 < len(chapters) else None
        pieces = []
        if previous:
            pieces.append(f"[Previous: {previous['title']}]({relative(filename, previous['file'])})")
        pieces.append(f"[Contents]({relative(filename, 'README.MD')}#table-of-contents)")
        if following:
            pieces.append(f"[Next: {following['title']}]({relative(filename, following['file'])})")
        else:
            pieces.append(f"[Practice labs]({relative(filename, 'labs/README.md')})")
        nav = "\n" + " · ".join(pieces) + "\n"
        updated = replace_block(replace_block(text, "NAV", nav), "FOOT", nav)
        if updated != text:
            changes[path] = updated
        table.append(f"| [{index + 1}. {title}]({filename}) | {chapter['description']} |")
    table.append("")
    readme = root / "README.MD"
    original = readme.read_text(encoding="utf-8")
    updated = replace_block(original, "CONTENTS", "\n".join(table))
    if updated != original:
        changes[readme] = updated
    return changes


def check_links(root: Path) -> tuple[list[str], int, int]:
    root = root.resolve()
    paths = sorted(path for path in root.rglob("*")
                   if path.is_file() and path.suffix.lower() == ".md"
                   and not any(part in IGNORED for part in path.relative_to(root).parts))
    documents = {path.resolve(): parse_document(path.read_text(encoding="utf-8")) for path in paths}
    errors = []
    count = 0
    graph: dict[Path, set[Path]] = {path: set() for path in documents}
    for path, document in documents.items():
        label = path.relative_to(root)
        errors.extend(f"{label}: {error}" for error in document.errors)
        for line, destination in document.links:
            parts = urlsplit(destination)
            if parts.scheme or parts.netloc:
                if parts.scheme not in ("https", "http", "mailto"):
                    errors.append(f"{label}:{line}: unsupported link scheme: {destination}")
                continue
            count += 1
            target = (path.parent / unquote(parts.path)).resolve() if parts.path else path
            prefix = f"{label}:{line}: {destination}"
            if not target.is_relative_to(root):
                errors.append(f"{prefix}: path leaves repository")
                continue
            if not target.exists():
                errors.append(f"{prefix}: destination does not exist")
                continue
            if target in documents:
                graph[path].add(target)
            if parts.fragment:
                if target not in documents:
                    errors.append(f"{prefix}: fragment target is not a checked Markdown file")
                elif unquote(parts.fragment) not in documents[target].anchors:
                    errors.append(f"{prefix}: fragment does not exist")
    reached: set[Path] = set()
    pending = [root / "README.MD"]
    while pending:
        path = pending.pop()
        if path not in reached:
            reached.add(path)
            pending.extend(graph.get(path, set()) - reached)
    errors.extend(f"{path.relative_to(root)}: unreachable from README.MD"
                  for path in documents if path not in reached)
    return errors, len(documents), count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("sync", "check"))
    args = parser.parse_args(argv)
    try:
        changes = navigation_changes(ROOT)
        if args.command == "sync":
            for path, content in changes.items():
                path.write_text(content, encoding="utf-8")
            print(f"Updated navigation in {len(changes)} files.")
        elif changes:
            for path in changes:
                print(f"stale navigation: {path.relative_to(ROOT)}", file=sys.stderr)
            print("Run: python tools/book.py sync", file=sys.stderr)
            return 1
        errors, documents, links = check_links(ROOT)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print(f"Book checks passed: {documents} Markdown files, {links} local links; all pages reachable.")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"book check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
