#!/usr/bin/env python3
"""Manually verify GitHub Markdown rendering or published fragment destinations."""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import quote, unquote, urlsplit
from urllib.request import Request, urlopen

from book import IGNORED, ROOT, parse_document, prose_lines, slug

REPOSITORY = "DevilsNerve/DMA-Hacking-Guide"


class Rendered(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        attrs = dict(attributes)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])


def markdown_files() -> list[Path]:
    return sorted(path for path in ROOT.rglob("*")
                  if path.is_file() and path.suffix.lower() == ".md"
                  and not any(part in IGNORED for part in path.relative_to(ROOT).parts))


def render_source(path: Path) -> dict:
    source = path.read_text(encoding="utf-8")
    body = json.dumps({"text": source, "mode": "gfm", "context": REPOSITORY})
    result = subprocess.run(["gh", "api", "--method", "POST", "markdown", "--input", "-"],
                            input=body, text=True, encoding="utf-8", capture_output=True,
                            check=True, timeout=45, cwd=ROOT)
    parsed = Rendered()
    parsed.feed(result.stdout)
    expected = Counter(url for _, url in parse_document(source).links)
    actual = Counter(parsed.links)
    errors = [f"rendered link missing: {url}" for url, count in expected.items() if actual[url] < count]
    explicit = Rendered()
    explicit.feed("\n".join(prose_lines(source)[0]))
    errors.extend(f"custom anchor missing: {identifier}" for identifier in explicit.ids
                  if f"user-content-{identifier}" not in parsed.ids)
    output = ROOT / "out/github-render/source" / (str(path.relative_to(ROOT)) + ".html")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.stdout, encoding="utf-8")
    return {"file": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(), "links": len(parsed.links),
            "custom_anchors": len(explicit.ids), "errors": errors}


def published_requirements(paths: list[Path]) -> dict[Path, set[str]]:
    needed: dict[Path, set[str]] = {}
    for path in paths:
        for _, destination in parse_document(path.read_text(encoding="utf-8")).links:
            parts = urlsplit(destination)
            if parts.scheme or parts.netloc or not parts.fragment:
                continue
            target = (path.parent / unquote(parts.path)).resolve() if parts.path else path
            if not target.is_relative_to(ROOT) or target not in paths:
                raise ValueError(f"run the local link checker first: {destination}")
            needed.setdefault(target, set()).add(unquote(parts.fragment))
    return needed


def verify_published(item: tuple[Path, set[str]], commit: str) -> dict:
    path, fragments = item
    relative = path.relative_to(ROOT).as_posix()
    title = path.read_text(encoding="utf-8").splitlines()[0].removeprefix("# ")
    title_id = "user-content-" + slug(title)
    url = f"https://github.com/{REPOSITORY}/blob/{commit}/{quote(relative)}"
    rendered = Rendered()
    attempts = 0
    while attempts < 2:
        attempts += 1
        request = Request(url, headers={"User-Agent": "DMA-Guide-Link-Verification"})
        with urlopen(request, timeout=45) as response:
            body = response.read(8 * 1024 * 1024 + 1)
        if len(body) > 8 * 1024 * 1024:
            raise ValueError(f"published response exceeds inspection limit: {relative}")
        html = body.decode("utf-8")
        rendered = Rendered()
        rendered.feed(html)
        output = ROOT / "out/github-render/published" / commit / (relative + f".attempt-{attempts}.html")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html, encoding="utf-8")
        if title_id in rendered.ids:
            break
        # GitHub can initially serve a file shell before its Markdown is ready.
        # Retry only an absent document, not a rendered document with a bad link.
    errors = []
    if title_id not in rendered.ids:
        errors.append("published Markdown document was not rendered")
    errors.extend(f"published fragment missing: {fragment}" for fragment in sorted(fragments)
                  if fragment not in rendered.ids and "user-content-" + fragment not in rendered.ids)
    return {"file": relative, "fragments": len(fragments), "attempts": attempts, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("source", "published"),
                        help="source renders local Markdown; published checks the clean HEAD commit on GitHub")
    args = parser.parse_args()
    try:
        paths = markdown_files()
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        with ThreadPoolExecutor(max_workers=3) as pool:
            if args.mode == "source":
                results = list(pool.map(render_source, paths))
            else:
                status = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
                if status:
                    raise ValueError("published verification requires a clean working tree matching HEAD")
                needed = published_requirements(paths)
                results = list(pool.map(lambda item: verify_published(item, commit), needed.items()))
        receipt = {"mode": args.mode, "base_commit" if args.mode == "source" else "commit": commit, "results": results}
        output = ROOT / "out/github-render" / f"{args.mode}-report.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        errors = [(row["file"], error) for row in results for error in row["errors"]]
        for path, error in errors:
            print(f"{path}: {error}", file=sys.stderr)
        if args.mode == "source":
            detail = f"{sum(row['links'] for row in results)} links, {sum(row['custom_anchors'] for row in results)} custom anchors"
        else:
            detail = f"{sum(row['fragments'] for row in results)} unique fragment destinations"
        print(f"GitHub {args.mode} check: {len(results)} pages, {detail}, {len(errors)} failures")
        return int(bool(errors))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"GitHub verification failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
