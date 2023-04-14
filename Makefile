PYTHON_VERSION=3.10.6

python-setup:
	pyenv install --skip-existing $(PYTHON_VERSION)
	pyenv local $(PYTHON_VERSION)

## Using venv
venv:
	pyenv exec python -m venv .venv
	. .venv/bin/activate && \
	pip install -e

infra/init:
	pulumi login $(INFRA_BUCKET)
	pulumi stack init organization/pipelines/main

PATH=./pipelines/$(instance)/$(layer)

pipeline/apply:
	PYTHON_PATH=$(PATH) pulumi up --config-file $(PATH)/Pulumi.main.yaml
