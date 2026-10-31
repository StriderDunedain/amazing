import unittest

from mazegen.builder import MazeBuilder
from mazegen.maze import Maze
from mazegen.presentation import (
    CellRole,
    Command,
    cell_role,
    command_from_key,
    handle_command,
    visible_path,
)
from mazegen.view_state import ViewState


def make_state() -> ViewState:
    """Create a two-cell state with a valid path."""
    maze = Maze.create(2, 1)
    MazeBuilder(maze).open_passage((0, 0), (1, 0))
    path = [(0, 0), (1, 0)]
    return ViewState(maze, (0, 0), (1, 0), lambda: (maze, path), path)


class PresentationTests(unittest.TestCase):
    def test_cell_roles_and_path_visibility_are_shared(self) -> None:
        state = make_state()

        self.assertEqual(cell_role(state, (0, 0)), CellRole.ENTRY)
        self.assertEqual(cell_role(state, (1, 0)), CellRole.EXIT)
        self.assertEqual(visible_path(state), frozenset())

        state.toggle_path()

        self.assertEqual(visible_path(state), {(0, 0), (1, 0)})
        self.assertEqual(cell_role(state, (0, 0)), CellRole.ENTRY)

    def test_commands_are_translated_and_applied_once(self) -> None:
        state = make_state()

        self.assertIs(command_from_key("P"), Command.TOGGLE_PATH)
        self.assertTrue(handle_command(state, Command.TOGGLE_PATH))
        self.assertTrue(state.show_path)
        self.assertFalse(handle_command(state, Command.QUIT))
        self.assertIsNone(command_from_key("?"))


if __name__ == "__main__":
    unittest.main()
