from collections.abc import Callable
from dataclasses import dataclass

from .colors import PALETTE
from .maze import Maze, Position

MazeWithPath = tuple[Maze, list[Position]]


@dataclass
class ViewState:
    """Hold maze data and interactive presentation preferences."""

    maze: Maze
    entry: Position
    exit_: Position
    generate: Callable[[], MazeWithPath]
    path: list[Position]

    show_path: bool = False
    wall_color: int = 0
    pattern_color: int = 6
    path_color: int = 3

    def regenerate(self) -> None:
        """Replace the maze and its already-calculated output path."""
        self.maze, self.path = self.generate()

    def toggle_path(self) -> None:
        """Toggle shortest-path visibility."""
        self.show_path = not self.show_path

    def cycle_wall_color(self) -> None:
        """Advance to the next wall color."""
        self.wall_color = (self.wall_color + 1) % len(PALETTE)

    def cycle_pattern_color(self) -> None:
        """Advance to the next blocked-pattern color."""
        self.pattern_color = (self.pattern_color + 1) % len(PALETTE)

    def cycle_path_color(self) -> None:
        """Advance to the next path color."""
        self.path_color = (self.path_color + 1) % len(PALETTE)
