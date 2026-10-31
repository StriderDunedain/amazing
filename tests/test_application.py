import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from mazegen.algorithms import bfs
from mazegen.application import Display, MazeApplication
from mazegen.builder import MazeBuilder
from mazegen.display import resolve_display
from mazegen.maze import Maze
from mazegen.view_state import ViewState


def make_two_cell_maze() -> Maze:
    maze = Maze.create(2, 1)
    MazeBuilder(maze).open_passage((0, 0), (1, 0))
    return maze


class ApplicationTests(unittest.TestCase):
    def test_application_displays_and_persists_regeneration(self) -> None:
        displayed: list[Maze] = []

        def display(state: ViewState) -> None:
            displayed.append(state.maze)
            state.regenerate()
            displayed.append(state.maze)

        with TemporaryDirectory() as directory:
            output = Path(directory) / "maze.txt"
            application = MazeApplication(
                generate=make_two_cell_maze,
                display=display,
                entry=(0, 0),
                exit_=(1, 0),
                output_file=output,
            )

            with patch("mazegen.output.bfs", wraps=bfs) as solve:
                application.run()

            self.assertEqual(output.read_text(encoding="utf-8"), "D7\n\n0,0\n1,0\nE\n")
            self.assertEqual(solve.call_count, 2)

        self.assertEqual(len(displayed), 2)

    def test_display_resolution_is_case_insensitive(self) -> None:
        def display(_state: ViewState) -> None:
            pass

        displays: dict[str, Display] = {"ascii": display}
        self.assertIs(resolve_display("ASCII", displays), display)

    def test_unknown_display_lists_available_modes(self) -> None:
        with self.assertRaisesRegex(ValueError, "choose one of: ascii"):
            resolve_display("web", {"ascii": lambda _state: None})


if __name__ == "__main__":
    unittest.main()
