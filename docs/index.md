*dorc*  is a data orchestration library built by 10DS.

*dorc* enables you to define and orchestrate data pipelines with minimal Python code and automatically deploy them into any Amazon Web Services environment.

## Overview

For a *dorc* projet, place the dorc repository alongside your pipeline config repository in your organization's source control. The *dorc* repository contains code for infrastructure deployment and Python models for pipeline definition. Separate your pipeline and configuration code in another repository passed to *dorc*.

The visual representation below depicts a typical *dorc* setup, illustrating the above description.

![dorc Overview](./images/dorc_overview.png)

## Motivation for *dorc*

At Number 10, we faced the challenge of abstracting away the complex infrastructure code required when building a data orchestration project from a repository. Our goal was to enable data scientists and analysts to focus on writing pure pipeline code without having to deal with custom infrastructure-as-code or maintain extensive lists of configuration files.

Additionally, we aimed for the orchestration to be cost-effective, scalable, and easy for scientists to learn. While Prefect, Dagster, and Airflow offer a good infrastructure abstraction from the repository, they are not inherently serverless and require the deployment of multiple services.

*dorc* was created to address these concerns. It is built entirely on AWS and embraces a serverless approach. Under the hood, *dorc* leverages AWS Lambdas and Step Functions, a highly scalable service for distributed orchestration.

## Structure of *dorc*

As previously mentioned, *dorc* handles all the code required to deploy serverless pipeline infrastructure. To accomplish this, *dorc* is divided into three core packages.

Universal: This package creates environment-agnostic infrastructure that is utilized across the entire stack. For example, it reads the folder structure from within the pipeline config repository, determines which pipelines will be created, and creates the respective AWS Elastic Container Registry to host the built pipeline code.

Infra: This package is responsible for environment-specific infrastructure. It includes the creation of AWS IAM roles and policies at the environment level. When pipelines are deployed to a specific environment, they utilize the infrastructure resources defined in this package.

Core: The main Python infrastructure code used when deploying a new pipeline to an environment resides in this package. The pipeline definition is defined and passed into the infrastructure. *dorc* then handles the building and deployment of each function, ultimately constructing the pipeline based on the provided definition.
