.PHONY: format lint test-smoke

format:
	black .
	isort .

lint:
	@echo "lint target not implemented"

test-smoke:
	pytest tests/test_smoke.py
