-include .env
export

PYTHON_VERSION=3.10.6

python-setup:
	pyenv install --skip-existing $(PYTHON_VERSION)
	pyenv local $(PYTHON_VERSION)

venv:
	pyenv exec python -m venv .venv
	. .venv/bin/activate && \
	pip install -r requirements.txt

infra/init:
	pulumi login $(INFRA_BUCKET)

DIR=$(CONFIG_REPO_PATH)/src/$(instance)/$(layer)

infra/apply:
	PYTHONPATH=$(DIR) pulumi stack select $(instance)-$(layer) --create
	PYTHONPATH=$(DIR) pulumi up --config-file $(DIR)/Pulumi.main.yaml

infra/refresh:
	PYTHONPATH=$(DIR) pulumi stack select $(instance)-$(layer)
	PYTHONPATH=$(DIR) pulumi refresh --config-file $(DIR)/Pulumi.main.yaml

DIR_UNIVERSAL=$(CONFIG_REPO_PATH)/$(UNIVERSAL_STACK_NAME)

infra/apply-universal:
	PYTHONPATH=$(DIR_UNIVERSAL) pulumi stack select universal --create
	PYTHONPATH=$(DIR_UNIVERSAL) pulumi up --config-file $(DIR_UNIVERSAL)/Pulumi.$(UNIVERSAL_STACK_NAME).yaml