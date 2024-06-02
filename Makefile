test:
	poetry run pytest -vv tests

install:
	poetry --version
	poetry install

clean:
	pyclean .
