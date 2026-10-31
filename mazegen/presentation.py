from collections.abc import Set as AbstractSet
from enum import Enum, auto

from .maze import Position
from .view_state import ViewState

ENTRY_COLOR_INDEX = 2
EXIT_COLOR_INDEX = 1


class CellRole(Enum):
    """Describe the presentation meaning of a maze cell."""

    NORMAL = auto()
    BLOCKED = auto()
    ENTRY = auto()
    EXIT = auto()
    PATH = auto()


class Command(Enum):
    """Describe an interaction shared by every display adapter."""

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
    """Return the visible path cells for the current presentation state."""
    if not state.show_path:
        return frozenset()
    return frozenset(state.path)


def cell_role(
    state: ViewState,
    position: Position,
    path: AbstractSet[Position] | None = None,
) -> CellRole:
    """Resolve a cell's role with a consistent priority for all displays."""
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
    """Return the shared palette index for a visible cell role."""
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
    """Translate one display key into a shared interaction command."""
    return KEY_COMMANDS.get(key.lower())


def handle_command(state: ViewState, command: Command) -> bool:
    """Apply a command and return whether the display should keep running."""
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
