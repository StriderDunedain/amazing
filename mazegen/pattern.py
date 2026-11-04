import sys

from .maze import Position

PATTERN_42 = (
    "# #  ###",
    "# #    #",
    "###   # ",
    "  #  #  ",
    "  #  ###",
)
PATTERN_WIDTH = len(PATTERN_42[0])
PATTERN_HEIGHT = len(PATTERN_42)

PATTERN_OMITTED_WARNING = (
    "Warning: maze is too small to contain the 42 pattern; continuing without it"
)


def pattern_warning(width: int, height: int) -> str | None:
    """Return the small-maze warning when the 42 pattern cannot fit."""
    if width < PATTERN_WIDTH + 2 or height < PATTERN_HEIGHT + 2:
        return PATTERN_OMITTED_WARNING
    return None


def make_42_pattern(width: int, height: int) -> set[Position]:
    """Return centered closed cells spelling 42 when space permits."""
    # Keep a corridor around the pattern and, in particular, keep (0, 0)
    # available as the generation starting point.
    if warning := pattern_warning(width, height):
        print(warning, file=sys.stderr)
        return set()

    offset_x = (width - PATTERN_WIDTH) // 2
    offset_y = (height - PATTERN_HEIGHT) // 2

    return {
        (offset_x + x, offset_y + y)
        for y, row in enumerate(PATTERN_42)
        for x, char in enumerate(row)
        if char == "#"
    }
