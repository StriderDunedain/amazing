import sys
import termios
import tty
from collections.abc import Set as AbstractSet
from enum import Enum, auto

from .colors import ANSI_RESET, color
from .maze import Directions as D
from .maze import Position
from .view_state import ViewState

CLEAR_SCREEN = "\033[2J\033[H"

NORTH_MASK = int(D.NORTH)
EAST_MASK = int(D.EAST)
SOUTH_MASK = int(D.SOUTH)
WEST_MASK = int(D.WEST)

ENTRY_COLOR_INDEX = 2
EXIT_COLOR_INDEX = 1


class CellRole(Enum):
    """Describe the visual meaning of a maze cell."""

    NORMAL = auto()
    BLOCKED = auto()
    ENTRY = auto()
    EXIT = auto()
    PATH = auto()


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

CELL_MARKERS = {
    CellRole.BLOCKED: "###",
    CellRole.ENTRY: " S ",
    CellRole.EXIT: " E ",
    CellRole.PATH: " ■ ",
}


def visible_path(state: ViewState) -> frozenset[Position]:
    """Return the path cells when shortest-path display is enabled."""
    if not state.show_path:
        return frozenset()
    return frozenset(state.path)


def cell_role(
    state: ViewState,
    position: Position,
    path: AbstractSet[Position] | None = None,
) -> CellRole:
    """Resolve a cell's visual role with a consistent priority."""
    if state.maze.is_blocked(position):
        return CellRole.BLOCKED
    if position == state.entry:
        return CellRole.ENTRY
    if position == state.exit_:
        return CellRole.EXIT
    if position in (visible_path(state) if path is None else path):
        return CellRole.PATH
    return CellRole.NORMAL


def role_color_index(state: ViewState, role: CellRole) -> int | None:
    """Return the palette index for a visible cell role."""
    match role:
        case CellRole.BLOCKED:
            return state.pattern_color
        case CellRole.ENTRY:
            return ENTRY_COLOR_INDEX
        case CellRole.EXIT:
            return EXIT_COLOR_INDEX
        case CellRole.PATH:
            return state.path_color
        case CellRole.NORMAL:
            return None


def command_from_key(key: str) -> Command | None:
    """Translate one terminal key into a command."""
    return KEY_COMMANDS.get(key.lower())


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
