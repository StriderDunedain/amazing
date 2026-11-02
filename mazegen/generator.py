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
from .view_state import MazeWithPath, ViewState

GenerationAlgorithm = Callable[[MazeBuilder, random.Random], None]


@dataclass
class MazeGenerator:
    """Generate reusable perfect or braided maze structures."""

    spec: GenerationSpec
    algorithm: GenerationAlgorithm
    _rng: random.Random = field(
        init=False,
        repr=False,
        compare=False,
    )
    _pattern: set[Position] = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        """Initialize the reproducible sequence used across regenerations."""
        self._rng = random.Random(self.spec.seed)
        self._pattern = make_42_pattern(self.spec.width, self.spec.height)

    def generate(self) -> Maze:
        """Generate and validate one maze using the configured parameters."""
        maze = Maze.create(self.spec.width, self.spec.height)
        builder = MazeBuilder(maze)
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
    ) -> MazeWithPath:
        """Generate a maze, write it, and return its shortest path."""
        maze = self.generate()

        if maze.is_blocked(entry):
            raise ValueError("ENTRY collides with the 42 pattern")
        if not valid_endpoint(maze, entry):
            raise ValueError(f"Invalid ENTRY: {entry}")

        if maze.is_blocked(exit_):
            raise ValueError("EXIT collides with the 42 pattern")
        if not valid_endpoint(maze, exit_):
            raise ValueError(f"Invalid EXIT: {exit_}")

        path = write_maze(maze, entry, exit_, output_file)
        return maze, path

    def build_state(
        self,
        entry: Position,
        exit_: Position,
        output_file: str | Path,
    ) -> ViewState:
        """Create ASCII view state around a freshly written maze."""
        maze, path = self.generate_and_write(entry, exit_, output_file)

        def regenerate() -> MazeWithPath:
            return self.generate_and_write(entry, exit_, output_file)

        return ViewState(
            maze=maze,
            entry=entry,
            exit_=exit_,
            generate=regenerate,
            path=path,
        )

    @staticmethod
    def solution(maze: Maze, entry: Position, exit_: Position) -> list[Position]:
        """Return a shortest entry-to-exit path through a generated maze."""
        return bfs(maze, entry, exit_)
