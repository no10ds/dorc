*dorc* ships with pipeline template code that allows for the easy creation of pipelines and pipeline functions.

## Pipeline Template

To create a new base pipeline from the template run the command

```
make create/pipeline
```

This will ask for the following prompts

```
1. Enter the pipeline layer
2. Enter the pipleline instance name
3. Enter the pipeline environment
4. Enter the folder in which to place the pipeline
5. Enter a description for this pipeline (Defaults to an empty string)
6. Enter the name of the first function (Defaults to function1)
```

> Note: To run the command you need to ensure that the [virtual environment](/getting_started/#setup) and required [environment variables](/getting_started/#environment-variables) have been setup first.

The pipeline will then be created under the folder `src/{layer}/{instance}` and have the relevant `__main__.py`, `pulumi.env.yaml` and lambda code setup.

### Custom Templates

It is possible to define your own pipeline templates depending on what structure you want to give to your pipelines. *dorc* uses Jinja2 templating under the hood and the two following templates

***pipeline_template.tpl***

```python
{{imports}}
{{config}}
{{handler}}
```

***function_template.tpl***

```python
{% if rapid_enabled %}
import os

from rapid import Rapid
from rapid import RapidAuth

rapid_url = os.getenv("RAPID_URL")
rapid_client_key = os.getenv("RAPID_CLIENT_KEY")
rapid_client_secret = os.getenv("RAPID_CLIENT_SECRET")

rapid = Rapid(auth=RapidAuth(rapid_client_key, rapid_client_secret, url=rapid_url))
{% endif %}

def handler(event, context):
    print("HELLO WORLD")

    return {"statusCode": 200, "body": "Hello World"}
```

Say for instance you require a different config setup to the one in the default template in your custom pipeline template you can remove the default config template and pass your own like the example below

```python
{{imports}}

# Custom config setup
from utils.config import create_config()
config = create_config()

{{handler}}
```

It is recommended to store your custom temlates inside your private source code repository and to tell *dorc* where these templates are you just need to set the `PIPELINE_TEMPLATE_PATH` environment variable. Note that if you do override the pipeline template path you will need both a `pipeline_template.tpl` and `function_template.tpl` in your private source code repoistory.

```
PIPELINE_TEMPLATE_PATH="../private-source-code/templates/pipeline/"
```
