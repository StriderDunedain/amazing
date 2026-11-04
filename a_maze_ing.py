import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from mazegen.algorithms import growing_tree, randomized_prim
from mazegen.ascii_view import animate_generation, run_ascii
from mazegen.config import ConfigError, load_config
from mazegen.generator import GenerationAlgorithm, MazeGenerator
from mazegen.maze import Maze, Position
from mazegen.view_state import ViewState

DEFAULT_ALGORITHMS: Mapping[str, GenerationAlgorithm] = {
    "growing_tree": growing_tree,
    "randomized_prim": randomized_prim,
}


def resolve_algorithm(name: str) -> GenerationAlgorithm:
    """Resolve a configured generation algorithm by name."""
    try:
        return DEFAULT_ALGORITHMS[name.lower()]
    except KeyError as error:
        available = ", ".join(sorted(DEFAULT_ALGORITHMS))
        raise ValueError(
            f"Unknown generation algorithm: {name!r}; choose one of: {available}",
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

        if config_path.resolve() == config.output_file.resolve():
            raise ConfigError("OUTPUT_FILE must not overwrite the configuration file")

        if config.output_file.exists() and config.output_file.is_dir():
            raise ConfigError("OUTPUT_FILE must name a file, not a directory")

        def draw_step(maze: Maze) -> None:
            animate_generation(
                maze,
                entry=config.entry,
                exit_=config.exit_,
                cells_per_second=config.animation_speed,
            )

        generator = MazeGenerator(
            spec=config.generation_spec,
            algorithm=resolve_algorithm(config.algorithm),
            on_step=draw_step,
        )

        def regenerate_maze() -> tuple[Maze, list[Position]]:
            return generator.generate_and_write(
                config.entry,
                config.exit_,
                config.output_file,
            )

        maze, path = regenerate_maze()
        run_ascii(
            ViewState(
                maze=maze,
                entry=config.entry,
                exit_=config.exit_,
                path=path,
                regenerate_maze=regenerate_maze,
            ),
        )

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
