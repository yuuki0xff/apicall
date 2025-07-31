PYTHON=python3

all: format test

format:
	$(PYTHON) -m yapf -p -i -r setup.py apicall/ tests/

test:
	$(PYTHON) -m mypy -p apicall
	$(PYTHON) -m pytest tests/
