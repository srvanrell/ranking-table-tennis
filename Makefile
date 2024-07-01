test:
	poetry run pytest -vv tests

test-and-logs:
	poetry run pytest -vvv tests -s --log-level debug -o log_cli=true --log-cli-level=DEBUG

install:
	poetry --version
	poetry install

clean:
	pyclean .
