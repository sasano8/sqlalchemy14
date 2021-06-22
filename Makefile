all: format test-local

format: format-black format-isort

format-black:
	@echo [black] && poetry run black .

format-isort:
	@echo [isort] && poetry run isort --profile black --filter-files .

test-local:
	@echo [pytest] && poetry run pytest --env=local -v .

test-docker:
	@echo [pytest] && poetry run pytest --env=docker -v .

# documentation:
# 	@rm -rf ./docs/auto
# 	@poetry run sphinx-apidoc --module-first -f -o ./docs/auto ./openapi_client_generator
# 	@poetry run sphinx-build -b singlehtml ./docs ./docs/_build