"""Unified Git Diff Parser service.

Parses raw unified diffs into structured file hunks and computes precise line numbers
for new/modified code. Adheres to safety limits to prevent denial of service.
"""
import logging
import re

from app.config import get_settings
from app.schemas.diff import DiffHunk, DiffLine, FileDiff, ParsedDiff

logger = logging.getLogger(__name__)

HUNK_PATTERN = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")
DIFF_GIT_PATTERN = re.compile(r"^diff --git a/(.*) b/(.*)$")


class DiffParserService:
    """Service to parse, validate, and line-map unified Git diffs."""

    def __init__(self, max_chars: int | None = None, max_files: int | None = None) -> None:
        settings = get_settings()
        self.max_chars = max_chars or settings.MAX_DIFF_CHARACTERS
        self.max_files = max_files or settings.MAX_DIFF_FILES

    def parse(self, raw_diff: str) -> ParsedDiff:
        """Parse raw unified diff text into a structured ParsedDiff object."""
        if not raw_diff or not raw_diff.strip():
            return ParsedDiff(files=[], total_files=0, total_additions=0, total_deletions=0)

        is_truncated = False
        effective_diff = raw_diff

        # Character budget guardrail
        if len(raw_diff) > self.max_chars:
            logger.warning("Diff length (%d) exceeded max budget (%d). Truncating.", len(raw_diff), self.max_chars)
            effective_diff = raw_diff[: self.max_chars]
            # Cut at last clean line break
            last_newline = effective_diff.rfind("\n")
            if last_newline != -1:
                effective_diff = effective_diff[:last_newline]
            is_truncated = True

        files: list[FileDiff] = []
        raw_lines = effective_diff.splitlines()

        current_file: FileDiff | None = None
        current_hunk: DiffHunk | None = None
        current_old_line: int = 0
        current_new_line: int = 0

        for line in raw_lines:
            diff_match = DIFF_GIT_PATTERN.match(line)
            if diff_match:
                if len(files) >= self.max_files:
                    is_truncated = True
                    break

                if current_file:
                    self._finalize_file(current_file, current_hunk)
                    files.append(current_file)
                    current_hunk = None

                old_path, new_path = diff_match.group(1), diff_match.group(2)
                current_file = FileDiff(old_path=old_path, new_path=new_path)
                continue

            if current_file is None:
                # Diff began without 'diff --git', fallback initialization
                current_file = FileDiff()

            if line.startswith("new file mode"):
                current_file.is_new_file = True
                continue
            elif line.startswith("deleted file mode"):
                current_file.is_deleted_file = True
                continue
            elif line.startswith("--- "):
                path_part = line[4:].strip()
                if path_part.startswith("a/"):
                    current_file.old_path = path_part[2:]
                elif path_part == "/dev/null":
                    current_file.is_new_file = True
                continue
            elif line.startswith("+++ "):
                path_part = line[4:].strip()
                if path_part.startswith("b/"):
                    current_file.new_path = path_part[2:]
                elif path_part == "/dev/null":
                    current_file.is_deleted_file = True
                continue

            hunk_match = HUNK_PATTERN.match(line)
            if hunk_match:
                if current_hunk:
                    current_file.hunks.append(current_hunk)

                old_start = int(hunk_match.group(1))
                old_lines = int(hunk_match.group(2) or 1)
                new_start = int(hunk_match.group(3))
                new_lines = int(hunk_match.group(4) or 1)

                current_old_line = old_start
                current_new_line = new_start

                current_hunk = DiffHunk(
                    header=line,
                    old_start=old_start,
                    old_lines=old_lines,
                    new_start=new_start,
                    new_lines=new_lines,
                    lines=[],
                )
                continue

            if current_hunk is not None:
                if line.startswith("+"):
                    diff_line = DiffLine(
                        origin="+",
                        content=line[1:],
                        old_line_number=None,
                        new_line_number=current_new_line,
                    )
                    current_hunk.lines.append(diff_line)
                    current_file.additions += 1
                    current_new_line += 1
                elif line.startswith("-"):
                    diff_line = DiffLine(
                        origin="-",
                        content=line[1:],
                        old_line_number=current_old_line,
                        new_line_number=None,
                    )
                    current_hunk.lines.append(diff_line)
                    current_file.deletions += 1
                    current_old_line += 1
                elif line.startswith(" "):
                    diff_line = DiffLine(
                        origin=" ",
                        content=line[1:],
                        old_line_number=current_old_line,
                        new_line_number=current_new_line,
                    )
                    current_hunk.lines.append(diff_line)
                    current_old_line += 1
                    current_new_line += 1
                elif line.startswith("\\ No newline at end of file"):
                    continue

        if current_file:
            self._finalize_file(current_file, current_hunk)
            if len(files) < self.max_files:
                files.append(current_file)
            else:
                is_truncated = True

        total_adds = sum(f.additions for f in files)
        total_dels = sum(f.deletions for f in files)

        return ParsedDiff(
            files=files,
            total_files=len(files),
            total_additions=total_adds,
            total_deletions=total_dels,
            is_truncated=is_truncated,
        )

    def _finalize_file(self, current_file: FileDiff, current_hunk: DiffHunk | None) -> None:
        """Attach trailing hunk to file."""
        if current_hunk:
            current_file.hunks.append(current_hunk)
