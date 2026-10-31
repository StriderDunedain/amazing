import sys
import termios
import tty

from .colors import ANSI_RESET, color
from .maze import Directions as D
from .presentation import (
    CellRole,
    cell_role,
    command_from_key,
    handle_command,
    role_color_index,
    visible_path,
)
from .view_state import ViewState

CLEAR_SCREEN = "\033[2J\033[H"

NORTH_MASK = int(D.NORTH)
EAST_MASK = int(D.EAST)
SOUTH_MASK = int(D.SOUTH)
WEST_MASK = int(D.WEST)

CELL_MARKERS = {
    CellRole.BLOCKED: "###",
    CellRole.ENTRY: " S ",
    CellRole.EXIT: " E ",
    CellRole.PATH: " ■ ",
}


def paint(text: str, color_index: int) -> str:
    """Wrap text in the selected ANSI color and a reset sequence."""
    return color(color_index).ansi + text + ANSI_RESET


def render_ascii(state: ViewState) -> str:
    """Render the current view state as a colored terminal maze."""
    maze = state.maze
    path = visible_path(state)
    painted_corner = paint("+", state.wall_color)
    painted_horizontal = paint("---", state.wall_color)
    painted_vertical = paint("|", state.wall_color)

    lines: list[str] = []

    for y in range(maze.height):
        top: list[str] = []
        middle: list[str] = []

        for x in range(maze.width):
            position = (x, y)
            walls = int(maze[position])

            top.append(painted_corner)
            top.append(painted_horizontal if walls & NORTH_MASK else "   ")
            middle.append(painted_vertical if walls & WEST_MASK else " ")

            role = cell_role(state, position, path)
            marker = CELL_MARKERS.get(role)
            color_index = role_color_index(state, role)

            middle.append(
                "   "
                if marker is None or color_index is None
                else paint(marker, color_index),
            )

        top.append(painted_corner)
        right_walls = int(maze[maze.width - 1, y])
        middle.append(painted_vertical if right_walls & EAST_MASK else " ")
        lines.extend(("".join(top), "".join(middle)))

    bottom: list[str] = []

    for x in range(maze.width):
        walls = int(maze[x, maze.height - 1])
        bottom.append(painted_corner)
        bottom.append(painted_horizontal if walls & SOUTH_MASK else "   ")

    bottom.append(painted_corner)
    lines.append("".join(bottom))

    return "\n".join(lines)


def read_key() -> str:
    """Read one key from the terminal without waiting for a newline."""
    fd = sys.stdin.fileno()
    previous = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(
            fd,
            termios.TCSADRAIN,
            previous,
        )


def print_controls(state: ViewState) -> None:
    """Print interactive controls and the active color names."""
    print()
    print(
        "[R] regenerate   [P] path   [C] walls   [4] 42   [V] path color   [Q] quit",
    )
    print(
        f"walls={color(state.wall_color).name}  "
        f"42={color(state.pattern_color).name}  "
        f"path={color(state.path_color).name}",
    )


def run_ascii(state: ViewState) -> None:
    """Run the interactive terminal display until the user quits."""
    try:
        while True:
            print(CLEAR_SCREEN, end="")

            print(render_ascii(state))
            print_controls(state)

            command = command_from_key(read_key())

            if command is not None and not handle_command(state, command):
                return

    except termios.error as error:
        raise RuntimeError(
            "ASCII display requires an interactive terminal",
        ) from error

    finally:
        print(ANSI_RESET, end="")
