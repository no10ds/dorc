*dorc* is built to include an easy integration with [rAPId](https://rapid.readthedocs.io/en/latest/) and can be optionally enabled. To enable rAPId for your pipelines you want to apply both the `rAPId_config` attribute in the configuration model and also the `rapid_layer_config` attribute in the universal configuration model.

## rAPId Integration Configuration

### rAPId Layer Configuration

The layer configuration is a block applied to the universal configuration that allows *dorc* to understand how the folder structure of your pipelines correspond to your layers within rAPId. For instance consider the folder structure of your *dorc* project below

```
/pipeline-config
    /src
        /raw-to-processed
            /example
        /processed-to-curated
            /example
        Dockerfile
```

This would typically link up to a rAPId account that would contain the three layers `raw, processed, curated`. You then tell dorc how the folder pipelines within your folder structure links to the layers by providing the `rapid_layer_config` attribute in `UniversalConfig`.

```python
from utils.config import UniversalConfig, LayerConfig

UniversalConfig(
    ...
    ...
    ...
    rapid_layer_config = [
        LayerConfig(folder='raw-to-processed', source='raw', target='processed'),
        LayerConfig(folder='processed-to-curated', source='processed', target='curated')
    ]
)
```

### rAPId Config

Alongside the layer configuration you set a further `rAPIdConfig` attribute to the `Configuration` block for environment specific details on your rAPId instance for which to use. See the [further details](/config/#rapid-configuration) on the values required.

## Pipeline rAPId Client Credentials

There are two ways to use a rAPId client within a pipeline:

1. Pass a already existing rAPId client key into the pipeline definition rAPId trigger block. If you have a more general rAPId client that you are happy with all pipelines using you can create this manually within rAPId and pass this to all pipelines.
2. Automatic creation of a rAPId client by *dorc*. If no client key is passed *dorc* will automatically create a new rAPId client for the pipeline.


## rAPId Permissions

*dorc* will automatically create a client for the pipeline because no `rapid_client_key` has been passed. When this is the case *dorc* will create the client with `READ` and `WRITE` permissions for the domain specified as well as the rAPId `PRIVATE` permission for both the source and target layers read using the `rapid_layer_config`.

## Usage

To use rAPId within your pipeline function *dorc* automatically sets a client key and client secret into the function environment variables. These can read from the values:

```
RAPID_CLIENT_KEY
RAPID_CLIENT_SECRET
RAPID_URL
```
