all: lint test

lint:
	poetry run mypy || exit
	poetry run flake8 || exit
	poetry run black --diff --check chairmanmao server || exit

test:
	poetry run pytest || exit
