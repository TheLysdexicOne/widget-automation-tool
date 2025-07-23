from pathlib import Path
import sys
import collections


def count_lines(filename):
    with open(filename, "r") as file:
        in_docstring = False
        lines = 0
        for line in file:
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_docstring = not in_docstring
                continue
            if not in_docstring and not stripped.startswith("#"):
                lines += 1
        return lines


nlines = []
for filename in Path(sys.argv[1]).glob("**/*.py"):
    if filename.is_file():
        nlines.append(count_lines(filename))

if nlines:
    print(
        f"    Average = {sum(nlines) / len(nlines):.1f}.  Min = {min(nlines)}.  Max = {max(nlines)} - {len(nlines)} files total"
    )
else:
    print("No Python files found.")

BINSIZE = 50
bins = collections.Counter(lines // BINSIZE for lines in nlines)
for bin in range(1 + max(nlines, default=0) // BINSIZE):
    num = bins.get(bin, 0)
    prop = num / len(nlines) if nlines else 0
    bars = "#" * int(50 * prop)
    print(
        f"    {bin * BINSIZE:3}-{((bin + 1) * BINSIZE) - 1:3}: {bars:60}  {num:3}: {prop * 100:.2f}% "
    )
