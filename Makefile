all:
	poetry run mypy
	poetry run flake8
	poetry run black --diff chairmanmao
