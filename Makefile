TAG := $(shell tq --raw -f pyproject.toml 'project.version')

test:
	uv run --extra db pytest

typecheck:
	uv run zuban check

bump:
	uv version --bump minor
	@echo ""
	@echo Run this:
	@echo "$ git commit -a --amend --no-edit"
	@echo "$ make publish"

publish:
	git tag -a $(TAG) -m v$(TAG)
	git push
	gh release create --notes-from-tag $(TAG)
