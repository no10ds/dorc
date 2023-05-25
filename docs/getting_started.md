To get started with deploying a new data orchestration project with *dorc* follow the guide below.

## Prerequisites

Before you get started with *dorc* you will need to ensure the following are setup before

* AWS - *dorc* is built upon AWS and therefore requires a valid AWS environment setup and with the relevant cli access permissions. We recommend using [aws-vault](https://github.com/99designs/aws-vault) as a way to securely handle AWS credentials.
* Pulumi - See the [documentation](https://www.pulumi.com/docs/install/) on how to install Pulumi based on your relevant platform.

## Folder structure



```
/main
    /dorc
    /private-source-code
```