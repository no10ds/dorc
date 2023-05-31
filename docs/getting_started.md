To get started with deploying a new data orchestration project with *dorc* follow the guide below.

## Prerequisites

Before you get started with *dorc* you will need to ensure the following are setup before

* AWS - *dorc* is built upon AWS and therefore requires a valid AWS environment setup and with the relevant cli access permissions. We recommend using [aws-vault](https://github.com/99designs/aws-vault) as a way to securely handle AWS credentials.
* pyenv - *dorc* uses [pyenv](https://github.com/pyenv/pyenv) to ensure the relevant version of Python is running.
* Pulumi - See the [documentation](https://www.pulumi.com/docs/install/) on how to install Pulumi based on your relevant platform.

## Folder Structure

The recommended folder structure of a new *dorc* project is below. Within a root directory of your choosing you would have the most recent *dorc* project cloned alongside your private source code repository.

```
/root
    /dorc
    /private-source-code
        /universal
        /infra
        /src
```

## Private Source Code Repository

*dorc* is designed to be run alongside your private source code repository where all your unique pipeline and configuration sits.

There is however a requirement on the folder structure of this private repository. A typical structure is seen above with the three different folders.

* `universal` - Used to handle and run the *dorc* universal infrastructure.
* `infra` - Used to handle and run the *dorc* infra infrastructure. This infrastructure can be deployed to different environments.
* `src` - Where the core pipeline source code lives.

Typically once a project is setup you would expect the bulk of the code changes to be happening within the `src` folder.

### Environments

Just like any standard software we recommend running your *dorc* project in multiple environments. A typical setup is to have a `dev`, `preprod` and `prod` environment. The software moves along these environments sequentially, tested in each environment before reaching production. *dorc* allows for all your data orchestration to be replicated across different environments of your choosing. The only deployment in *dorc* that is environment agnostic is the universal infrastructure.

If you don't require anymore than one environment we recommend calling this `prod`.

### Layers

We recommend building your *dorc* project with the concept of data pipeline layers in mind. A typical first layer is to take data from a raw source and clean into a standardised form. A typical second layer might be taking this cleaned data and performing aggregations or filters to produce a processed layer. We could then join together multiple processed datasets into richer curated sources.

For a *dorc* project we would reference this structure within the `src` folder like the following, note that example is typically the high level name of the specific pipeline you are willing to create

```
/private-source-code
    /src
        /example
            /raw
            /processed
            /curated
        Dockerfile
```

See further [reading](https://medium.com/codex/data-pipeline-architecture-variety-of-ways-you-can-build-your-data-pipeline-66b3dd456df1) if unsure on a typical data engineering structure.

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
* CONFIG_REPO_PATH - The directory path that points to your private source code folder. For the recommended structure above this value would be `../private-source-code`
* UNIVERSAL_STACK_NAME - The folder location & name of the infrastructure stack that the universal infrastructure will be deployed too. **We recommend leaving this as *universal* if possible**.
* INFRA_STACK_NAME - The folder location & name of the infrastructure stack that the infra infrastructure will be deployed too. **We recommend leaving this as *infra* if possible**.
* PULUMI_CONFIG_PASSPHRASE -

## Dockerfile

*dorc* builds all function code into Docker images and uses these images to deploy serverless lambda functions. The context of the Dockerfile can be set to the following

```Dockerfile
FROM amazon/aws-lambda-python:3.9

ARG CODE_PATH

COPY ${CODE_PATH}/* ${LAMBDA_TASK_ROOT}/

CMD [ "lambda.handler" ]
```

## Setup

All of the commands used within a *dorc* project are exposed as Make commands. Perform the following sequence to get started

1. `make python-setup` - Installs the relevant Python version using pyenv
2. `make venv` - Creates the Python virtual environment and installs all relevant packages
3. `. .venv/bin/activate` - Activate the virtual environment
4. `pip install -e ../private-source-code` - It is also recommended to install your python private source code repository into the virtual environment so common modules are found
5. `make infra/init` - Initialise the Pulumi infrastructure. You will need to ensure you have the relevant aws access available within the shell

## Universal Infrastructure

Using the same folder structure as previously mentioned and with the `UNIVERSAL_STACK_NAME=universal` environment variables set we can use *dorc* to handle all the universal project infrastructure. *dorc* exports a Universal creator Python class.

Create a `__main__.py` within the universal folder (or the name you specified in the `UNIVERSAL_STACK_NAME` environment variable). Then create a `Pulumi.universal.yaml` in the same directory.

```
/private-source-code
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

Now under the *dorc* repository and in the virtual environment created by *dorc*, we apply the universal infrastructure using the common *dorc* `infra/apply` command.

```
make infra/apply instance=universal
```

TODO - Link this to further documentation on the infra/apply command

## Infra Infrastructure

Building on the universal setup we now want to apply the environment specific environment. For this guide we are only dealing with a **prod** environment but it can easily extended to whatever environments you require.

Create the folder that you specified for the `INFRA_STACK_NAME` and the required `__main__.py` file. For every environment you wish to create you will need to create a relevant `Pulumi.{env}.yaml` file.

```
/private-source-code
    /universal
        .
        .
        .
    /infra
        __main__.py
        Pulumi.prod.yaml
```

Within the `Pulumi.prod.yaml` we need to set the environment configuration variable

```yaml
config:
  environment: prod
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
