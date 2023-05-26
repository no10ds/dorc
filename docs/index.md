*dorc* is 10 Downing's Street internal data orchestration library.

*dorc* allows for serverless data projects to be defined in Python code and automatically deployed into any Amazon Web Services environment.

## Overview

Below shows a typical project structure to use when getting setup with *dorc*. Within your orginsations source control environment you would have the *dorc* repository alongside your private source code repository. *dorc* contains all the code needed to deploy all the relevant infrastructure aswell as the Python models used to define your pipelines. You would then define your pipeline and configuration code in a seperate repository that you then pass to *dorc*.

Below is a typical *dorc* setup visually describing the above.

![dorc Overview](./images/dorc_overview.png)

## Motiviation for *dorc*

In Number 10 we had the issue of how can abstact away the complex infrastructure code needed when building a data orchestration project from a repository so data scientists and analysts are just writing pure pipeline code and not having to write custom infrastrucure-as-code or maintain long lists of configuration yamls.

We also want the ability for the orchestration to be cheap, scalable and not be a learning curve for scientists. Prefect, Dagster & Airflow offer a good abstraction of the infrastructure from the repo however are not natually serverless in nature and require several different services to be deployed.

*dorc* was created as a way to address these concerns. It is built entirely upon AWS and is serverless by nature. Under the hood *dorc* utilises Amazon Step Functions a highly scalable service for distributed orchestration.

## Structure of *dorc*

As mentioned *dorc* handles all the code needed to deploy serverless pipeline infrastructure. To do this *dorc* is broken into three core packages.

- Universal - Creates non-environment specific infrastructure used across the entire stack. For instance it will read the folder structure from within the private source code repository, calculate what pipelines are going to be created an create their retrospective AWS Elastic Container Registry used to host the built pipeline code.
- Infra - For wider infrastructure that will want to be environment specific, this is created within the infra code. For instance the specific AWS IAM roles and policies will be created each at an environment level, then when pipelines are deployed to this specific environment they will use the infra resources at these environments.
- Core - The main Pythonic infrastructure code used when deploying a new pipeline to an environment. The pipeline definition is defined and passed into the infrastructure. *dorc* then handles the building and deployment of each function and finally constructs the pipeline based on the definition passed.
