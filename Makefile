.PHONY: test test-and-logs install clean publish

test:
	uv run pytest -vv tests

test-and-logs:
	uv run pytest -vvv tests -s --log-level debug -o log_cli=true --log-cli-level=DEBUG

install:
	uv --version
	uv sync --extra test
	uv run pre-commit install

clean:
	pyclean .

publish:
	uv build
	uv publish
