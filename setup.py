from setuptools import setup, find_packages

setup(
    name="Pipelines",
    packages=find_packages(include=["infrastructure"]),
    include_package_data=True,
)
