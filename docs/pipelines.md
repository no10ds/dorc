Once the project setup has been completed and we have both the universal and infra infrastructure created with *dorc* we can start building the pipelines.

## Pipeline Structure

As previously mentioned a pipeline consists of a high level name, the layer for which we might reference this pipeline logic and the environment for which we want to deploy it to.

Say we have a data source, the census, that we can pull in raw from an api and want to manipulate in certain ways so it is compatiable with a machine learning model we have deployed later in our processes. We can setup the *dorc* pipeline structure as the following

```
/pipeline-config
    /src
        /census
            /raw
                /src
                    /function1
                        lambda.py
                __main__.py
                Pulumi.prod.yaml
                Pulumi.preprod.yaml
            /processed
                /src
                    /function1
                        lambda.py
                    /function2
                        lambda.py
                __main__.py
                Pulumi.prod.yaml
                Pulumi.preprod.yaml
```

We can see we define a new pipeline called census under the `src` folder. Next we define our two layers, raw and processed. Our raw pipeline will simply pull the census from the api and save into a temporary holding store. The second layer is our processed pipeline which will take the raw from this holding store, perform our aggreations and transformations to get the data into a valid state for our model.

## Pipeline Creator

Once setup we can now use the *dorc* pipeline creator to deploy and replicate our pipeline to our different environments. In the `__main__.py` file we create a *dorc* pipeline like the following

```python
from infrastructure.core.Creator import CreatePipeline
from infrastructure.core.models.definition import (
    PipelineDefinition,
    Function
)

pipeline_definition = PipelineDefinition(
    file_path=__file__,
    description="Pulls raw census data from API",
    functions=[
        Function(name="function1"),
        # Function(name="function1", next_function="function2"),
        # Function(name="function2")
    ]
)

pipeline = CreatePipeline(config, pipeline_definition)
pipeline.apply()
```

To deploy this into our environment we would use the relevant *dorc* make command

```
make infra/apply instance=census layer=raw env=prod
```

## Functions

A core concept of *dorc* is to breakdown your data pipelines into reusable chunks that can then get called in a predefined order.

*dorc* will read all folders inside the unique pipeline `src` folder as pipeline functions, where the name of the folder is the name of the pipeline function. All code and files within this folder will then be packaged up and deployed as a serverless function.

The pattern for a *dorc* function is to have a `lambda.py` file with the following function definition

```python
def handler(event, context):

    # ...
    # Do your logic here
    # ...

    return {"statusCode": 200, "body": "your response"}
```
