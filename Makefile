TAG := $(shell tq --raw -f pyproject.toml 'project.version')

test:
	uv run pytest -s --reuse-db --cov-report=xml  --cov-report=html --cov-report=term:skip-covered --cov=toml_decouple

bump:
	uv version --bump minor
	@echo ""
	@echo Run this:
	@echo "$ git commit -a --amend --no-edit"
	@echo "$ make publish"

publish:
	git tag -a $(TAG) -m v$(TAG)
	git push --tags
	gh release create --notes-from-tag $(TAG)
