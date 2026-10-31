import random
from collections.abc import Callable
from dataclasses import dataclass, field

from .algorithms import bfs, braid
from .builder import MazeBuilder
from .config import GenerationSpec
from .maze import Maze, Position
from .pattern import make_42_pattern
from .validation import validate_generated_maze

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

    def __post_init__(self) -> None:
        """Initialize the reproducible sequence used across regenerations."""
        self._rng = random.Random(self.spec.seed)

    def generate(self) -> Maze:
        """Generate and validate one maze using the configured parameters."""
        maze = Maze.create(self.spec.width, self.spec.height)
        builder = MazeBuilder(maze)
        builder.block_cells(make_42_pattern(self.spec.width, self.spec.height))

        self.algorithm(builder, self._rng)

        if not self.spec.perfect:
            braid(builder, self._rng)

        validate_generated_maze(maze, self.spec.perfect)

        return maze

    @staticmethod
    def solution(maze: Maze, entry: Position, exit_: Position) -> list[Position]:
        """Return a shortest entry-to-exit path through a generated maze."""
        return bfs(maze, entry, exit_)
