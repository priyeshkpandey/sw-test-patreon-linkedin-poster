.PHONY: install test lint run
install:
	python3 -m venv .venv && .venv/bin/pip install -e '.[dev]' && .venv/bin/playwright install chromium
test:
	.venv/bin/pytest -q
lint:
	.venv/bin/ruff check .
run:
	.venv/bin/python -m pipeline.main run --dry-run
