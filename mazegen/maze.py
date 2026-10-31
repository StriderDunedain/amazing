from __future__ import annotations

from collections.abc import Set as AbstractSet
from dataclasses import dataclass, field
from enum import IntFlag
from typing import TypeAlias

Position: TypeAlias = tuple[int, int]


class Directions(IntFlag):
    """Represent closed cardinal walls as composable bit flags."""

    NORTH = 1 << 0
    EAST = 1 << 1
    SOUTH = 1 << 2
    WEST = 1 << 3


D = Directions

ALL_WALLS = D.NORTH | D.EAST | D.SOUTH | D.WEST

WALL_DELTA = {
    (0, -1): (D.NORTH, D.SOUTH),
    (1, 0): (D.EAST, D.WEST),
    (0, 1): (D.SOUTH, D.NORTH),
    (-1, 0): (D.WEST, D.EAST),
}


@dataclass
class Maze:
    """Store maze dimensions, wall bits, and blocked pattern cells."""

    width: int
    height: int
    _cells: list[list[Directions]]
    _blocked: set[Position] = field(default_factory=set)

    def __getitem__(self, pos: Position) -> Directions:
        """Return the closed-wall flags at a position."""
        x, y = pos
        return self._cells[y][x]

    def _set_walls(
        self,
        pos: Position,
        value: Directions,
    ) -> None:
        """Replace wall flags through the builder's mutation boundary."""
        x, y = pos
        self._cells[y][x] = value

    @classmethod
    def create(cls, width: int, height: int) -> Maze:
        """Create a positive-sized maze with every wall closed."""
        if width <= 0 or height <= 0:
            raise ValueError("Maze dimensions must be positive")

        cells = [[ALL_WALLS for _ in range(width)] for _ in range(height)]
        return cls(width, height, cells)

    @property
    def blocked_len(self) -> int:
        """Return the blocked-cell count without copying the collection."""
        return len(self._blocked)

    @property
    def blocked(self) -> AbstractSet[Position]:
        """Return an immutable snapshot of blocked positions."""
        return frozenset(self._blocked)

    def is_blocked(self, pos: Position) -> bool:
        """Return whether a position belongs to the blocked pattern."""
        return pos in self._blocked

    def _update_blocked(self, positions: set[Position]) -> None:
        """Add blocked positions through the builder's mutation boundary."""
        self._blocked.update(positions)

    def in_bounds(self, pos: Position) -> bool:
        """Return whether a position lies inside the maze."""
        x, y = pos

        return 0 <= x < self.width and 0 <= y < self.height

    def connected_neighbors(self, pos: Position) -> list[Position]:
        """Return neighbors connected through open shared walls."""
        x, y = pos
        connected: list[Position] = []

        for (dx, dy), (wall, _) in WALL_DELTA.items():
            neighbor = (x + dx, y + dy)

            if not self.in_bounds(neighbor) or self.is_blocked(neighbor):
                continue

            if not self[x, y] & wall:
                connected.append(neighbor)

        return connected

    def closed_neighbors(self, pos: Position) -> list[Position]:
        """Return adjacent corridor cells separated by a closed wall."""
        x, y = pos
        closed: list[Position] = []

        for (dx, dy), (wall, _) in WALL_DELTA.items():
            neighbor = (x + dx, y + dy)

            if not self.in_bounds(neighbor) or self.is_blocked(neighbor):
                continue

            if self[x, y] & wall:
                closed.append(neighbor)

        return closed

    def candidates(self, pos: Position) -> list[Position]:
        """Return adjacent in-bounds positions that are not blocked."""
        x, y = pos

        candidates = [(x + dx, y + dy) for dx, dy in WALL_DELTA]

        return [
            candidate
            for candidate in candidates
            if self.in_bounds(candidate) and not self.is_blocked(candidate)
        ]
