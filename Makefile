VENV=.venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

.PHONY: venv install lint test clean

venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

install: venv
	$(PIP) install -r requirements.txt

lint:
	$(VENV)/bin/ruff . || true

test:
	$(VENV)/bin/pytest -q

clean:
	rm -rf $(VENV) build dist *.egg-info

