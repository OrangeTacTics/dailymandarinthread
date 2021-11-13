all: lint test

lint:
	poetry run mypy || exit
	poetry run flake8 || exit
	poetry run black --diff --check chairmanmao server || exit
	poetry run schema --diff || exit

test:
	poetry run pytest || exit

containers:
	podman build -t chairmanmao-bot:latest    -f Dockerfile.chairmanmao-bot
	podman build -t chairmanmao-server:latest -f Dockerfile.chairmanmao-server
