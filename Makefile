# Installs dependencies
install:
	poetry install

# Runs sample script
run:
	python run.py 10

# Runs tests
test:
	pytest

# Runs tests with coverage
test-cover:
	pytest --cov=konsensus tests/

precommit:
	pre-commit run --verbose --all-files --show-diff-on-failure

format:
	black konsensus

lint:
	pylint konsensus

build:
	poetry build

publish:
	poetry build
	twine upload --verbose -u '__token__' dist/*
