from .algorithms import (
    closed_walls_in_window,
    dead_ends,
    edge_count,
    independent_loops,
)
from .maze import WALL_DELTA, Maze, Position
from .maze import Directions as D


def validate_generated_maze(maze: Maze, perfect: bool) -> None:
    """Enforce the topology postconditions required by the subject."""
    if not consistent_walls(maze):
        raise ValueError("Generated maze has inconsistent shared walls")
    if not borders_closed(maze):
        raise ValueError("Generated maze has an open external border")
    if not is_connected(maze):
        raise ValueError("Generated maze contains disconnected corridor cells")
    if has_open_3x3(maze):
        raise ValueError("Generated maze contains a forbidden open 3x3 area")

    if perfect:
        if not _has_tree_edge_count(maze):
            raise ValueError("Generator failed to produce a perfect maze")
        return

    if independent_loops(maze) < 2:
        raise ValueError("Non-perfect maze must contain at least two routes")
    if not key_cells_open(maze):
        raise ValueError("Non-perfect maze must keep corners and center open")
    if real_dead_end_count(maze) > 2:
        raise ValueError("Non-perfect maze contains too many real dead ends")


def valid_endpoint(
    maze: Maze,
    pos: Position,
) -> bool:
    """Return whether an endpoint is in bounds and not blocked."""
    return maze.in_bounds(pos) and not maze.is_blocked(pos)


def reachable_cells(maze: Maze, start: Position) -> set[Position]:
    """Return corridor cells reachable from a valid starting position."""
    if not valid_endpoint(maze, start):
        return set()

    visited = {start}
    stack = [start]

    while stack:
        for neighbor in maze.connected_neighbors(stack.pop()):
            if neighbor not in visited:
                visited.add(neighbor)
                stack.append(neighbor)

    return visited


def consistent_walls(maze: Maze) -> bool:
    """Return whether both cells agree on every shared wall."""
    return all(
        bool(maze[position] & wall) == bool(maze[neighbor] & opposite)
        for position in maze.positions()
        for (dx, dy), (wall, opposite) in WALL_DELTA.items()
        if maze.in_bounds(
            neighbor := (position[0] + dx, position[1] + dy),
        )
    )


def borders_closed(maze: Maze) -> bool:
    """Return whether every external maze border is closed."""
    return all(
        maze[x, 0] & D.NORTH and maze[x, maze.height - 1] & D.SOUTH
        for x in range(maze.width)
    ) and all(
        maze[0, y] & D.WEST and maze[maze.width - 1, y] & D.EAST
        for y in range(maze.height)
    )


def is_connected(maze: Maze) -> bool:
    """Return whether all non-blocked cells form one component."""
    start = next(maze.corridors(), None)
    if start is None:
        return False

    reachable = reachable_cells(maze, start)
    usable = maze.width * maze.height - maze.blocked_len

    return len(reachable) == usable


def has_open_3x3(maze: Maze) -> bool:
    """Return whether any 3-by-3 group has no internal walls."""
    return any(
        closed_walls_in_window(maze, (x, y)) == 0
        for y in range(maze.height - 2)
        for x in range(maze.width - 2)
    )


def real_dead_end_count(maze: Maze) -> int:
    """Count dead ends that could open toward a normal corridor cell."""
    return sum(bool(maze.closed_neighbors(pos)) for pos in dead_ends(maze))


def key_cells_open(maze: Maze) -> bool:
    """Return whether every corner and at least one center cell is a corridor."""
    corners = {
        (0, 0),
        (maze.width - 1, 0),
        (0, maze.height - 1),
        (maze.width - 1, maze.height - 1),
    }
    center_x = range((maze.width - 1) // 2, maze.width // 2 + 1)
    center_y = range((maze.height - 1) // 2, maze.height // 2 + 1)
    centers = {(x, y) for x in center_x for y in center_y}

    return all(not maze.is_blocked(position) for position in corners) and any(
        not maze.is_blocked(position) for position in centers
    )


def is_perfect(maze: Maze) -> bool:
    """Return whether the maze is a valid connected spanning tree."""
    return (
        consistent_walls(maze)
        and borders_closed(maze)
        and is_connected(maze)
        and _has_tree_edge_count(maze)
    )


def _has_tree_edge_count(maze: Maze) -> bool:
    """Return whether the maze graph has the edge count of a tree."""
    vertices = maze.width * maze.height - maze.blocked_len
    return edge_count(maze) == vertices - 1
