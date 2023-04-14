-include .env
export

PYTHON_VERSION=3.10.6

python-setup:
	pyenv install --skip-existing $(PYTHON_VERSION)
	pyenv local $(PYTHON_VERSION)

venv:
	pyenv exec python -m venv .venv
	. .venv/bin/activate && \
	pip install .

infra/remove:
	pulumi stack rm

infra/init:
	pulumi login $(INFRA_BUCKET)
	pulumi stack init organization/pipelines/main

DIR=./pipelines/$(instance)/$(layer)

infra/apply:
	PYTHONPATH=$(DIR)/ pulumi up --config-file $(DIR)/Pulumi.main.yaml
