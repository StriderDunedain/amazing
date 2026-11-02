import sys

from .maze import Position

PATTERN_42 = (
    "# #  ###",
    "# #    #",
    "###   # ",
    "  #  #  ",
    "  #  ###",
)


def make_42_pattern(width: int, height: int) -> set[Position]:
    """Return centered closed cells spelling 42 when space permits."""
    pattern_width = len(PATTERN_42[0])
    pattern_height = len(PATTERN_42)

    # Keep a corridor around the pattern and, in particular, keep (0, 0)
    # available as the generation starting point.
    if width < pattern_width + 2 or height < pattern_height + 2:
        print(
            "Warning: maze is too small to contain the 42 pattern; "
            "continuing without it",
            file=sys.stderr,
        )
        return set()

    offset_x = (width - pattern_width) // 2
    offset_y = (height - pattern_height) // 2

    blocked = {
        (offset_x + x, offset_y + y)
        for y, row in enumerate(PATTERN_42)
        for x, char in enumerate(row)
        if char == "#"
    }
    return blocked
