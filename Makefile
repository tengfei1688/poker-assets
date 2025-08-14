.PHONY: setup process clean

VENV ?= .venv

setup:
	python -m venv $(VENV)
	$(VENV)/bin/pip install -U pip
	$(VENV)/bin/pip install -r requirements.txt

process:
	$(VENV)/bin/python scripts/pipeline.py

clean:
	rm -rf frames_raw frames_clean outputs .cache $(VENV)