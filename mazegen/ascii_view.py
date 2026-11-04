import sys
import termios
import time
import tty
from collections.abc import Set as AbstractSet
from enum import Enum, auto

from .colors import ANSI_RESET, color
from .maze import Directions as D
from .maze import Maze, Position
from .pattern import pattern_warning
from .view_state import ViewState

CLEAR_SCREEN = "\033[2J\033[H"

ENTRY_COLOR_INDEX = 2
EXIT_COLOR_INDEX = 1


class Command(Enum):
    """Describe an interactive terminal command."""

    REGENERATE = auto()
    TOGGLE_PATH = auto()
    NEXT_WALL_COLOR = auto()
    NEXT_PATTERN_COLOR = auto()
    NEXT_PATH_COLOR = auto()
    QUIT = auto()


KEY_COMMANDS = {
    "r": Command.REGENERATE,
    "p": Command.TOGGLE_PATH,
    "c": Command.NEXT_WALL_COLOR,
    "4": Command.NEXT_PATTERN_COLOR,
    "v": Command.NEXT_PATH_COLOR,
    "q": Command.QUIT,
    "\x1b": Command.QUIT,
}


def visible_path(state: ViewState) -> frozenset[Position]:
    """Return the path cells when shortest-path display is enabled."""
    return frozenset(state.path) if state.show_path else frozenset()


def handle_command(state: ViewState, command: Command) -> bool:
    """Apply a command and return whether the view should keep running."""
    match command:
        case Command.REGENERATE:
            state.regenerate()
        case Command.TOGGLE_PATH:
            state.toggle_path()
        case Command.NEXT_WALL_COLOR:
            state.cycle_wall_color()
        case Command.NEXT_PATTERN_COLOR:
            state.cycle_pattern_color()
        case Command.NEXT_PATH_COLOR:
            state.cycle_path_color()
        case Command.QUIT:
            return False
    return True


def paint(text: str, color_index: int) -> str:
    """Wrap text in the selected ANSI color and a reset sequence."""
    return f"{color(color_index).ansi}{text}{ANSI_RESET}"


def render_cell(
    state: ViewState,
    position: Position,
    path: AbstractSet[Position],
) -> str:
    """Render a cell marker using blocked, endpoint, then path priority."""
    if state.maze.is_blocked(position):
        return paint("###", state.pattern_color)
    if position == state.entry:
        return paint(" S ", ENTRY_COLOR_INDEX)
    if position == state.exit_:
        return paint(" E ", EXIT_COLOR_INDEX)
    if position in path:
        return paint(" ■ ", state.path_color)
    return "   "


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
            walls = maze[position]

            top.extend(
                (painted_corner, painted_horizontal if walls & D.NORTH else "   "),
            )
            middle.extend(
                (
                    painted_vertical if walls & D.WEST else " ",
                    render_cell(state, position, path),
                ),
            )

        top.append(painted_corner)
        right_walls = maze[maze.width - 1, y]
        middle.append(painted_vertical if right_walls & D.EAST else " ")
        lines.extend(("".join(top), "".join(middle)))

    bottom = "".join(
        painted_corner
        + (painted_horizontal if maze[x, maze.height - 1] & D.SOUTH else "   ")
        for x in range(maze.width)
    )
    lines.append(bottom + painted_corner)

    return "\n".join(lines)


def animate_generation(
    maze: Maze,
    entry: Position,
    exit_: Position,
    cells_per_second: int,
) -> None:
    """Draw one intermediate generation frame in an interactive terminal."""
    if not sys.stdout.isatty():
        return
    if cells_per_second <= 0:
        raise ValueError("Animation speed must be positive")

    state = ViewState(
        maze=maze,
        entry=entry,
        exit_=exit_,
        path=[],
    )
    print(CLEAR_SCREEN, end="")
    print(render_ascii(state))
    time.sleep(1 / cells_per_second)


def read_key() -> str:
    """Read one key from the terminal without waiting for a newline."""
    fd = sys.stdin.fileno()
    previous = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, previous)


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
    if warning := pattern_warning(state.maze.width, state.maze.height):
        print(warning)


def run_ascii(state: ViewState) -> None:
    """Run the interactive terminal display until the user quits."""
    try:
        while True:
            print(CLEAR_SCREEN, end="")

            print(render_ascii(state))
            print_controls(state)

            command = KEY_COMMANDS.get(read_key().lower())

            if command is not None and not handle_command(state, command):
                return

    except termios.error as error:
        raise RuntimeError(
            "ASCII display requires an interactive terminal",
        ) from error

    finally:
        print(ANSI_RESET, end="")
