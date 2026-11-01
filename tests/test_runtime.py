import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from mazegen.algorithms import bfs, growing_tree
from mazegen.config import GenerationSpec
from mazegen.generator import MazeGenerator


class RuntimeTests(unittest.TestCase):
    def test_generator_builds_state_and_persists_regeneration(self) -> None:
        generator = MazeGenerator(GenerationSpec(2, 1, True, 42), growing_tree)

        with TemporaryDirectory() as directory:
            output = Path(directory) / "maze.txt"

            with patch("mazegen.output.bfs", wraps=bfs) as solve:
                state = generator.build_state((0, 0), (1, 0), output)
                first_maze = state.maze
                state.regenerate()

            self.assertEqual(
                output.read_text(encoding="utf-8"),
                "D7\n\n0,0\n1,0\nE\n",
            )
            self.assertEqual(solve.call_count, 2)
            self.assertIsNot(state.maze, first_maze)


if __name__ == "__main__":
    unittest.main()
