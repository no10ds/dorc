-include .env
export

PYTHON_VERSION=3.10.6

AWS_REGION=eu-west-2

python-setup:
	pyenv install --skip-existing $(PYTHON_VERSION)
	pyenv local $(PYTHON_VERSION)

venv:
	pyenv exec python -m venv .venv
	. .venv/bin/activate && \
	pip install -r requirements.txt

infra/init:
	pulumi login $(INFRA_BUCKET)


DIR=../Pipelines-Config/src/$(instance)/$(layer)/
infra/apply:
	PYTHONPATH=$(DIR) pulumi stack select $(instance)-$(layer) --create
	PYTHONPATH=$(DIR) pulumi up --config-file $(DIR)/Pulumi.main.yaml

infra/apply-universal:
	PYTHONPATH=../Pipelines-Config/universal/ pulumi stack select universal --create
	PYTHONPATH=../Pipelines-Config/universal/ pulumi up --config-file ../Pipelines-Config/universal/Pulumi.universal.yaml