from collections.abc import Callable
from dataclasses import dataclass

from .colors import PALETTE
from .maze import Maze, Position

DEFAULT_WALL_COLOR = 0  # white
DEFAULT_PATTERN_COLOR = 6  # cyan
DEFAULT_PATH_COLOR = 3  # yellow


@dataclass
class ViewState:
    """Hold maze data and interactive presentation preferences."""

    maze: Maze
    entry: Position
    exit_: Position
    path: list[Position]
    regenerate_maze: Callable[[], tuple[Maze, list[Position]]] | None = None

    show_path: bool = False
    wall_color: int = DEFAULT_WALL_COLOR
    pattern_color: int = DEFAULT_PATTERN_COLOR
    path_color: int = DEFAULT_PATH_COLOR

    def regenerate(self) -> None:
        """Replace the maze and its already-calculated output path."""
        if self.regenerate_maze is not None:
            self.maze, self.path = self.regenerate_maze()

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
