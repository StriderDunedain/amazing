from collections.abc import Mapping
from types import MappingProxyType

from .application import Display
from .ascii_view import run_ascii

DEFAULT_DISPLAYS: Mapping[str, Display] = (
    MappingProxyType(
        {
            "ascii": run_ascii,
        },
    )
)


def resolve_display(
    mode: str,
    displays: Mapping[str, Display] = DEFAULT_DISPLAYS,
) -> Display:
    """Resolve a case-insensitive display name from an injected registry."""
    try:
        return displays[mode.lower()]
    except KeyError as error:
        available = ", ".join(sorted(displays))
        raise ValueError(
            f"Unknown display mode: {mode!r}; choose one of: {available}",
        ) from error
