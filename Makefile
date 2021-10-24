all: lint test

lint:
	poetry run mypy
	poetry run flake8
	poetry run black --diff chairmanmao server

test:
	poetry run pytest
