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

# Define common variables
DIR = $(CONFIG_REPO_PATH)/src/$(instance)/$(layer)
DIR_UNIVERSAL = $(CONFIG_REPO_PATH)/$(UNIVERSAL_STACK_NAME)

infra/set-stack:
	PYTHONPATH=$(dir) pulumi stack select $(stack) --create

infra/apply:
ifeq ($(instance), $(UNIVERSAL_STACK_NAME))
	make infra/set-stack stack=universal dir=$(DIR_UNIVERSAL)
	PYTHONPATH=$(DIR_UNIVERSAL) pulumi up --config-file $(DIR_UNIVERSAL)/Pulumi.$(UNIVERSAL_STACK_NAME).yaml -r --show-replacement-steps
else
	make infra/set-stack stack=$(instance)-$(layer)-$(ENVIRONMENT) dir=$(DIR)
	PYTHONPATH=$(DIR) pulumi up --config-file $(DIR)/Pulumi.$(ENVIRONMENT).yaml --show-replacement-steps
endif

infra/destroy:
ifeq ($(instance), $(UNIVERSAL_STACK_NAME))
	make infra/set-stack stack=universal dir=$(DIR_UNIVERSAL)
	PYTHONPATH=$(DIR_UNIVERSAL) pulumi destroy --config-file $(DIR_UNIVERSAL)/Pulumi.$(UNIVERSAL_STACK_NAME).yaml
else
	make infra/set-stack stack=$(instance)-$(layer)-$(ENVIRONMENT) dir=$(DIR)
	PYTHONPATH=$(DIR) pulumi destroy --config-file $(DIR)/Pulumi.$(ENVIRONMENT).yaml
endif