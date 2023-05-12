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

infra/set-stack:
	PYTHONPATH=$(DIR) pulumi stack select $(instance)-$(layer) --create

infra/apply:
	make infra/set-stack && \
	PYTHONPATH=$(DIR) pulumi up --refresh="true" --diff --config-file $(DIR)/Pulumi.main.yaml

infra/refresh:
	make infra/set-stack && \
	PYTHONPATH=$(DIR) pulumi refresh --config-file $(DIR)/Pulumi.main.yaml

infra/destroy:
	make infra/set-stack && \
	PYTHONPATH=$(DIR) pulumi destroy --config-file $(DIR)/Pulumi.main.yaml

DIR_UNIVERSAL=$(CONFIG_REPO_PATH)/$(UNIVERSAL_STACK_NAME)

infra/set-stack-universal:
	PYTHONPATH=$(DIR_UNIVERSAL) pulumi stack select universal --create

infra/apply-universal:
	make infra/set-stack-univesal && \
	PYTHONPATH=$(DIR_UNIVERSAL) pulumi up --config-file $(DIR_UNIVERSAL)/Pulumi.$(UNIVERSAL_STACK_NAME).yaml

infra/destroy-universal:
	make infra/set-stack-univesal && \
	PYTHONPATH=$(DIR_UNIVERSAL) pulumi destroy --config-file $(DIR_UNIVERSAL)/Pulumi.$(UNIVERSAL_STACK_NAME).yaml
