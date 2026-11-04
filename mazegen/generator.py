import random
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .algorithms import bfs, braid
from .builder import MazeBuilder
from .config import GenerationSpec
from .maze import Maze, Position
from .output import write_maze
from .pattern import make_42_pattern
from .validation import valid_endpoint, validate_generated_maze

GenerationAlgorithm = Callable[[MazeBuilder, random.Random], None]


@dataclass
class MazeGenerator:
    """Generate reusable perfect or braided maze structures."""

    spec: GenerationSpec
    algorithm: GenerationAlgorithm
    on_step: Callable[[Maze], None] | None = field(
        default=None,
        repr=False,
        compare=False,
    )
    _rng: random.Random = field(init=False, repr=False, compare=False)
    _pattern: set[Position] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Initialize the reproducible sequence used across regenerations."""
        self._rng = random.Random(self.spec.seed)
        self._pattern = make_42_pattern(self.spec.width, self.spec.height)

    def generate(self) -> Maze:
        """Generate and validate one maze using the configured parameters."""
        maze = Maze.create(self.spec.width, self.spec.height)
        builder = MazeBuilder(maze, self.on_step)
        builder.block_cells(self._pattern)

        self.algorithm(builder, self._rng)

        if not self.spec.perfect:
            braid(builder, self._rng)

        validate_generated_maze(maze, self.spec.perfect)

        return maze

    def generate_and_write(
        self,
        entry: Position,
        exit_: Position,
        output_file: str | Path,
    ) -> tuple[Maze, list[Position]]:
        """Generate a maze, write it, and return its shortest path."""
        maze = self.generate()

        for name, position in (("ENTRY", entry), ("EXIT", exit_)):
            if maze.is_blocked(position):
                raise ValueError(f"{name} collides with the 42 pattern")
            if not valid_endpoint(maze, position):
                raise ValueError(f"Invalid {name}: {position}")

        path = write_maze(maze, entry, exit_, output_file)
        return maze, path

    @staticmethod
    def solution(maze: Maze, entry: Position, exit_: Position) -> list[Position]:
        """Return a shortest entry-to-exit path through a generated maze."""
        return bfs(maze, entry, exit_)
