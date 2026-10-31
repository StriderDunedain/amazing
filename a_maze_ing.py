import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType

from mazegen.algorithms import growing_tree, randomized_prim
from mazegen.application import Display, MazeApplication
from mazegen.config import ConfigError, load_config
from mazegen.display import DEFAULT_DISPLAYS, resolve_display
from mazegen.generator import GenerationAlgorithm, MazeGenerator
from mazegen.pattern import make_42_pattern

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


def main(
    argv: Sequence[str] | None = None,
    displays: Mapping[str, Display] = DEFAULT_DISPLAYS,
) -> int:
    """Load configuration, generate the maze, and run its selected display."""
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
        display = resolve_display(config.display, displays)
        algorithm = resolve_algorithm(config.algorithm)
        pattern = make_42_pattern(config.width, config.height)

        if config_path.resolve() == config.output_file.resolve():
            raise ConfigError("OUTPUT_FILE must not overwrite the configuration file")

        if config.output_file.exists() and config.output_file.is_dir():
            raise ConfigError("OUTPUT_FILE must name a file, not a directory")

        if not pattern:
            print(
                "Error: maze is too small to contain the 42 pattern; "
                "continuing without it",
                file=sys.stderr,
            )
        elif config.entry in pattern:
            raise ConfigError("ENTRY collides with the 42 pattern")
        elif config.exit_ in pattern:
            raise ConfigError("EXIT collides with the 42 pattern")

        generator = MazeGenerator(
            spec=config.generation_spec,
            algorithm=algorithm,
        )

        application = MazeApplication(
            generate=generator.generate,
            display=display,
            entry=config.entry,
            exit_=config.exit_,
            output_file=config.output_file,
        )

        application.run()

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
