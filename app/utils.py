import os
import tomli

def get_api_version() -> str:
    """
    Reads the API version from pyproject.toml.
    """
    pyproject_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pyproject.toml")
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomli.load(f)
    return pyproject_data["tool"]["poetry"]["version"]  # or ["project"]["version"] depending on your pyproject
