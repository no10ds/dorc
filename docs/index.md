*dorc*  is a data orchestration library built by 10DS (Number 10 Data Science).

*dorc* enables you to define and orchestrate data pipelines with minimal Python code and automatically deploy them into any Amazon Web Services environment.

## Overview

For a *dorc* project, place the dorc repository alongside your pipeline config repository. The *dorc* repository contains code for infrastructure deployment and models for config and pipeline definitions.

The visual representation below depicts a typical *dorc* setup, illustrating the above description.

![dorc Overview](./images/dorc_overview.png)

## Motivation for *dorc*

At Number 10, we faced the challenge of abstracting away the complex infrastructure code required when building a data orchestration project from a repository. Our goal was to enable data scientists and analysts to focus on writing pure pipeline code without having to deal with custom infrastructure-as-code or maintain extensive lists of configuration files.

Additionally, we aimed for the orchestration to be cost-effective, scalable, and easy for scientists to learn. While Prefect, Dagster, and Airflow offer a good infrastructure abstraction from the repository, they are not inherently serverless and require the deployment of multiple services.

*dorc* was created to address these concerns. It is built entirely on AWS and embraces a serverless approach. Under the hood, *dorc* leverages AWS Lambdas and Step Functions, a highly scalable service for distributed orchestration.
