.PHONY: test test-and-logs install clean publish

test:
	uv run pytest -vv tests

test-and-logs:
	uv run pytest -vvv tests -s --log-level debug -o log_cli=true --log-cli-level=DEBUG

test-coverage:
	uv run pytest -vv tests --cov=ranking_table_tennis --cov-report=term-missing

install:
	uv --version
	uv sync --extra test
	uv run pre-commit install

update-deps:
	uv sync --upgrade --extra test

clean:
	pyclean .

publish:
	uv build
	uv publish
