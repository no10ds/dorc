import os
import typer

from pathlib import Path
from jinja2 import Template, Environment, FileSystemLoader

CONFIG_REPO_PATH = os.getenv("CONFIG_REPO_PATH")

IMPORT_STRING = """
from utils.config import Config, UniversalConfig
from infrastructure.core.creator import CreatePipeline
from infrastructure.core.models.definition import (
    PipelineDefinition,
    Function,
    NextFunction
)
"""

CONFIG_STRING = """
config = Config(
    universal=UniversalConfig(
        region="CHANGE_ME",
        project="CHANGE_ME",
    ),
    vpc_id="CHANGE_ME",
    private_subnet_ids=["CHANGE_ME"]
)
"""

HANDLER_STRING = """
pipeline_definition = PipelineDefinition(
    file_path=__file__,
    description="{{ description }}",
    functions=[Function(name="{{ first_function_name }}")],
)
"""

print(os.getenv("PIPELINE_TEMPLATE_PATH", "./templates/pipeline/"))


environment = Environment(  # nosec B701
    loader=FileSystemLoader(
        os.getenv("PIPELINE_TEMPLATE_PATH", "./templates/pipeline/")
    ),
    autoescape=False,
)


def create_initial_path(source_code_folder: str, layer: str, instance: str):
    return f"{CONFIG_REPO_PATH}/{source_code_folder}/{layer}/{instance}"


def create_pipeline_template(initial_path: str, template: str):
    path = f"{initial_path}/__main__.py"
    with open(path, "w") as file:
        file.write(template)


def create_pipeline_function(
    initial_path: str, first_function_name: str, template: str
):
    path = f"{initial_path}/{first_function_name}/lambda.py"
    with open(path, "w") as file:
        file.write(template)


def create_pipeline_folders(initial_path: str, first_function_name: str) -> None:
    folder = f"{initial_path}/{first_function_name}"
    Path(folder).mkdir(parents=True, exist_ok=True)


def create_pipeline_pulumi_config(initial_path: str, pipeline_env: str) -> None:
    path = f"{initial_path}/Pulumi.{pipeline_env}.yaml"
    content = f"""
config:
    environment: {pipeline_env}
    """
    with open(path, "w") as file:
        file.write(content)


def get_inputs():
    layer = typer.prompt("Enter the pipeline layer", type=str)
    instance = typer.prompt("Enter the pipeline instance name", type=str)
    pipeline_env = typer.prompt("Enter the pipeline environment", type=str)
    source_code_folder = typer.prompt(
        "Enter the folder in which to place the pipeline",
        type=str,
        default="src",
        show_default=True,
    )
    description = typer.prompt(
        "Enter a description for this pipeline",
        type=str,
        default="",
        show_default=False,
    )
    first_function_name = typer.prompt(
        "Enter the name of the first function", type=str, default="function1"
    )

    return (
        layer,
        instance,
        pipeline_env,
        source_code_folder,
        description,
        first_function_name,
    )


def render_pipeline_template(description: str, first_function_name: str) -> str:
    template = environment.get_template("pipeline_template.tpl")
    return template.render(
        imports=IMPORT_STRING,
        config=CONFIG_STRING,
        handler=Template(HANDLER_STRING).render(
            description=description, first_function_name=first_function_name
        ),
    )


def render_function_template() -> str:
    template = environment.get_template("function_template.tpl")
    return template.render()


if __name__ == "__main__":
    (
        layer,
        instance,
        pipeline_env,
        source_code_folder,
        description,
        first_function_name,
    ) = get_inputs()
    pipeline_template = render_pipeline_template(description, first_function_name)
    function_template = render_function_template()
    initial_path = create_initial_path(source_code_folder, layer, instance)
    create_pipeline_folders(initial_path, first_function_name)
    create_pipeline_pulumi_config(initial_path, pipeline_env)
    create_pipeline_template(initial_path, pipeline_template)
    create_pipeline_function(initial_path, first_function_name, function_template)
