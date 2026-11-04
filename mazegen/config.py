from dataclasses import dataclass
from pathlib import Path

from .maze import Position

REQUIRED_KEYS = {
    "WIDTH",
    "HEIGHT",
    "ENTRY",
    "EXIT",
    "OUTPUT_FILE",
    "PERFECT",
}

OPTIONAL_KEYS = {
    "ALGORITHM",
    "ANIMATION_SPEED",
    "SEED",
}

ALLOWED_KEYS = REQUIRED_KEYS | OPTIONAL_KEYS
DEFAULT_ANIMATION_SPEED = 200


class ConfigError(ValueError):
    """Report invalid configuration syntax or values."""


@dataclass(frozen=True, slots=True)
class GenerationSpec:
    """Describe one reproducible maze-generation sequence."""

    width: int
    height: int
    perfect: bool
    seed: int | None = None


@dataclass(frozen=True)
class Config:
    """Contain validated maze configuration."""

    width: int
    height: int
    entry: Position
    exit_: Position
    output_file: Path
    perfect: bool
    seed: int | None = None
    algorithm: str = "growing_tree"
    animation_speed: int = DEFAULT_ANIMATION_SPEED

    @property
    def generation_spec(self) -> GenerationSpec:
        """Return the subset of configuration used by maze generation."""
        return GenerationSpec(
            width=self.width,
            height=self.height,
            perfect=self.perfect,
            seed=self.seed,
        )


def validate_config(config: Config) -> None:
    """Validate relationships and bounds in converted configuration."""
    if config.width <= 0:
        raise ConfigError("WIDTH must be positive and non-zero")
    if config.height <= 0:
        raise ConfigError("HEIGHT must be positive and non-zero")
    if config.entry == config.exit_:
        raise ConfigError("ENTRY and EXIT must be different")
    if not position_in_bounds(config.entry, config.width, config.height):
        raise ConfigError("ENTRY is outside the maze")
    if not position_in_bounds(config.exit_, config.width, config.height):
        raise ConfigError("EXIT is outside the maze")
    if config.animation_speed <= 0:
        raise ConfigError("ANIMATION_SPEED must be positive and non-zero")


def load_config(path: str | Path) -> Config:
    """Read, convert, and validate a configuration file."""
    try:
        raw = read_config(path)
    except UnicodeError as error:
        raise ConfigError("Configuration file must be valid UTF-8") from error

    config = convert_config(raw)
    validate_config(config)
    return config


def convert_config(raw: dict[str, str]) -> Config:
    """Convert raw configuration strings to typed values."""
    return Config(
        width=parse_int(raw["WIDTH"], "WIDTH"),
        height=parse_int(raw["HEIGHT"], "HEIGHT"),
        entry=parse_position(raw["ENTRY"], "ENTRY"),
        exit_=parse_position(raw["EXIT"], "EXIT"),
        output_file=Path(raw["OUTPUT_FILE"]),
        perfect=parse_bool(raw["PERFECT"], "PERFECT"),
        seed=parse_int(raw["SEED"], "SEED") if "SEED" in raw else None,
        algorithm=raw.get("ALGORITHM", "growing_tree").lower(),
        animation_speed=(
            parse_int(raw["ANIMATION_SPEED"], "ANIMATION_SPEED")
            if "ANIMATION_SPEED" in raw
            else DEFAULT_ANIMATION_SPEED
        ),
    )


def read_config(path: str | Path) -> dict[str, str]:
    """Parse unique allowed key-value pairs from a configuration file."""
    raw: dict[str, str] = {}

    with open(path, encoding="utf-8") as file:
        for line_no, raw_line in enumerate(file, 1):
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                raise ConfigError(f"Line {line_no}: expected KEY=VALUE")

            key, value = map(str.strip, line.split("=", maxsplit=1))

            if not key:
                raise ConfigError(f"Line {line_no}: key must not be empty")

            if key not in ALLOWED_KEYS:
                raise ConfigError(f"Line {line_no}: unknown key {key!r}")

            if key in raw:
                raise ConfigError(f"Line {line_no}: duplicate key {key!r}")

            if not value:
                raise ConfigError(f"Line {line_no}: {key} must not be empty")

            raw[key] = value

    if missing := REQUIRED_KEYS - raw.keys():
        raise ConfigError("Missing keys: " + ", ".join(sorted(missing)))

    return raw


def position_in_bounds(pos: Position, width: int, height: int) -> bool:
    """Return whether a position lies inside the configured dimensions."""
    x, y = pos
    return 0 <= x < width and 0 <= y < height


def parse_int(value: str, key: str) -> int:
    """Parse an integer written with ASCII decimal digits."""
    if not value.isascii() or not value.isdecimal():
        raise ConfigError(f"{key} must contain only ASCII digits (0-9)")

    return int(value)


def parse_position(value: str, key: str = "Coordinate") -> Position:
    """Parse an x,y coordinate pair."""
    parts = value.split(",")

    if len(parts) != 2 or any(not part.strip() for part in parts):
        raise ConfigError(f"{key} must use the format x,y")

    return parse_int(parts[0].strip(), key), parse_int(parts[1].strip(), key)


def parse_bool(value: str, key: str = "Boolean") -> bool:
    """Parse a case-insensitive true or false value."""
    normalized = value.lower()
    if normalized not in {"true", "false"}:
        raise ConfigError(f"{key} must be True or False")
    return normalized == "true"
