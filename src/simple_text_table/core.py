"""Render aligned text tables that survive wide characters.

Python's ``str`` type counts code points, not display cells.  A CJK
ideograph occupies two terminal cells but has length one, so a naive
``ljust`` pads it with one space too many.  This module measures display
width by code point: East Asian Wide and Fullwidth code points count as
2, combining marks count as 0, and everything else counts as 1.

That is a deliberate simplification.  It is not a full UAX #11
implementation (no emoji sequences, no variation selectors) but it is
correct for the common cases -- CJK, Hangul, combining accents -- and it
has no dependencies.  If you need grapheme clusters, reach for a real
library.
"""

from __future__ import annotations

import unicodedata
from typing import Iterable, List, Sequence, Tuple

__all__ = ["Column", "Table", "render"]


class Column:
    """A named column with an alignment.

    ``align`` is one of ``"left"``, ``"right"`` or ``"center"``.  The
    value is stored as-is; validation happens at render time so that a
    Column can be built before its legal values are known.
    """

    __slots__ = ("header", "align")

    def __init__(self, header: str, align: str = "left") -> None:
        self.header = header
        self.align = align

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Column({self.header!r}, align={self.align!r})"


def _is_wide(ch: str) -> bool:
    """Return True if *ch* occupies two terminal cells.

    We look at the East Asian Width property directly rather than
    hard-coding ranges, because the property table ships with the
    interpreter and stays current with Unicode releases.
    """
    return unicodedata.east_asian_width(ch) in ("W", "F")


def _is_zero_width(ch: str) -> bool:
    """Return True if *ch* occupies no terminal cells.

    Combining marks (``Mn``, ``Me``) and the zero-width space are the
    cases that actually show up in text tables.  Control characters are
    left alone; they are a caller error and we do not silently hide them.
    """
    if ch == "\u200b":
        return True
    return unicodedata.category(ch) in ("Mn", "Me")


def display_width(text: str) -> int:
    """Return the number of terminal cells *text* occupies."""
    total = 0
    for ch in text:
        if _is_zero_width(ch):
            continue
        total += 2 if _is_wide(ch) else 1
    return total


def _pad(text: str, width: int, align: str) -> str:
    """Pad *text* to *width* display cells according to *align*."""
    gap = width - display_width(text)
    if gap <= 0:
        return text
    if align == "left":
        return text + " " * gap
    if align == "right":
        return " " * gap + text
    if align == "center":
        left = gap // 2
        right = gap - left
        return " " * left + text + " " * right
    raise ValueError(f"unknown alignment: {align!r}")


class Table:
    """A collection of columns and rows that can render to a string.

    The table is built up in memory.  Rows shorter than the column list
    are padded with empty strings; rows longer than the column list raise
    ``ValueError`` at render time, because silently dropping data is
    worse than a loud failure.
    """

    def __init__(self, columns: Sequence[Column]) -> None:
        self.columns: List[Column] = list(columns)
        self.rows: List[Tuple[str, ...]] = []

    def add_row(self, *cells: str) -> "Table":
        """Append a row.  Returns ``self`` so calls can be chained."""
        if len(cells) > len(self.columns):
            raise ValueError(
                f"row has {len(cells)} cells but table has {len(self.columns)} columns"
            )
        self.rows.append(tuple(str(c) for c in cells))
        return self

    def _widths(self) -> List[int]:
        widths = [display_width(col.header) for col in self.columns]
        for row in self.rows:
            for i, cell in enumerate(row):
                w = display_width(cell)
                if w > widths[i]:
                    widths[i] = w
        return widths

    def render(self) -> str:
        """Return the table as a single string with a trailing newline."""
        widths = self._widths()
        lines: List[str] = []

        header_cells = [
            _pad(col.header, widths[i], col.align)
            for i, col in enumerate(self.columns)
        ]
        lines.append(" | ".join(header_cells))
        lines.append("-+-".join("-" * w for w in widths))

        for row in self.rows:
            cells = list(row) + [""] * (len(self.columns) - len(row))
            padded = [
                _pad(cells[i], widths[i], self.columns[i].align)
                for i in range(len(self.columns))
            ]
            lines.append(" | ".join(padded))

        return "\n".join(lines) + "\n"


def render(columns: Iterable[Column], rows: Iterable[Sequence[str]]) -> str:
    """Convenience wrapper: build a Table and render it in one call."""
    table = Table(list(columns))
    for row in rows:
        table.add_row(*row)
    return table.render()
