from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .maze import Maze, Position
from .output import write_maze
from .validation import valid_endpoint
from .view_state import MazeWithPath, ViewState

MazeFactory = Callable[[], Maze]
Display = Callable[[ViewState], None]


@dataclass(frozen=True)
class MazeApplication:
    """Connect maze construction, persistence, and a presentation strategy."""

    generate: MazeFactory
    display: Display
    entry: Position
    exit_: Position
    output_file: str | Path

    def _generate(self) -> MazeWithPath:
        """Generate a maze and return the path persisted with it."""
        maze = self.generate()

        if not valid_endpoint(maze, self.entry):
            raise ValueError(f"Invalid ENTRY: {self.entry}")

        if not valid_endpoint(maze, self.exit_):
            raise ValueError(f"Invalid EXIT: {self.exit_}")

        path = write_maze(maze, self.entry, self.exit_, self.output_file)

        return maze, path

    def build_state(self) -> ViewState:
        """Create display state around a freshly generated maze."""
        maze, path = self._generate()
        return ViewState(
            maze=maze,
            entry=self.entry,
            exit_=self.exit_,
            generate=self._generate,
            path=path,
        )

    def run(self) -> None:
        """Build the initial state and hand control to the display."""
        self.display(self.build_state())
