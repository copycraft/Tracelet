# app / utils

import tomli

def get_api_version():
    with open("pyproject.toml", "rb") as f:
        pyproject_data = tomli.load(f)

    # Adjust depending on your pyproject
    if "tool" in pyproject_data and "poetry" in pyproject_data["tool"]:
        return pyproject_data["tool"]["poetry"]["version"]
    elif "project" in pyproject_data:
        return pyproject_data["project"]["version"]
    else:
        return "unknown"
