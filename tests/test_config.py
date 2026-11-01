import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from a_maze_ing import main, resolve_algorithm
from mazegen import MazeGenerator
from mazegen.algorithms import growing_tree, randomized_prim
from mazegen.config import ConfigError, GenerationSpec, load_config
from mazegen.view_state import ViewState


def write_config(
    path: Path,
    output: Path,
    algorithm: str | None = None,
) -> None:
    algorithm_line = "" if algorithm is None else f"ALGORITHM={algorithm}\n"
    path.write_text(
        "WIDTH=4\n"
        "HEIGHT=3\n"
        "ENTRY=0,0\n"
        "EXIT=3,2\n"
        f"OUTPUT_FILE={output}\n"
        "PERFECT=False\n"
        "SEED=42\n"
        f"{algorithm_line}",
        encoding="utf-8",
    )


class ConfigTests(unittest.TestCase):
    def test_algorithm_defaults_and_is_case_insensitive(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.txt"
            output = root / "maze.txt"

            write_config(config_path, output)
            self.assertEqual(load_config(config_path).algorithm, "growing_tree")

            write_config(config_path, output, algorithm="RANDOMIZED_PRIM")
            self.assertEqual(load_config(config_path).algorithm, "randomized_prim")

    def test_algorithm_resolution(self) -> None:
        self.assertIs(resolve_algorithm("GROWING_TREE"), growing_tree)
        self.assertIs(resolve_algorithm("randomized_prim"), randomized_prim)

        with self.assertRaisesRegex(
            ValueError,
            "choose one of: growing_tree, randomized_prim",
        ):
            resolve_algorithm("kruskal")

    def test_unknown_algorithm_is_reported_without_a_traceback(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.txt"
            write_config(config_path, root / "maze.txt", algorithm="kruskal")
            stderr = StringIO()

            with redirect_stderr(stderr):
                result = main(["a_maze_ing.py", str(config_path)])

            self.assertEqual(result, 1)
            self.assertIn("Unknown generation algorithm", stderr.getvalue())

    def test_configured_algorithm_is_injected_into_generator(self) -> None:
        displayed: list[ViewState] = []

        with TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.txt"
            write_config(
                config_path,
                root / "maze.txt",
                algorithm="randomized_prim",
            )

            with (
                patch("a_maze_ing.run_ascii", side_effect=displayed.append),
                redirect_stderr(StringIO()),
            ):
                result = main(["a_maze_ing.py", str(config_path)])

            expected = MazeGenerator(
                GenerationSpec(4, 3, False, 42),
                randomized_prim,
            ).generate()

            self.assertEqual(result, 0)
            self.assertEqual(displayed[0].maze, expected)

    def test_display_is_no_longer_a_config_option(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.txt"
            write_config(config_path, root / "maze.txt")
            config_path.write_text(
                config_path.read_text(encoding="utf-8") + "DISPLAY=ascii\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ConfigError, "unknown key 'DISPLAY'"):
                load_config(config_path)

    def test_cli_accepts_exactly_one_config_argument(self) -> None:
        self.assertEqual(main([]), 1)
        self.assertEqual(main(["a_maze_ing.py", "config.txt", "ascii"]), 1)

    def test_missing_duplicate_unknown_and_empty_keys_are_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.txt"
            write_config(config_path, root / "maze.txt")
            valid = config_path.read_text(encoding="utf-8")
            cases = {
                "missing": (valid.replace("HEIGHT=3\n", ""), "Missing keys: HEIGHT"),
                "duplicate": (valid + "WIDTH=5\n", "duplicate key 'WIDTH'"),
                "unknown": (valid + "STYLE=wide\n", "unknown key 'STYLE'"),
                "empty key": (valid + "=value\n", "key must not be empty"),
                "empty value": (
                    valid.replace("WIDTH=4", "WIDTH="),
                    "WIDTH must not be empty",
                ),
            }

            for name, (contents, message) in cases.items():
                with self.subTest(name=name):
                    config_path.write_text(contents, encoding="utf-8")
                    with self.assertRaisesRegex(ConfigError, message):
                        load_config(config_path)

    def test_malformed_values_have_key_specific_errors(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.txt"
            write_config(config_path, root / "maze.txt")
            valid = config_path.read_text(encoding="utf-8")
            cases = {
                "width": (valid.replace("WIDTH=4", "WIDTH=wide"), "WIDTH"),
                "entry": (valid.replace("ENTRY=0,0", "ENTRY=0;0"), "ENTRY"),
                "boolean": (
                    valid.replace("PERFECT=False", "PERFECT=perhaps"),
                    "PERFECT",
                ),
                "seed": (valid.replace("SEED=42", "SEED=random"), "SEED"),
            }

            for name, (contents, key) in cases.items():
                with self.subTest(name=name):
                    config_path.write_text(contents, encoding="utf-8")
                    with self.assertRaisesRegex(ConfigError, key):
                        load_config(config_path)

    def test_integers_accept_only_ascii_decimal_digits(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.txt"
            write_config(config_path, root / "maze.txt")
            valid = config_path.read_text(encoding="utf-8")
            invalid_widths = (
                "24,15",
                "24.15",
                "-24",
                "٢٤",  # Arabic-Indic digits
                "२४",  # Devanagari digits
                "Ⅹ",  # Roman numeral ten
                "二十四",  # Chinese numerals
            )

            for width in invalid_widths:
                with self.subTest(width=width):
                    config_path.write_text(
                        valid.replace("WIDTH=4", f"WIDTH={width}"),
                        encoding="utf-8",
                    )
                    with self.assertRaisesRegex(
                        ConfigError,
                        r"WIDTH must contain only ASCII digits \(0-9\)",
                    ):
                        load_config(config_path)

    def test_output_cannot_overwrite_config_or_name_a_directory(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.txt"

            write_config(config_path, config_path)
            original = config_path.read_text(encoding="utf-8")
            stderr = StringIO()
            with redirect_stderr(stderr):
                result = main(["a_maze_ing.py", str(config_path)])

            self.assertEqual(result, 1)
            self.assertIn("must not overwrite", stderr.getvalue())
            self.assertEqual(config_path.read_text(encoding="utf-8"), original)

            write_config(config_path, root)
            stderr = StringIO()
            with redirect_stderr(stderr):
                result = main(["a_maze_ing.py", str(config_path)])

            self.assertEqual(result, 1)
            self.assertIn("must name a file", stderr.getvalue())

    def test_endpoints_cannot_collide_with_pattern(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.txt"
            config_path.write_text(
                "WIDTH=10\n"
                "HEIGHT=7\n"
                "ENTRY=1,1\n"
                "EXIT=9,6\n"
                f"OUTPUT_FILE={root / 'maze.txt'}\n"
                "PERFECT=True\n",
                encoding="utf-8",
            )
            stderr = StringIO()

            with redirect_stderr(stderr):
                result = main(["a_maze_ing.py", str(config_path)])

            self.assertEqual(result, 1)
            self.assertIn("ENTRY collides with the 42 pattern", stderr.getvalue())

    def test_malformed_config_is_reported_without_a_traceback(self) -> None:
        with TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.txt"
            config_path.write_text("WIDTH=4\nBROKEN\n", encoding="utf-8")
            stderr = StringIO()

            with redirect_stderr(stderr):
                result = main(["a_maze_ing.py", str(config_path)])

            self.assertEqual(result, 1)
            self.assertIn("Error: Line 2: expected KEY=VALUE", stderr.getvalue())

    def test_invalid_encoding_and_missing_file_are_reported(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.txt"
            config_path.write_bytes(b"WIDTH=4\n\xff\n")

            with self.assertRaisesRegex(ConfigError, "valid UTF-8"):
                load_config(config_path)

            stderr = StringIO()
            with redirect_stderr(stderr):
                result = main(["a_maze_ing.py", str(root / "missing.txt")])

            self.assertEqual(result, 1)
            self.assertIn("Error:", stderr.getvalue())

    def test_missing_output_parent_is_reported(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.txt"
            write_config(config_path, root / "missing" / "maze.txt")
            stderr = StringIO()

            with redirect_stderr(stderr):
                result = main(["a_maze_ing.py", str(config_path)])

            self.assertEqual(result, 1)
            self.assertIn("Error:", stderr.getvalue())

    def test_memory_failure_is_reported_without_a_traceback(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.txt"
            write_config(config_path, root / "maze.txt")
            stderr = StringIO()

            with (
                patch("a_maze_ing.MazeGenerator", side_effect=MemoryError),
                redirect_stderr(stderr),
            ):
                result = main(["a_maze_ing.py", str(config_path)])

            self.assertEqual(result, 1)
            self.assertIn("not enough memory", stderr.getvalue())

    def test_small_maze_warning_and_ascii_view(self) -> None:
        displayed: list[ViewState] = []

        with TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "config.txt"
            write_config(config_path, root / "maze.txt")
            stderr = StringIO()

            with (
                patch("a_maze_ing.run_ascii", side_effect=displayed.append),
                redirect_stderr(stderr),
            ):
                result = main(["a_maze_ing.py", str(config_path)])

            self.assertEqual(result, 0)
            self.assertEqual(len(displayed), 1)
            self.assertIn("too small to contain the 42 pattern", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
