VENV=.venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

.PHONY: venv install lint test clean

venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

install: venv
	$(PIP) install -r requirements.txt


check-venv:
	@echo "Running venv normalization check..."
	@python3 scripts/check_single_venv.py || (echo "check_single_venv reported issues" && exit 1)


safe-grep:
	@echo "Running safe search (tracked files only, size-limited)..."
	@python3 scripts/safe_search.py "$(pattern)" "$(prefix)" || true


fix-venv-refs:
	@echo "Dry-run: show proposed replacements for absolute venv references"
	@python3 scripts/fix_venv_refs.py || true

lint:
	$(VENV)/bin/ruff . || true

test:
	$(VENV)/bin/pytest -q

clean:
	rm -rf $(VENV) build dist *.egg-info

