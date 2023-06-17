from utils.constants import LAMBDA_HANDLER_FILE


def path_to_name(path: str, seperator: str = "-") -> str:
    return (
        path.strip("/")
        .replace("/", seperator)
        .replace("-", seperator)
        .replace("_", seperator)
    )


def extract_lambda_name_from_filepath(file_path: str) -> str:
    return path_to_name(file_path.replace(f"/{LAMBDA_HANDLER_FILE}", ""))
