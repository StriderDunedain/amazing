from __future__ import annotations

from collections.abc import Iterator
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

    def positions(self) -> Iterator[Position]:
        """Iterate over every maze position row by row."""
        return ((x, y) for y in range(self.height) for x in range(self.width))

    def corridors(self) -> Iterator[Position]:
        """Iterate over every non-blocked maze position."""
        return (pos for pos in self.positions() if not self.is_blocked(pos))

    def connected_neighbors(self, pos: Position) -> list[Position]:
        """Return neighbors connected through open shared walls."""
        return self._neighbors_by_wall(pos, closed=False)

    def closed_neighbors(self, pos: Position) -> list[Position]:
        """Return adjacent corridor cells separated by a closed wall."""
        return self._neighbors_by_wall(pos, closed=True)

    def _neighbors_by_wall(
        self,
        pos: Position,
        closed: bool,
    ) -> list[Position]:
        """Return corridor neighbors matching the requested wall state."""
        x, y = pos
        cell = self[pos]
        return [
            neighbor
            for (dx, dy), (wall, _) in WALL_DELTA.items()
            if self.in_bounds(neighbor := (x + dx, y + dy))
            and not self.is_blocked(neighbor)
            and bool(cell & wall) is closed
        ]

    def candidates(self, pos: Position) -> list[Position]:
        """Return adjacent in-bounds positions that are not blocked."""
        x, y = pos
        return [
            neighbor
            for dx, dy in WALL_DELTA
            if self.in_bounds(neighbor := (x + dx, y + dy))
            and not self.is_blocked(neighbor)
        ]
