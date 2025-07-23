test:
	uv run pytest -Wi --reuse-db --cov-report=xml --cov-report=term:skip-covered --cov=toml_decouple
