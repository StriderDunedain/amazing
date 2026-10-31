from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DisplayColor:
    """Store a named ANSI display color."""

    name: str
    ansi: str


PALETTE = (
    DisplayColor("white", "\033[97m"),
    DisplayColor("red", "\033[91m"),
    DisplayColor("green", "\033[92m"),
    DisplayColor("yellow", "\033[93m"),
    DisplayColor("blue", "\033[94m"),
    DisplayColor("magenta", "\033[95m"),
    DisplayColor("cyan", "\033[96m"),
)

ANSI_RESET = "\033[0m"


def color(index: int) -> DisplayColor:
    """Return a palette color while wrapping indices cyclically."""
    return PALETTE[index % len(PALETTE)]
