.PHONY: help install test send quiet verbose debug check-branding check-newsletter check-theme analyze-branding clean

help:
	@echo "Ghost Newsletter Sender - Available Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Core Commands:"
	@echo "  test             Dry-run: send test email to GHOST_TEST_EMAIL"
	@echo "  send             Send newsletter to all subscribers (requires confirmation)"
	@echo ""
	@echo "Output Control:"
	@echo "  quiet            Dry-run with minimal output (verbosity=0)"
	@echo "  verbose          Dry-run with detailed output (verbosity=2)"
	@echo "  debug            Dry-run with debug output (verbosity=3)"
	@echo ""
	@echo "Ghost API Inspection:"
	@echo "  check-branding   Check branding settings from Ghost API"
	@echo "  check-newsletter Check newsletter configuration from Ghost API"
	@echo "  check-theme      Check theme information from Ghost API"
	@echo "  analyze-branding Comprehensive branding capability analysis"
	@echo ""
	@echo "Setup:"
	@echo "  install          Sync dependencies with uv"
	@echo "  clean            Remove uv-managed .venv directory"
	@echo ""
	@echo "Examples:"
	@echo "  make test                              # Test with default settings"
	@echo "  make send                              # Send to all subscribers (with confirmation)"
	@echo "  make quiet                             # Minimal output test"
	@echo ""

install:
	uv sync

test:
	uv run python ghost.py

send:
	@echo "⚠️  WARNING: This will send the newsletter to ALL subscribers"
	@echo ""
	@read -p "Type 'yes' to confirm sending to all subscribers: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		uv run python ghost.py --send; \
	else \
		echo "Send cancelled."; \
		exit 1; \
	fi

quiet:
	uv run python ghost.py --verbosity 0

verbose:
	uv run python ghost.py --verbosity 2

debug:
	uv run python ghost.py --verbosity 3

check-branding:
	uv run python ghost.py --check-branding

check-newsletter:
	uv run python ghost.py --check-newsletter

check-theme:
	uv run python ghost.py --check-theme

analyze-branding:
	uv run python ghost.py --analyze-branding

clean:
	rm -rf .venv

.DEFAULT_GOAL := help
