*dorc* exposes the ability to clearly define complex data pipelines in Python code. The pipeline definition model is defined as a Pydantic model and is passed into the create pipeline instance.

## Pipeline Definition

```python
from infrastructure.core.models.definition import PipelineDefinition

PipelineDefinition(
    file_path: str
    description: Optional[str]
    functions: list[Function]
    trigger: Optional[S3Trigger | CronTrigger]
)

* `file_path` - The releative path to the pipeline `__main__.py` file. It is advised to use the python `__file__` operator for this value
* `description` - Optional description used to describe this pipeline
* `functions` - List of pipeline `Function` that will define the structure
* `trigger` - Optional aws trigger that can be used to start the pipeline, choice between a `S3Trigger` or `CronTrigger`

## Function

The function represents a logical block of pipeline code. A pipeline will typically be made up of several different functions pointing to each other in a series of steps.

```python
from infrastructure.core.models.definition import Function

Function(
    name: str
    next_function: Optional[str | NextFunction] = None
)
```

* `name` - The name of the function. This name has to match the name of the folder created under `../src/`. For instance `../src/census_processing_raw` will have the function name of *census_processing_raw*
* `next_function` - The name of the next function to trigger once the previous function has finished processing. If this is the last function to be run in a pipline this field can be omitted or set to `None`. Otherwise you can set the string value name of next function or for more complicated cases the type of `NextFunction`

### NextFunction

```python
from infrastructure.core.models.definition import NextFunction

NextFunction(
    name: str
    type: Optional[NextFunctionTypes] = NextFunctionTypes.FUNCTION
)
```

* `name` - The string name of the next funtion to trigger (this must match the name of a relevant folder name under `../src`)
* `type` - The type of function we wish to trigger next. This is an optional value that defaults to a function but it is possible to trigger another seperate pipeline instead of a function.

#### Trigger Function

In this example we use the definition to trigger another serverless function

```python
from infrastructure.core.models.definition import Function, NextFunction, NextFunctionTypes

next_function = NextFunction(
    name: "census_processing_upload",
    type: NextFunctionTypes.FUNCTION
)

Function(
    name="census_processing_raw",
    next_function=next_function
)
```

#### Trigger Pipeline

Unlike the example above instead of triggering another function within our pipeline we wish to trigger a completely separate pipeline. This example assumes another pipeline exists with the name *train_census_model* that could for instance take the raw census data and train a model through it.

```python
from infrastructure.core.models.definition import Function, NextFunction, NextFunctionTypes

next_function = NextFunction(
    name: "train_census_model",
    type: NextFunctionTypes.PIPELINE
)

Function(
    name="census_processing_raw",
    next_function=next_function
)
```

## Trigger

We can optionally set triggers on our pipeline that based on the condition will automatically run our pipeline.

### S3 Trigger

As *dorc* is built upon aws we can trigger a pipeline on a new object being placed within a S3 bucket. This is useful to run pipelines automatically on new data entering some area.

```python
from infrastructure.core.models.definition import S3Trigger

S3Trigger(
    name: str
    bucket_name: str
    key_prefix: str
)
```

* `name` - Name to give this trigger
* `bucket_name` - Name of the S3 bucket to create the trigger for
* `key_prefix` - Path within the S3 bucket to filter for new files landing. If you wish to trigger the pipeline for every new file use the string `"/"`

### cron Trigger

You can periodically trigger your pipeline to run at defined times using a aws cron expression. This is useful if you are pulling data from a api and wish for it to be refreshed at some given cadence.

```python
from infrastructure.core.models.definition import CronTrigger

CronTrigger(
    name: str
    cron: str
)
```

* `name` - Name to give this trigger
* `cron` - String representation of a relevant aws cron. We recommend reading the [docs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html) on aws crons as these differ from regular cron definitions. For example if you wish your pipeline to be triggered every 10 minutes you can set the `cron` variable to the string `cron(0/10 * * * ? *)`
