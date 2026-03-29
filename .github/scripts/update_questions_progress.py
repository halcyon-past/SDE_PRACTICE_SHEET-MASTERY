#!/usr/bin/env python3
"""Scan Questions, track changes, and regenerate README progress sections."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS_DIR = ROOT / "Questions"
README_PATH = ROOT / "README.md"
TRACKER_PATH = ROOT / ".github" / "tracker" / "questions_tracker.json"

STANDARD_PATTERN = re.compile(r"^Leetcode_(\d+)\.py$")
BONUS_PATTERN = re.compile(r"^Leetcode_Bonus_(\d+)\.py$")
WHY_PLACEHOLDER = "TODO: Add why it matters."

SNAPSHOT_START = "<!-- AUTO:PROJECT_SNAPSHOT:START -->"
SNAPSHOT_END = "<!-- AUTO:PROJECT_SNAPSHOT:END -->"
PATTERN_START = "<!-- AUTO:PATTERN_COVERAGE:START -->"
PATTERN_END = "<!-- AUTO:PATTERN_COVERAGE:END -->"
SOLVED_START = "<!-- AUTO:SOLVED_PROBLEMS:START -->"
SOLVED_END = "<!-- AUTO:SOLVED_PROBLEMS:END -->"


@dataclass(frozen=True)
class QuestionEntry:
    topic: str
    file_name: str
    number: int
    is_bonus: bool

    @property
    def relative_path(self) -> str:
        return f"Questions/{self.topic}/{self.file_name}"


def load_leetcode_title_map() -> Dict[int, str]:
    """Fetch all LeetCode problem titles keyed by frontend question id."""
    url = "https://leetcode.com/api/problems/all/"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return {}

    title_map: Dict[int, str] = {}
    for item in payload.get("stat_status_pairs", []):
        stat = item.get("stat", {})
        frontend_id = str(stat.get("frontend_question_id", "")).strip()
        if frontend_id.isdigit():
            title_map[int(frontend_id)] = stat.get("question__title", "").strip()
    return title_map


def scan_questions() -> List[QuestionEntry]:
    entries: List[QuestionEntry] = []
    if not QUESTIONS_DIR.exists():
        return entries

    for topic_dir in sorted(path for path in QUESTIONS_DIR.iterdir() if path.is_dir()):
        topic = topic_dir.name
        for py_file in sorted(topic_dir.glob("*.py")):
            match = BONUS_PATTERN.match(py_file.name)
            if match:
                entries.append(
                    QuestionEntry(
                        topic=topic,
                        file_name=py_file.name,
                        number=int(match.group(1)),
                        is_bonus=True,
                    )
                )
                continue

            match = STANDARD_PATTERN.match(py_file.name)
            if match:
                entries.append(
                    QuestionEntry(
                        topic=topic,
                        file_name=py_file.name,
                        number=int(match.group(1)),
                        is_bonus=False,
                    )
                )

    return sorted(entries, key=lambda e: (e.is_bonus, e.topic.lower(), e.number, e.file_name.lower()))


def extract_bonus_why_map(existing_readme: str) -> Dict[int, str]:
    """Preserve manually edited bonus 'Why it matters' text by question id."""
    why_map: Dict[int, str] = {}
    in_bonus_table = False

    for line in existing_readme.splitlines():
        stripped = line.strip()
        if stripped.startswith("### Bonus Foundations"):
            in_bonus_table = True
            continue

        if in_bonus_table and stripped.startswith("---"):
            break

        if not in_bonus_table or not stripped.startswith("|"):
            continue

        parts = [part.strip() for part in stripped.split("|")]
        if len(parts) < 6:
            continue

        problem_cell = parts[2]
        why_cell = parts[3]
        match = re.search(r"LeetCode\s+(\d+)", problem_cell, flags=re.IGNORECASE)
        if not match:
            continue

        qid = int(match.group(1))
        if why_cell and why_cell != "Why it matters":
            why_map[qid] = why_cell

    return why_map


def quote_path(path: str) -> str:
    return urllib.parse.quote(path, safe="/")


def replace_between_markers(text: str, start_marker: str, end_marker: str, content: str) -> str:
    escaped_start = re.escape(start_marker)
    escaped_end = re.escape(end_marker)
    pattern = re.compile(f"{escaped_start}\\n.*?\\n{escaped_end}", flags=re.DOTALL)
    replacement = f"{start_marker}\\n{content}\\n{end_marker}"
    return pattern.sub(replacement, text)


def ensure_markers_after_heading(
    text: str,
    heading: str,
    next_heading: str,
    start_marker: str,
    end_marker: str,
) -> str:
    if start_marker in text and end_marker in text:
        return text

    heading_match = re.search(rf"^##\s+{re.escape(heading)}\s*$", text, flags=re.MULTILINE)
    if not heading_match:
        return text

    block_start = heading_match.end()
    next_match = re.search(rf"^##\s+{re.escape(next_heading)}\s*$", text[block_start:], flags=re.MULTILINE)
    if next_match:
        block_end = block_start + next_match.start()
    else:
        block_end = len(text)

    block_body = text[block_start:block_end]
    stripped_body = block_body.strip("\n")
    wrapped = f"\n\n{start_marker}\n{stripped_body}\n{end_marker}\n\n"

    return text[:block_start] + wrapped + text[block_end:]


def ensure_solved_markers(text: str) -> str:
    if SOLVED_START in text and SOLVED_END in text:
        return text

    heading_match = re.search(r"^##\s+Solved\s+Problems\s*$", text, flags=re.MULTILINE)
    if not heading_match:
        return text

    block_start = heading_match.end()
    footer_match = re.search(r"^---\s*$", text[block_start:], flags=re.MULTILINE)
    if footer_match:
        block_end = block_start + footer_match.start()
    else:
        block_end = len(text)

    block_body = text[block_start:block_end]
    stripped_body = block_body.strip("\n")
    wrapped = f"\n\n{SOLVED_START}\n{stripped_body}\n{SOLVED_END}\n\n"

    return text[:block_start] + wrapped + text[block_end:]


def ensure_all_markers(text: str) -> str:
    updated = ensure_markers_after_heading(
        text,
        heading="Project Snapshot",
        next_heading="Pattern Coverage",
        start_marker=SNAPSHOT_START,
        end_marker=SNAPSHOT_END,
    )
    updated = ensure_markers_after_heading(
        updated,
        heading="Pattern Coverage",
        next_heading="Solved Problems",
        start_marker=PATTERN_START,
        end_marker=PATTERN_END,
    )
    updated = ensure_solved_markers(updated)
    return updated


def build_tracker(entries: List[QuestionEntry], title_map: Dict[int, str]) -> dict:
    previous_payload = {}
    if TRACKER_PATH.exists():
        try:
            previous_payload = json.loads(TRACKER_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous_payload = {}

    previous_paths = {
        row.get("relative_path")
        for row in previous_payload.get("questions", [])
        if isinstance(row, dict) and row.get("relative_path")
    }
    current_paths = {entry.relative_path for entry in entries}

    added = sorted(current_paths - previous_paths)
    removed = sorted(previous_paths - current_paths)

    topics = sorted({entry.topic for entry in entries})
    bonus_count = sum(1 for entry in entries if entry.is_bonus)

    tracker_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_questions": len(entries),
            "total_bonus": bonus_count,
            "topic_count": len(topics),
        },
        "topics": topics,
        "changes_since_last_run": {
            "added": added,
            "removed": removed,
        },
        "questions": [
            {
                "topic": entry.topic,
                "file_name": entry.file_name,
                "question_number": entry.number,
                "is_bonus": entry.is_bonus,
                "title": title_map.get(entry.number, ""),
                "relative_path": entry.relative_path,
            }
            for entry in entries
        ],
    }
    return tracker_payload


def build_snapshot_section(entries: List[QuestionEntry]) -> str:
    standard_entries = [entry for entry in entries if not entry.is_bonus]
    topics = sorted({entry.topic for entry in entries})
    per_topic: Dict[str, List[QuestionEntry]] = {topic: [] for topic in topics}
    for entry in standard_entries:
        per_topic[entry.topic].append(entry)

    bonus_count = sum(1 for entry in entries if entry.is_bonus)

    lines: List[str] = []
    lines.append("| Metric | Value |")
    lines.append("|---|---:|")
    lines.append(f"| Total Problems Solved | {len(entries)} |")
    lines.append(f"| Core Patterns Covered | {len(topics)} |")
    lines.append(f"| Bonus Problems | {bonus_count} |")
    lines.append("")
    lines.append("```mermaid")
    lines.append("pie title Solved Problem Distribution")
    for topic in topics:
        topic_count = len(per_topic.get(topic, []))
        if topic_count > 0:
            lines.append(f'    "{topic}" : {topic_count}')
    if bonus_count > 0:
        lines.append(f'    "Bonus" : {bonus_count}')
    lines.append("```")

    return "\n".join(lines)


def build_pattern_coverage_section(entries: List[QuestionEntry]) -> str:
    topics = sorted({entry.topic for entry in entries})
    bonus_count = sum(1 for entry in entries if entry.is_bonus)

    lines: List[str] = []
    lines.append("```mermaid")
    lines.append("graph LR")
    lines.append("    A[Practice Repository]")
    for idx, topic in enumerate(topics, start=1):
        node = f"T{idx}"
        lines.append(f"    A --> {node}[{topic}]")
    if bonus_count > 0:
        lines.append("    A --> B0[Bonus Foundations]")
    lines.append("```")

    return "\n".join(lines)


def build_solved_problems_section(entries: List[QuestionEntry], title_map: Dict[int, str], existing_readme: str) -> str:
    bonus_why_map = extract_bonus_why_map(existing_readme)

    standard_entries = [entry for entry in entries if not entry.is_bonus]
    bonus_entries = [entry for entry in entries if entry.is_bonus]
    topics = sorted({entry.topic for entry in entries})

    per_topic: Dict[str, List[QuestionEntry]] = {topic: [] for topic in topics}
    for entry in standard_entries:
        per_topic[entry.topic].append(entry)

    for topic in per_topic:
        per_topic[topic].sort(key=lambda e: (e.number, e.file_name.lower()))

    bonus_entries.sort(key=lambda e: (e.number, e.topic.lower(), e.file_name.lower()))

    lines: List[str] = []
    lines.append("")

    for topic in topics:
        topic_entries = per_topic.get(topic, [])
        if not topic_entries:
            continue

        lines.append(f"### {topic} ({len(topic_entries)})")
        lines.append("")
        lines.append("| # | Problem | File |")
        lines.append("|---:|---|---|")
        for idx, entry in enumerate(topic_entries, start=1):
            title = title_map.get(entry.number, "").strip() or "Unknown Title"
            file_path = quote_path(entry.relative_path)
            lines.append(
                f"| {idx} | LeetCode {entry.number} - {title} | [{entry.file_name}]({file_path}) |"
            )
        lines.append("")

    if bonus_entries:
        lines.append("### Bonus Foundations ({})".format(len(bonus_entries)))
        lines.append("")
        lines.append("This track contains supporting questions that strengthen core techniques used in higher-level pattern problems.")
        lines.append("")
        lines.append("| # | Problem | Why it matters | File |")
        lines.append("|---:|---|---|---|")
        for idx, entry in enumerate(bonus_entries, start=1):
            title = title_map.get(entry.number, "").strip() or "Unknown Title"
            file_path = quote_path(entry.relative_path)
            why_text = bonus_why_map.get(entry.number, WHY_PLACEHOLDER)
            lines.append(
                f"| {idx} | LeetCode {entry.number} - {title} | {why_text} | [{entry.file_name}]({file_path}) |"
            )
        lines.append("")

    return "\n".join(lines).strip("\n")


def update_readme_sections(entries: List[QuestionEntry], title_map: Dict[int, str], existing_readme: str) -> str:
    readme_with_markers = ensure_all_markers(existing_readme)

    snapshot_content = build_snapshot_section(entries)
    pattern_content = build_pattern_coverage_section(entries)
    solved_content = build_solved_problems_section(entries, title_map, readme_with_markers)

    updated = replace_between_markers(
        readme_with_markers,
        SNAPSHOT_START,
        SNAPSHOT_END,
        snapshot_content,
    )
    updated = replace_between_markers(
        updated,
        PATTERN_START,
        PATTERN_END,
        pattern_content,
    )
    updated = replace_between_markers(
        updated,
        SOLVED_START,
        SOLVED_END,
        solved_content,
    )
    return updated


def main() -> int:
    entries = scan_questions()
    title_map = load_leetcode_title_map()
    existing_readme = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""

    tracker = build_tracker(entries, title_map)
    TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRACKER_PATH.write_text(json.dumps(tracker, indent=2) + "\n", encoding="utf-8")

    readme_contents = update_readme_sections(entries, title_map, existing_readme)
    README_PATH.write_text(readme_contents, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
