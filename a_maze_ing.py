import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType

from mazegen.algorithms import growing_tree, randomized_prim
from mazegen.ascii_view import run_ascii
from mazegen.config import ConfigError, load_config
from mazegen.generator import GenerationAlgorithm, MazeGenerator

DEFAULT_ALGORITHMS: Mapping[str, GenerationAlgorithm] = MappingProxyType(
    {
        "growing_tree": growing_tree,
        "randomized_prim": randomized_prim,
    },
)


def resolve_algorithm(name: str) -> GenerationAlgorithm:
    """Resolve a configured generation algorithm by name."""
    try:
        return DEFAULT_ALGORITHMS[name.lower()]
    except KeyError as error:
        available = ", ".join(sorted(DEFAULT_ALGORITHMS))
        raise ValueError(
            f"Unknown generation algorithm: {name!r}; "
            f"choose one of: {available}",
        ) from error


def main(argv: Sequence[str] | None = None) -> int:
    """Load configuration, generate the maze, and run the ASCII view."""
    arguments = sys.argv if argv is None else argv

    if len(arguments) != 2:
        print(
            f"Usage: {arguments[0] if arguments else 'a_maze_ing.py'} config.txt",
            file=sys.stderr,
        )
        return 1

    try:
        config_path = Path(arguments[1])
        config = load_config(config_path)
        algorithm = resolve_algorithm(config.algorithm)

        if config_path.resolve() == config.output_file.resolve():
            raise ConfigError("OUTPUT_FILE must not overwrite the configuration file")

        if config.output_file.exists() and config.output_file.is_dir():
            raise ConfigError("OUTPUT_FILE must name a file, not a directory")

        generator = MazeGenerator(
            spec=config.generation_spec,
            algorithm=algorithm,
        )

        state = generator.build_state(
            entry=config.entry,
            exit_=config.exit_,
            output_file=config.output_file,
        )
        run_ascii(state)

    except MemoryError:
        print(
            "Error: not enough memory for the requested maze dimensions",
            file=sys.stderr,
        )
        return 1
    except (ConfigError, OSError, RuntimeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
