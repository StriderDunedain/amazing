import itertools
import random
from collections import deque

from .builder import MazeBuilder
from .maze import Directions as D
from .maze import Maze, Position

DELTA_TO_DIRECTION = {
    (0, -1): "N",
    (1, 0): "E",
    (0, 1): "S",
    (-1, 0): "W",
}

EAST_MASK = int(D.EAST)
SOUTH_MASK = int(D.SOUTH)


def growing_tree(builder: MazeBuilder, rng: random.Random) -> None:
    """Carve a perfect maze with the last-cell Growing Tree strategy."""
    maze = builder.maze

    start = (0, 0)

    if maze.is_blocked(start):
        raise ValueError("Generation starting cell is blocked")

    visited: set[Position] = {start}
    active: list[Position] = [start]

    while active:
        current = active[-1]

        candidates = [
            candidate
            for candidate in maze.candidates(current)
            if candidate not in visited
        ]

        if not candidates:
            active.pop()
            continue

        next_cell = rng.choice(candidates)

        builder.open_passage(current, next_cell)

        visited.add(next_cell)
        active.append(next_cell)


def randomized_prim(builder: MazeBuilder, rng: random.Random) -> None:
    """Generate a perfect maze using randomized Prim's algorithm."""
    maze = builder.maze

    start = (0, 0)

    if maze.is_blocked(start):
        raise ValueError("Generation starting cell is blocked")

    visited: set[Position] = {start}
    frontier: list[tuple[Position, Position]] = [
        (start, neighbor) for neighbor in maze.candidates(start)
    ]

    while frontier:
        index = rng.randrange(len(frontier))
        visited_cell, unvisited_cell = frontier.pop(index)

        if unvisited_cell in visited:
            continue

        builder.open_passage(visited_cell, unvisited_cell)

        visited.add(unvisited_cell)
        frontier.extend(
            (unvisited_cell, neighbor)
            for neighbor in maze.candidates(unvisited_cell)
            if neighbor not in visited
        )


def bfs(maze: Maze, start: Position, end: Position) -> list[Position]:
    """Return a shortest path between two valid corridor cells."""
    if (
        not maze.in_bounds(start)
        or not maze.in_bounds(end)
        or maze.is_blocked(start)
        or maze.is_blocked(end)
    ):
        return []

    queue = deque([start])
    parent: dict[Position, Position | None] = {start: None}

    while queue:
        if (current := queue.popleft()) == end:
            break

        for neighbor in maze.connected_neighbors(current):
            if neighbor not in parent:
                parent[neighbor] = current
                queue.append(neighbor)

    if end not in parent:
        return []

    path: list[Position] = []
    cursor: Position | None = end

    while cursor is not None:
        path.append(cursor)
        cursor = parent[cursor]

    path.reverse()
    return path


def path_to_directions(path: list[Position]) -> str:
    """Encode a position path as cardinal direction letters."""
    directions: list[str] = []

    for (x, y), (next_x, next_y) in itertools.pairwise(path):
        if (delta := (next_x - x, next_y - y)) not in DELTA_TO_DIRECTION:
            raise ValueError("Path contains non-adjacent cells")

        directions.append(DELTA_TO_DIRECTION[delta])

    return "".join(directions)


def dead_ends(maze: Maze) -> list[Position]:
    """Return corridor cells having exactly one connected neighbor."""
    return [
        pos
        for y in range(maze.height)
        for x in range(maze.width)
        if not maze.is_blocked(pos := (x, y))
        and len(maze.connected_neighbors(pos)) == 1
    ]


def edge_count(maze: Maze) -> int:
    """Count open passages in the undirected maze graph."""
    total = 0

    for y in range(maze.height):
        for x in range(maze.width):
            if maze.is_blocked(position := (x, y)):
                continue

            walls = int(maze[position])

            if x + 1 < maze.width:
                east = (x + 1, y)
                if not maze.is_blocked(east) and not walls & EAST_MASK:
                    total += 1

            if y + 1 < maze.height:
                south = (x, y + 1)
                if not maze.is_blocked(south) and not walls & SOUTH_MASK:
                    total += 1

    return total


# Previous implementation, retained for comparison:
# def edge_count(maze: Maze) -> int:
#     """Count open passages in the undirected maze graph."""
#     return (
#         sum(
#             len(maze.connected_neighbors(pos))
#             for x in range(maze.width)
#             for y in range(maze.height)
#             if not maze.is_blocked(pos := (x, y))
#         )
#         // 2
#     )


def can_open_passage(maze: Maze, current: Position, potential: Position) -> bool:
    """Return whether opening a passage would avoid an open 3-by-3 area."""
    return not any(
        closed_walls_in_window(maze, window) == 1
        for window in affected_windows(maze, current, potential)
    )


def affected_windows(
    maze: Maze,
    current: Position,
    potential: Position,
) -> list[Position]:
    """Return 3-by-3 windows affected by opening the proposed passage."""
    x1, y1 = current
    x2, y2 = potential

    # If horizontally adjacent
    if y1 == y2:
        left = min(x1, x2)  # Use the left-hand cell

        xs = [left - 1, left]
        ys = [y1 - 2, y1 - 1, y1]
    else:
        top = min(y1, y2)

        xs = [x1 - 2, x1 - 1, x1]
        ys = [top - 1, top]

    return [
        (x, y)
        for y in ys
        for x in xs
        if (x >= 0 and y >= 0 and x + 2 < maze.width and y + 2 < maze.height)
    ]


def closed_walls_in_window(maze: Maze, top_left: Position) -> int:
    """Count closed internal walls in a 3-by-3 cell window."""
    pos_x, pos_y = top_left
    return sum(
        (dx < 2 and bool(int(maze[pos_x + dx, pos_y + dy]) & EAST_MASK))
        + (dy < 2 and bool(int(maze[pos_x + dx, pos_y + dy]) & SOUTH_MASK))
        for dy in range(3)
        for dx in range(3)
    )


def independent_loops(maze: Maze) -> int:
    """Return the number of independent cycles in a connected maze."""
    vertices = maze.width * maze.height - maze.blocked_len
    return edge_count(maze) - vertices + 1


def _safe_closed_passages(maze: Maze) -> list[tuple[Position, Position]]:
    """Return unique closed passages that can be opened safely."""
    return [
        (position, neighbor)
        for y in range(maze.height)
        for x in range(maze.width)
        if not maze.is_blocked(position := (x, y))
        for neighbor in maze.closed_neighbors(position)
        if position < neighbor and can_open_passage(maze, position, neighbor)
    ]


def braid(builder: MazeBuilder, rng: random.Random) -> None:
    """Open safe passages to reduce dead ends and guarantee two loops."""
    maze = builder.maze

    for dead_end in dead_ends(maze):
        # Earlier openings might have opened walls that removed a dead end
        if len(maze.connected_neighbors(dead_end)) != 1:
            continue

        safe = [
            neighbor
            for neighbor in maze.closed_neighbors(dead_end)
            if can_open_passage(maze, dead_end, neighbor)
        ]

        if safe:
            builder.open_passage(dead_end, rng.choice(safe))

    while independent_loops(maze) < 2:
        if not (safe_passages := _safe_closed_passages(maze)):
            raise ValueError(
                "Maze dimensions cannot support two routes without an open 3x3 area",
            )

        builder.open_passage(*rng.choice(safe_passages))
