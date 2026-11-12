"""Check a saved source snapshot and extract Markdown sections for review."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)(?:[ \t]+#+)?[ \t]*$")
CODE_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def split_sections(text: str) -> list[dict[str, object]]:
    """Keep the original text and one-based line ranges for each heading."""
    lines = text.splitlines(keepends=True)
    sections: list[dict[str, object]] = []
    heading_path: list[tuple[int, str]] = []
    start = 0
    fence_character: str | None = None
    fence_length = 0

    def append_section(end: int) -> None:
        content = "".join(lines[start:end])
        if content:
            sections.append({
                "heading_path": [title for _, title in heading_path],
                "start_line": start + 1,
                "end_line": end,
                "text": content,
            })

    for index, line in enumerate(lines):
        stripped_line = line.rstrip("\r\n")
        fence = CODE_FENCE.match(stripped_line)
        if fence:
            marker, suffix = fence.groups()
            if fence_character is None:
                fence_character, fence_length = marker[0], len(marker)
            elif marker[0] == fence_character and len(marker) >= fence_length and not suffix.strip():
                fence_character = None
            continue
        if fence_character:
            continue
        heading = HEADING.match(stripped_line)
        if heading:
            append_section(index)
            level, title = len(heading[1]), heading[2]
            heading_path = [(depth, name) for depth, name in heading_path if depth < level]
            heading_path.append((level, title))
            start = index
    append_section(len(lines))
    return sections


def build_preview(snapshot_path: Path, asset_root: Path) -> dict[str, object]:
    """Verify saved bytes before producing excerpts. This does not approve a source."""
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    for key in ("source_id", "title", "source_version", "license", "license_url", "review_status"):
        if not isinstance(snapshot.get(key), str) or not snapshot[key]:
            raise ValueError(f"Snapshot requires {key}")
    if snapshot["review_status"] not in {"pending", "verified", "rejected"}:
        raise ValueError("Unknown source review status")
    if not isinstance(snapshot.get("files"), list) or not snapshot["files"]:
        raise ValueError("Snapshot requires at least one source file")

    root = asset_root.resolve()
    seen_paths: set[Path] = set()
    sections: list[dict[str, object]] = []
    for source in snapshot["files"]:
        relative_path = Path(source["path"])
        source_path = (root / relative_path).resolve()
        if relative_path.is_absolute() or not source_path.is_relative_to(root):
            raise ValueError("Source path must remain relative to asset_root")
        if source_path in seen_paths:
            raise ValueError("Duplicate source path")
        seen_paths.add(source_path)
        content = source_path.read_bytes()
        if hashlib.sha256(content).hexdigest() != source["sha256"]:
            raise ValueError(f"SHA-256 mismatch: {relative_path}")
        git_header = b"blob " + str(len(content)).encode("ascii") + b"\0"
        if hashlib.sha1(git_header + content).hexdigest() != source["git_blob_sha1"]:
            raise ValueError(f"Git blob hash mismatch: {relative_path}")
        if len(content) != source["size_bytes"]:
            raise ValueError(f"File size mismatch: {relative_path}")
        if relative_path.suffix == ".md":
            for section in split_sections(content.decode("utf-8")):
                sections.append({
                    "source_id": snapshot["source_id"],
                    "source_version": snapshot["source_version"],
                    "source_path": source["path"],
                    "source_url": source["url"],
                    "page": None,
                    **section,
                })
    return {
        "purpose": "source_review",
        "source_id": snapshot["source_id"],
        "title": snapshot["title"],
        "source_version": snapshot["source_version"],
        "review_status": snapshot["review_status"],
        "attribution": {
            "author": snapshot.get("author"),
            "publisher": snapshot.get("publisher"),
            "license": snapshot["license"],
            "license_url": snapshot["license_url"],
            "changes": "Source text split at headings; text preserved without rewriting.",
        },
        "files": snapshot["files"],
        "sections": sections,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        preview = build_preview(args.snapshot, args.asset_root)
        input_paths = {args.snapshot.resolve()}
        input_paths.update((args.asset_root / source["path"]).resolve() for source in preview["files"])
        if args.output.resolve() in input_paths:
            raise ValueError("Output must not overwrite the snapshot or a source file")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(preview, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"Source preview failed: {exc}\n")
    print(f"Checked {len(preview['files'])} files; wrote {len(preview['sections'])} sections to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
