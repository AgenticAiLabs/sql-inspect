.PHONY: install test rmpyc

test:
	$(MAKE) install
	pytest
	$(MAKE) rmpyc

rmpyc:
	find . -type d \( -name "__pycache__" -o -name ".pytest_cache" \) -exec rm -rf {} +

install:
	pip install -e .

deploy:
	python -m build
	twine upload dist/*

test_demo:
	pytest -s tests/test_demo.py

test_core:
	pytest -s tests/test_core.py
