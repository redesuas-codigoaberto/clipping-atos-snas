# Development tasks. `make` alone lists them.
# The pipeline itself needs only Python; the checks run pytest and ruff through uv (https://docs.astral.sh/uv/).
PYTHON ?= python3
PORT ?= 8000
UV_RUN = uv run --group dev

.DEFAULT_GOAL := help
.PHONY: help site serve regenerate regenerate-historico test lint format check dispatch

help: ## List the available targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  make %-12s %s\n", $$1, $$2}'

# Same build steps as "Build the site" in .github/workflows/clipping.yml.
site: ## Build the pages (index.html and relatorio.html) in site/
	rm -rf site
	$(PYTHON) scripts/report.py

serve: site ## Build site/ and serve it at http://localhost:$(PORT)/
	@echo "Preview at http://localhost:$(PORT)/ (Ctrl+C to stop)"
	$(PYTHON) -m http.server $(PORT) --bind 127.0.0.1 --directory site

regenerate: ## Rewrite clipping-novo/ from data/ with the current rules (after a rule change)
	@for index in data/??-??-????.json; do \
		day=$$(basename $$index .json); \
		if $(PYTHON) -c "import json, sys; sys.exit(not json.load(open('$$index'))['count'])"; then \
			$(PYTHON) scripts/clipping.py $$day > /dev/null || exit 1; \
		fi; \
	done
	@git diff --stat -- clipping-novo

regenerate-historico: ## Rewrite clipping-historico/ (2004-2025) from cache/historico/data with the current rules
	$(PYTHON) scripts/clippings_range.py

test: ## Run the tests
	$(UV_RUN) pytest

lint: ## Check the code with ruff, without changing it
	$(UV_RUN) ruff check .
	$(UV_RUN) ruff format --check .

format: ## Fix what ruff can and format the code
	$(UV_RUN) ruff check --fix .
	$(UV_RUN) ruff format .

check: lint test ## Run everything CI runs: lint and tests

# Starts the daily workflow on GitHub through the gh CLI (https://cli.github.com/), logged in with `gh auth login`.
# DATE=DD-MM-AAAA picks the edition; without it, the workflow uses today's date.
dispatch: ## Run the daily workflow on GitHub now (DATE=DD-MM-AAAA for another edition)
	gh workflow run clipping.yml --ref main $(if $(DATE),-f date=$(DATE))
	@echo "Follow it with: gh run watch"
