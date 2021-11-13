all: lint test

lint:
	poetry run mypy || exit
	poetry run flake8 || exit
	poetry run black --diff --check chairmanmao server || exit
	poetry run schema --diff || exit

test:
	poetry run pytest || exit

containers:
	podman build -t dmt-chairmanmao:latest    -f Dockerfile
