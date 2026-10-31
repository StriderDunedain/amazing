from pathlib import Path

from .algorithms import bfs, path_to_directions
from .maze import Maze, Position


def maze_to_hex(maze: Maze) -> list[str]:
    """Encode every maze row as hexadecimal wall digits."""
    return [
        "".join(format(int(maze[x, y]), "X") for x in range(maze.width))
        for y in range(maze.height)
    ]


def write_maze(
    maze: Maze, entry: Position, exit_: Position, output_file: str | Path
) -> list[Position]:
    """Write the maze and return the shortest path used in the output."""
    if not (path := bfs(maze, entry, exit_)):
        raise ValueError("No path exists between entry and exit")

    directions = path_to_directions(path)

    with open(output_file, "w", encoding="utf-8") as file:
        file.writelines(row + "\n" for row in maze_to_hex(maze))

        file.write("\n")
        file.write(f"{entry[0]},{entry[1]}\n")
        file.write(f"{exit_[0]},{exit_[1]}\n")
        file.write(directions + "\n")

    return path
