# simple_text_table

Render aligned text tables that survive wide characters.

```python
from simple_text_table import Column, Table, render

table = Table([Column("name"), Column("score", "right")])
table.add_row("alice", "10")
table.add_row("\u4e2d\u6587", "7")
print(table.render(), end="")
```

Output:

```
name | score
-----+------
alice |    10
\u4e2d\u6587 |     7
```

The same table can be built with the one-shot helper:

```python
print(render([Column("k"), Column("v")], [["a", "1"], ["b", "2"]]), end="")
```

## Why this exists

`str.ljust` and friends count code points.  A CJK ideograph is one code
point but two terminal cells, so a table built with `ljust` drifts out of
alignment the moment a wide character appears.  This library measures
display width by code point -- East Asian Wide and Fullwidth count as 2,
combining marks count as 0, everything else counts as 1 -- and pads on
that basis.

The trade-off is scope.  This is not a full UAX #11 implementation.  It
does not handle emoji ZWJ sequences, variation selectors, or other
grapheme-cluster cases.  For the tables that actually show up in logs and
CLIs -- ASCII, CJK, accented Latin -- it is correct and it has no
dependencies.

## The awkward edge

A row longer than the column list raises `ValueError` at `add_row` time.
A row shorter than the column list is padded with empty cells.  That
asymmetry is deliberate: dropping data silently is worse than a loud
failure, but a short row is usually a caller who forgot a trailing empty
field, and refusing it would be needlessly strict.

## API

- `Column(header, align="left")` -- `align` is `"left"`, `"right"` or
  `"center"`.  An unknown value raises `ValueError` when the table is
  rendered.
- `Table(columns)` -- `columns` is a sequence of `Column`.  `add_row(*cells)`
  appends a row and returns the table so calls can be chained.
- `Table.render()` -- returns the table as a string ending in a newline.
- `render(columns, rows)` -- convenience wrapper around the above.

The separator line uses ` | ` between cells and `-+-` between column
rules, so the header, separator and body all line up column for column.

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

