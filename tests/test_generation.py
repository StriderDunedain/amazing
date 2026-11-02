import random
import unittest
from contextlib import redirect_stderr
from io import StringIO

from mazegen import MazeGenerator, randomized_prim
from mazegen.algorithms import (
    bfs,
    closed_walls_in_window,
    growing_tree,
    independent_loops,
)
from mazegen.builder import MazeBuilder
from mazegen.config import GenerationSpec
from mazegen.generator import GenerationAlgorithm
from mazegen.maze import ALL_WALLS, Maze
from mazegen.pattern import make_42_pattern
from mazegen.validation import (
    borders_closed,
    consistent_walls,
    is_connected,
    is_perfect,
    key_cells_open,
    real_dead_end_count,
)


class GenerationTests(unittest.TestCase):
    @staticmethod
    def generator(
        width: int,
        height: int,
        perfect: bool,
        seed: int | None = None,
        algorithm: GenerationAlgorithm = growing_tree,
    ) -> MazeGenerator:
        """Build the production generator from an explicit generation spec."""
        with redirect_stderr(StringIO()):
            return MazeGenerator(
                GenerationSpec(width, height, perfect, seed),
                algorithm,
            )

    def test_perfect_generation_invariants(self) -> None:
        for algorithm in (growing_tree, randomized_prim):
            for width, height in ((1, 1), (9, 6), (10, 7), (20, 15)):
                for seed in range(5):
                    with self.subTest(
                        algorithm=algorithm.__name__,
                        width=width,
                        height=height,
                        seed=seed,
                    ):
                        maze = self.generator(
                            width,
                            height,
                            True,
                            seed,
                            algorithm,
                        ).generate()

                        self.assertTrue(consistent_walls(maze))
                        self.assertTrue(borders_closed(maze))
                        self.assertTrue(is_connected(maze))
                        self.assertTrue(is_perfect(maze))

    def test_non_perfect_generation_invariants(self) -> None:
        for algorithm in (growing_tree, randomized_prim):
            for seed in range(10):
                with self.subTest(algorithm=algorithm.__name__, seed=seed):
                    maze = self.generator(
                        20,
                        15,
                        False,
                        seed,
                        algorithm,
                    ).generate()

                    self.assertTrue(consistent_walls(maze))
                    self.assertTrue(borders_closed(maze))
                    self.assertTrue(is_connected(maze))
                    self.assertFalse(is_perfect(maze))
                    self.assertGreaterEqual(independent_loops(maze), 2)
                    self.assertTrue(key_cells_open(maze))
                    self.assertLessEqual(real_dead_end_count(maze), 2)
                    self.assertFalse(
                        any(
                            closed_walls_in_window(maze, (x, y)) == 0
                            for y in range(maze.height - 2)
                            for x in range(maze.width - 2)
                        ),
                    )

    def test_seed_reproduces_a_sequence_of_distinct_mazes(self) -> None:
        for algorithm in (growing_tree, randomized_prim):
            first = self.generator(20, 15, True, seed=42, algorithm=algorithm)
            second = self.generator(20, 15, True, seed=42, algorithm=algorithm)

            first_sequence = [first.generate(), first.generate()]
            second_sequence = [second.generate(), second.generate()]

            self.assertEqual(first_sequence, second_sequence)
            self.assertNotEqual(first_sequence[0], first_sequence[1])

    def test_algorithms_produce_different_seeded_mazes(self) -> None:
        growing = self.generator(20, 15, True, 42, growing_tree).generate()
        prim = self.generator(20, 15, True, 42, randomized_prim).generate()

        self.assertNotEqual(growing, prim)

    def test_pattern_has_a_surrounding_corridor(self) -> None:
        stderr = StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(make_42_pattern(9, 6), set())

        self.assertIn("continuing without it", stderr.getvalue())

        pattern = make_42_pattern(10, 7)
        self.assertEqual(len(pattern), 18)
        self.assertNotIn((0, 0), pattern)
        self.assertTrue(all(0 < x < 9 and 0 < y < 6 for x, y in pattern))

    def test_pattern_cells_remain_closed(self) -> None:
        maze = self.generator(20, 15, True, seed=42).generate()

        self.assertTrue(maze.blocked)
        self.assertTrue(all(maze[position] == ALL_WALLS for position in maze.blocked))

    def test_builder_rejects_invalid_mutations(self) -> None:
        maze = Maze.create(2, 2)
        builder = MazeBuilder(maze)

        with self.assertRaises(ValueError):
            builder.block_cells({(2, 0)})

        builder.block_cells({(1, 0)})
        with self.assertRaises(ValueError):
            builder.open_passage((0, 0), (1, 0))

        with self.assertRaises(ValueError):
            builder.open_passage((-1, 0), (0, 0))

    def test_generation_algorithm_is_injected(self) -> None:
        generated: list[Maze] = []

        def algorithm(builder: MazeBuilder, rng: random.Random) -> None:
            generated.append(builder.maze)
            growing_tree(builder, rng)

        maze = self.generator(2, 2, True, 42, algorithm).generate()

        self.assertEqual(generated, [maze])

    def test_maze_has_no_public_topology_assignment(self) -> None:
        maze = Maze.create(1, 1)

        with self.assertRaises(TypeError):
            maze[0, 0] = ALL_WALLS  # type: ignore[index]

    def test_bfs_rejects_invalid_or_blocked_endpoints(self) -> None:
        maze = Maze.create(2, 2)
        MazeBuilder(maze).block_cells({(1, 0)})

        self.assertEqual(bfs(maze, (-1, 0), (0, 0)), [])
        self.assertEqual(bfs(maze, (0, 0), (1, 0)), [])

    def test_maze_dimensions_must_be_positive(self) -> None:
        for dimensions in ((0, 1), (1, 0), (-1, 2)):
            with self.subTest(dimensions=dimensions), self.assertRaises(ValueError):
                Maze.create(*dimensions)


if __name__ == "__main__":
    unittest.main()
