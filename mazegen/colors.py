from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AnsiColor:
    """Store a named ANSI terminal color."""

    name: str
    ansi: str


PALETTE = (
    AnsiColor("white", "\033[97m"),
    AnsiColor("red", "\033[91m"),
    AnsiColor("green", "\033[92m"),
    AnsiColor("yellow", "\033[93m"),
    AnsiColor("blue", "\033[94m"),
    AnsiColor("magenta", "\033[95m"),
    AnsiColor("cyan", "\033[96m"),
)

ANSI_RESET = "\033[0m"


def color(index: int) -> AnsiColor:
    """Return a palette color while wrapping indices cyclically."""
    return PALETTE[index % len(PALETTE)]
