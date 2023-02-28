# Installs dependencies
install:
	pipenv install

# Runs application
run:
	python asgi_server.py

# Runs tests
test:
	pytest

# Runs tests with coverage
test-cover:
	pytest --cov=konsensus tests/

format:
	black konsensus

lint:
	pylint konsensus
