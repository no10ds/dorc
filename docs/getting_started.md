To deploy a new data orchestration project with *dorc*, follow the guide below.

## Prerequisites

Before you get started with *dorc* you will need to ensure the following are setup before

* AWS - AWS is used to create the cloud infrastructure, you therefore require an AWS environment with the relevant access and permissions. We recommend using [aws-vault](https://github.com/99designs/aws-vault) as a way of securely handling AWS credentials.
* pyenv - [pyenv](https://github.com/pyenv/pyenv) is used to install and manage the Python.
* Pulumi - Pulumi is used to deploy all the infrastructure programmatically. See the [documentation](https://www.pulumi.com/docs/install/) on how to install Pulumi.

## Folder Structure

The folder structure for setting up *dorc* is shown below. Within a directory of your choice, you will need to clone the *dorc* repo, alongside your pipeline config repository.

```
/<directory>
    /dorc
    /pipeline-config
        /universal
        /infra
        /src
        Dockerfile
        requirements.txt
```

## Pipeline Config Repository

The pipeline config repository is where your unique pipeline definition and configuration sits.

There is however a requirement on the folder structure of this private repository. A typical structure is seen above with the three different folders.

* `universal` - Used to handle and run the *dorc* universal infrastructure.
* `infra` - Used to handle and run the *dorc* infra infrastructure. This infrastructure can be deployed to different environments.
* `src` - Where the core pipeline source code lives.

Typically once a project is setup you would expect the bulk of the code changes to be happening within the `src` folder.

### Environments

Just like any standard software we recommend running your project in multiple environments. *dorc* allows for all of your data orchestration to be replicated across different environments of your choosing.

The only deployment in *dorc* that is environment agnostic is the universal infrastructure.

### Layers

Layers facilitate enable the organization of data pipelines at different levels of abstraction, promoting a structured and manageable approach to data management.

> Note: You do not have to use layers, you can just have one folder called `default` that contains all of your pipelines.

A typical data architecture might contain the following layers:

- raw-to-processed: This layer consists of pipelines responsible for transforming datasets from their raw form, performing tasks such as validation, cleaning, and wrangling, and then moving them to the processed layer. The resulting data could then be used by Data Scientists for analysis or developmet.

- processed-to-curated: This layer consists of pipelines that further refine the processed data into curated data products. Activities in this layer may involve joining multiple datasets and incorporating business logic. The resulting data could then be surfaced in visualisations.


For a *dorc* project we would reference this structure within the `src` folder like the following, note that example is typically the high level name of the specific pipeline you are willing to create.

```
/pipeline-config
    /src
        /raw-to-processed
            /example
        /processed-to-curated
            /example
        Dockerfile
        requirements.txt
```

See further [reading](https://medium.com/codex/data-pipeline-architecture-variety-of-ways-you-can-build-your-data-pipeline-66b3dd456df1) if unsure about typical data engineering structures.

## Environment Variables

The following environment variables are required. We recommend creating a `.env` within the *dorc* folder but if this is not possible, e.g. running *dorc* through automated CI/CD actions exporting the variables is required.

```
AWS_ACCOUNT=
AWS_REGION=

CONFIG_REPO_PATH=

INFRA_BUCKET=
UNIVERSAL_STACK_NAME=
INFRA_STACK_NAME=

PULUMI_CONFIG_PASSPHRASE=
```

See the description and a example for each of the variables below

* AWS_ACCOUNT - AWS Account ID, for more details see [here](https://docs.aws.amazon.com/signin/latest/userguide/FindingYourAWSId.html)
* AWS_REGION - The AWS specific region in which to deploy all the infrastructure too
* CONFIG_REPO_PATH - The relative path to your pipeline-config repo from your local dorc repo. For the recommended structure above this value would be `../pipeline-config`
* UNIVERSAL_STACK_NAME - The folder location & name of the infrastructure stack that the universal infrastructure will be deployed too. *Default value is: universal*
* INFRA_STACK_NAME - The folder location & name of the infrastructure stack that the infra infrastructure will be deployed too. *Default value is: infra*
* PULUMI_CONFIG_PASSPHRASE -

## Dockerfile

Docker is used to store and the code as images which are then deployed to serverless lambda functions. The Dockerfile can be set to the following:

```Dockerfile
FROM amazon/aws-lambda-python:3.9

ARG CODE_PATH

COPY ${CODE_PATH}/* ${LAMBDA_TASK_ROOT}/

COPY requirements.tx[t]  ./global-requirements.txt
RUN test -f global-requirements.txt && pip install -r global-requirements.txt || echo "No global requirements"

COPY ${CODE_PATH}/../requirements.tx[t] ${LAMBDA_TASK_ROOT}/
RUN test -f ${LAMBDA_TASK_ROOT}/requirements.txt && pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt || echo "No local requirements"


CMD [ "lambda.handler" ]
```

This allows for a project wide `requirements.txt` for universal wide Python packages to be installed but also for a pipeline specific `requirements.txt`.

## Setup

All of the commands used within *dorc* are exposed as `Make` commands. Perform the following sequence to get started

1. `make python-setup` - Installs the relevant Python version using pyenv
2. `make venv` - Creates the Python virtual environment and installs all relevant packages
3. `. .venv/bin/activate` - Activate the virtual environment
4. `make infra/init` - Initialise the Pulumi infrastructure. You will need to ensure you have the relevant aws access available within the shell

## Universal Infrastructure

Using the same folder structure as previously mentioned and with the `UNIVERSAL_STACK_NAME=universal` environment variables set we can use *dorc* to handle all the universal project infrastructure. *dorc* exports a Universal creator Python class.

Create a `__main__.py` within the universal folder (or the name you specified in the `UNIVERSAL_STACK_NAME` environment variable). Then create a `Pulumi.universal.yaml` in the same directory.

```
/pipeline-config
    /universal
        __main__.py
        Pulumi.universal.yaml
```

Within the `__main__.py` you want to create an instance of the *dorc* universal creator and pass it with an instance of the *dorc* universal configuration model.

```python
# These are imported from dorc
from utils.config import UniversalConfig
from infrastructure.universal import CreateUniversal

config = UniversalConfig(
    region="eu-west-2",
    project="ExampleDorc",
    tags={"project": "example-dorc"},
)

universal_infrastructure_creator = CreateUniversal(config)
universal_infrastructure_creator.apply()
```

In the *dorc* repository and in the virtual environment created by *dorc*, we apply the universal infrastructure using the common *dorc* `infra/apply` command.

```
make infra/apply instance=universal
```


## Infra Infrastructure

Building on the universal setup we now want to apply the environment specific environment.

Create the folder that you specified for the `INFRA_STACK_NAME` and the required `__main__.py` file. For every environment you wish to create you will need to create a relevant `Pulumi.{env}.yaml` file.

```
/pipeline-config
    /universal
        .
        .
        .
    /infra
        __main__.py
        Pulumi.{env}.yaml
```

Within the `Pulumi.{env}.yaml` we need to set the environment configuration variable

```yaml
config:
  environment: env
```

Now we can create and apply the *dorc* python code within the `__main__.py`

```python
from utils.config import Config
from infrastructure.infra import CreateInfra

config = Config(
    universal=YOUR_BASE_UNIVERSAL_CONFIG,
    vpc_id="aws_vpc_id",
    private_subnet_ids=["aws_private_subnet_id"],
)

infra_infrastructure_creator = CreateInfra(config)
infra_infrastructure_creator.apply()
```

Now apply the infrastructure with the relevant *dorc* command

```
make infra/apply instance=infra env=prod
```

Now we have the universal and infra infrastructure setup we can create our pipelines.
