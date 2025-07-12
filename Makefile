# Makefile for Plugwise Pi project

.PHONY: help install test clean lint format docs run-collector run-api deploy

# Default target
help:
	@echo "Plugwise Pi - Available commands:"
	@echo "  install      - Install dependencies"
	@echo "  test         - Run tests"
	@echo "  clean        - Clean build artifacts"
	@echo "  lint         - Run linting"
	@echo "  format       - Format code with black"
	@echo "  docs         - Generate documentation"
	@echo "  run-collector - Run the data collector"
	@echo "  run-api      - Run the API server"
	@echo "  deploy       - Deploy to Raspberry Pi"

# Install dependencies
install:
	python3 -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt

# Run tests
test:
	. venv/bin/activate && python -m pytest tests/ -v

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .coverage
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

# Run linting
lint:
	. venv/bin/activate && flake8 plugwise_pi/ tests/
	. venv/bin/activate && mypy plugwise_pi/

# Format code
format:
	. venv/bin/activate && black plugwise_pi/ tests/

# Generate documentation
docs:
	. venv/bin/activate && python -c "import plugwise_pi; print('Documentation generation not yet implemented')"

# Run the data collector
run-collector:
	. venv/bin/activate && python -m plugwise_pi.collector

# Run the API server
run-api:
	. venv/bin/activate && python -m plugwise_pi.api

# Deploy to Raspberry Pi (requires SSH access)
deploy:
	@echo "Deploying to Raspberry Pi..."
	@echo "Make sure you have SSH access to your Raspberry Pi"
	@echo "Update the IP address in the command below:"
	@echo "rsync -avz --exclude='venv' --exclude='data' --exclude='logs' . pi@YOUR_PI_IP:/home/pi/plugwise_pi/"

# Development setup
dev-setup: install
	cp config/config.example.yaml config/config.yaml
	@echo "Development setup complete!"
	@echo "Edit config/config.yaml with your settings"

# Quick test
quick-test:
	. venv/bin/activate && python tests/test_basic.py

# Check project structure
check-structure:
	@echo "Checking project structure..."
	@test -f README.md || echo "Missing README.md"
	@test -f requirements.txt || echo "Missing requirements.txt"
	@test -f setup.py || echo "Missing setup.py"
	@test -d plugwise_pi || echo "Missing plugwise_pi directory"
	@test -d tests || echo "Missing tests directory"
	@test -d config || echo "Missing config directory"
	@test -f config/config.example.yaml || echo "Missing config.example.yaml"
	@echo "Structure check complete!"

# Install development dependencies
install-dev: install
	. venv/bin/activate && pip install black flake8 mypy pytest pytest-cov

# Run all checks
check: format lint test
	@echo "All checks passed!"

# Create release
release:
	@echo "Creating release..."
	. venv/bin/activate && python setup.py sdist bdist_wheel
	@echo "Release created in dist/"

# Install in development mode
install-dev-mode:
	. venv/bin/activate && pip install -e .

# Uninstall development mode
uninstall-dev-mode:
	. venv/bin/activate && pip uninstall plugwise-pi -y 