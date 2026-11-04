PYTHON ?= python3
CONFIG ?= config.txt

.PHONY: install run debug clean lint lint-strict build

install:
	$(PYTHON) -m ensurepip --upgrade
	$(PYTHON) -m pip install -e ".[dev]"

run:
	$(PYTHON) a_maze_ing.py $(CONFIG)

debug:
	$(PYTHON) -m pdb a_maze_ing.py $(CONFIG)

clean:
	find . -path ./.venv -prune -o -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .mypy_cache .ruff_cache build dist *.egg-info

lint:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --strict

build:
	$(PYTHON) -m build
	cp $$(ls -1t dist/mazegen-*.whl | head -n 1) .
	cp $$(ls -1t dist/mazegen-*.tar.gz | head -n 1) .
