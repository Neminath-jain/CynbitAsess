"""Schemas for parsed Git diff structures."""
from typing import Literal

from pydantic import BaseModel, Field


class DiffLine(BaseModel):
    """An individual line inside a diff hunk."""
    origin: Literal["+", "-", " "]
    content: str
    old_line_number: int | None = None
    new_line_number: int | None = None


class DiffHunk(BaseModel):
    """A hunk representing a contiguous patch in a file."""
    header: str
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    lines: list[DiffLine] = Field(default_factory=list)


class FileDiff(BaseModel):
    """Diff summary and hunks for a single file."""
    old_path: str | None = None
    new_path: str | None = None
    is_new_file: bool = False
    is_deleted_file: bool = False
    hunks: list[DiffHunk] = Field(default_factory=list)
    additions: int = 0
    deletions: int = 0

    @property
    def display_path(self) -> str:
        """Return the best available file path."""
        return self.new_path or self.old_path or "unknown_file"

    def get_valid_new_line_numbers(self) -> set[int]:
        """Return all valid target line numbers in the new file."""
        line_numbers: set[int] = set()
        for hunk in self.hunks:
            for line in hunk.lines:
                if line.new_line_number is not None:
                    line_numbers.add(line.new_line_number)
        return line_numbers

    def format_for_analysis(self) -> str:
        """Format the file diff with line numbers for LLM evaluation."""
        lines_out: list[str] = [f"--- File: {self.display_path} ---"]
        for hunk in self.hunks:
            lines_out.append(hunk.header)
            for line in hunk.lines:
                num_prefix = f"L{line.new_line_number:4d}" if line.new_line_number is not None else "     "
                lines_out.append(f"{num_prefix} {line.origin} {line.content}")
        return "\n".join(lines_out)


class ParsedDiff(BaseModel):
    """Root model for an entire parsed pull request diff."""
    files: list[FileDiff] = Field(default_factory=list)
    total_files: int = 0
    total_additions: int = 0
    total_deletions: int = 0
    is_truncated: bool = False

    def find_file(self, path: str) -> FileDiff | None:
        """Look up a file diff by new_path or old_path."""
        for f in self.files:
            if f.new_path == path or f.old_path == path:
                return f
        return None
