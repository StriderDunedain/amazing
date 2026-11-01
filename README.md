*This project has been created as part of the 42 curriculum by mtrukhin.*

# A-Maze-ing

## Description

A-Maze-ing reads a configuration file, generates a reproducible maze, writes
its hexadecimal wall representation and shortest entry-to-exit path, and opens
an interactive terminal ASCII visualization.

The reusable `mazegen` package exposes maze generation, shortest-path access,
and output helpers. The CLI uses one interactive terminal ASCII view. Perfect
mode creates a spanning-tree maze with one path between every pair of corridor
cells. Non-perfect mode braids that maze into a Pac-Man-like board with at
least two independent loops, no open 3-by-3 area, full connectivity, and at
most two real dead ends.

## Features

- Seeded Growing Tree and randomized Prim maze generation.
- Perfect and braided non-perfect modes.
- Fully closed cells forming a centered “42” when dimensions permit it.
- Shortest-path calculation and hexadecimal output.
- Interactive terminal ASCII display.
- Runtime controls for regeneration, path visibility, and colors.
- Installable `mazegen` Python package.

A seed reproduces the complete sequence: the first maze is repeatable, while
each `R` interaction advances the same random stream and produces a new maze.

## Instructions

Python 3.10 or newer is required.

```console
make install
make run
```

The mandatory direct invocation is:

```console
python3 a_maze_ing.py config.txt
```

Other useful commands are:

```console
make debug
make test
make lint
make lint-strict
make build
make clean
```

`make build` creates both a source distribution and wheel, then copies the
latest `mazegen-*` artifacts to the repository root as required by the subject.

## Configuration

The file contains one `KEY=VALUE` pair per line. Empty lines and lines starting
with `#` are ignored.

| Key | Required | Meaning | Example |
| --- | --- | --- | --- |
| `WIDTH` | yes | Number of columns | `WIDTH=20` |
| `HEIGHT` | yes | Number of rows | `HEIGHT=15` |
| `ENTRY` | yes | Entry coordinate as `x,y` | `ENTRY=0,0` |
| `EXIT` | yes | Exit coordinate as `x,y` | `EXIT=19,14` |
| `OUTPUT_FILE` | yes | Generated maze file | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | yes | `True` for one path, `False` for a braided board | `PERFECT=False` |
| `SEED` | no | Reproducible random seed | `SEED=42` |
| `ALGORITHM` | no | `growing_tree` (default) or `randomized_prim` | `ALGORITHM=growing_tree` |

## Controls

| Key | Action |
| --- | --- |
| `R` | Regenerate the maze |
| `P` | Show or hide the shortest path |
| `C` | Change wall color |
| `4` | Change the “42” color |
| `V` | Change path color |
| `Q` or Escape | Quit |

## Generation algorithm

The default is the Growing Tree algorithm with a last-added-cell selection
policy, making it an iterative recursive-backtracker variant. It was chosen as
the default because it naturally creates long corridors, is straightforward to
seed, does not need recursion, and can avoid the blocked “42” cells.

Setting `ALGORITHM=randomized_prim` selects randomized Prim's algorithm instead.
It grows the maze by repeatedly choosing a random frontier edge, which generally
produces shorter branches and a different visual texture. Both algorithms first
produce a connected spanning tree and use the same injected
`(MazeBuilder, random.Random) -> None` interface.

For `PERFECT=False`, a braiding pass opens safe walls at dead ends. It refuses
walls that would produce a completely open 3-by-3 area, then ensures that at
least two independent cycles exist.

## Reusing `mazegen`

Build and install the package:

```console
make build
python3 -m pip install ./mazegen-0.1.0-py3-none-any.whl
```

Basic use with custom size and seed:

```python
from mazegen import GenerationSpec, MazeGenerator, randomized_prim

generator = MazeGenerator(
    spec=GenerationSpec(
        width=20,
        height=15,
        perfect=True,
        seed=42,
    ),
    algorithm=randomized_prim,
)
maze = generator.generate()

walls_at_origin = maze[0, 0]
solution = generator.solution(maze, (0, 0), (19, 14))
```

`Maze` exposes dimensions, wall values, blocked cells, connected neighbors,
and the generated structure independently of the output-file encoding.

## Output format

Each row contains one hexadecimal digit per cell. Bits 0–3 represent closed
north, east, south, and west walls respectively. After a blank line, the file
contains the entry coordinate, exit coordinate, and shortest path encoded with
`N`, `E`, `S`, and `W`. Every line ends with a newline.

## Technical choices

- A local `random.Random` instance isolates seeded generation.
- `IntFlag` represents composable wall bits.
- Iterative BFS produces shortest paths without recursion.
- Each generated maze calculates its path once; output and visualization share
  that stored result.
- `Maze` is a read-only topology model; `MazeBuilder` owns checked mutations.
- Generation algorithms are injected; ASCII is the single built-in view.
- The ASCII renderer consumes presentation state without owning generation.
- Pattern placement, braiding, subject validation, and file output remain
  direct internal collaborators because the project has only one of each.

## Team and project management

This was a solo project. The sole developer handled generation, validation,
configuration, output, visualization, packaging, and testing.

The initial plan was to finish generation and output first, then add the visual
layer. Tight time constraints led to duplicated debug/rendering code and limited
automated tests. The final cleanup consolidated diagnostics into unit tests,
added package and lint automation, and removed obsolete display-selection code
after settling on terminal ASCII.

The seeded generator and graph validations worked well. Earlier integration of
tests, packaging, and renderer boundaries would have reduced late refactoring.
Tools used include Python's standard library, unittest, mypy, Ruff, flake8,
and the provided maze analyzer.

## Resources

- [Python `random` documentation](https://docs.python.org/3/library/random.html)
- [Python `enum` documentation](https://docs.python.org/3/library/enum.html)
- [Python packaging guide](https://packaging.python.org/)
- [Maze generation algorithms](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- The A-Maze-ing v2.3 subject and its provided analyzer.

AI was used to review code written under time pressure, locate duplicated and
unreachable code, suggest dependency boundaries, create edge-case test ideas,
and check the implementation against the subject. All resulting changes were
reviewed through static analysis, unit tests, and randomized invariant sweeps.

## License

This project is available under the GNU General Public License v3.0 or later.
See [LICENSE.md](LICENSE.md).
