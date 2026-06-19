SHELL := /usr/bin/env bash

.PHONY: help setup lint test check node-check python-build release-dry-run clean

help:
	@printf "cursor-dreaming-sdk developer commands\n\n"
	@printf "  make setup          Install Python dev dependencies\n"
	@printf "  make lint           Run Python and Node lint/syntax checks\n"
	@printf "  make test           Run Python and Node tests\n"
	@printf "  make check          Run the full local quality gate\n"
	@printf "  make python-build   Build the Python wheel/sdist\n"
	@printf "  make release-dry-run  Build Python package and npm tarball\n"
	@printf "  make clean          Remove local caches and build outputs\n"

setup:
	cd python && uv sync --extra dev

node-check:
	npm run lint
	npm test

lint:
	cd python && uv run ruff check .
	$(MAKE) node-check

test:
	cd python && uv run pytest -q
	npm test

python-build:
	cd python && uv build

release-dry-run: check python-build
	npm pack --dry-run

check: setup lint test
	python3 -c "import yaml; [yaml.safe_load(open(path)) for path in ('.github/workflows/ci.yml', '.github/workflows/weekly-eval.yml', '.github/workflows/codeql.yml', '.github/workflows/dependency-review.yml', '.github/workflows/release.yml', '.github/dependabot.yml', '.github/ISSUE_TEMPLATE/config.yml')]; print('yaml ok')"

clean:
	rm -rf python/.pytest_cache python/.ruff_cache python/dist python/build
	rm -rf dist build *.tgz
