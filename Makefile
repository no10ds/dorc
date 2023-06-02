-include .env
export

PYTHON_VERSION=3.11.0

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
DIR = $(CONFIG_REPO_PATH)/src/$(layer)/$(instance)
DIR_UNIVERSAL = $(CONFIG_REPO_PATH)/$(UNIVERSAL_STACK_NAME)
DIR_INFRA = $(CONFIG_REPO_PATH)/$(INFRA_STACK_NAME)

infra/set-stack:
	PYTHONPATH=$(dir) pulumi stack select $(stack) --create

infra/apply:
ifeq ($(instance), $(UNIVERSAL_STACK_NAME))
	make infra/set-stack stack=universal dir=$(DIR_UNIVERSAL)
	PYTHONPATH=$(DIR_UNIVERSAL) pulumi up --config-file $(DIR_UNIVERSAL)/Pulumi.$(UNIVERSAL_STACK_NAME).yaml --show-replacement-steps $(ARGS)
else ifeq ($(instance), $(INFRA_STACK_NAME))
	make infra/set-stack stack=$(INFRA_STACK_NAME)-$(env) dir=$(DIR_INFRA)
	PYTHONPATH=$(DIR_INFRA) pulumi up --config-file $(DIR_INFRA)/Pulumi.$(env).yaml --show-replacement-steps $(ARGS)
else
	make infra/set-stack stack=$(layer)-$(env)-$(instance) dir=$(DIR)
	PYTHONPATH=$(DIR) pulumi up --config-file $(DIR)/Pulumi.$(env).yaml --show-replacement-steps $(ARGS)
endif

infra/destroy:
ifeq ($(instance), $(UNIVERSAL_STACK_NAME))
	make infra/set-stack stack=universal dir=$(DIR_UNIVERSAL)
	PYTHONPATH=$(DIR_UNIVERSAL) pulumi destroy --config-file $(DIR_UNIVERSAL)/Pulumi.$(UNIVERSAL_STACK_NAME).yaml $(ARGS)
else ifeq ($(instance), $(INFRA_STACK_NAME))
	make infra/set-stack stack=$(INFRA_STACK_NAME)-$(env) dir=$(DIR_INFRA)
	PYTHONPATH=$(DIR_INFRA) pulumi destroy --config-file $(DIR_INFRA)/Pulumi.$(env).yaml $(ARGS)
else
	make infra/set-stack stack=$(layer)-$(env)-$(instance) dir=$(DIR)
	PYTHONPATH=$(DIR) pulumi destroy --config-file $(DIR)/Pulumi.$(env).yaml $(ARGS)
endif

test:
	pytest -s -vv --disable-warnings
