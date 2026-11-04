from collections.abc import Callable
from dataclasses import dataclass

from .maze import ALL_WALLS, WALL_DELTA, Maze, Position


@dataclass(frozen=True)
class MazeBuilder:
    """Mutate one fixed maze; frozen prevents rebinding the builder fields."""

    _maze: Maze
    _on_step: Callable[[Maze], None] | None = None

    @property
    def maze(self) -> Maze:
        """Expose the maze as the builder's read-only topology view."""
        return self._maze

    def block_cells(self, positions: set[Position]) -> None:
        """Mark fully closed in-bounds cells as unavailable corridors."""
        invalid = {pos for pos in positions if not self._maze.in_bounds(pos)}
        if invalid:
            raise ValueError(f"Blocked cells outside the maze: {sorted(invalid)}")

        carved = {
            position for position in positions if self._maze[position] != ALL_WALLS
        }
        if carved:
            raise ValueError(f"Cannot block carved cells: {sorted(carved)}")

        self._maze._update_blocked(positions)
        self._notify()

    def open_passage(self, first: Position, second: Position) -> None:
        """Remove the shared wall between two adjacent corridor cells."""
        if not self._maze.in_bounds(first) or not self._maze.in_bounds(second):
            raise ValueError("Passage cells must be inside the maze")

        if self._maze.is_blocked(first) or self._maze.is_blocked(second):
            raise ValueError("Cannot open a passage through a blocked cell")

        x1, y1 = first
        x2, y2 = second

        if (direction := (x2 - x1, y2 - y1)) not in WALL_DELTA:
            raise ValueError("Cells must be adjacent")

        first_wall, second_wall = WALL_DELTA[direction]

        self._maze._set_walls(first, self._maze[first] & ~first_wall)
        self._maze._set_walls(second, self._maze[second] & ~second_wall)
        self._notify()

    def _notify(self) -> None:
        """Report a completed topology mutation when animation is enabled."""
        if self._on_step is not None:
            self._on_step(self._maze)
