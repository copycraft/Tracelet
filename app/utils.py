# app / utils

import tomli
import logging

logger = logging.getLogger("tracelet.utils")

def get_api_version():
    try:
        with open("pyproject.toml", "rb") as f:
            pyproject_data = tomli.load(f)

        # Adjust depending on your pyproject
        if "tool" in pyproject_data and "poetry" in pyproject_data["tool"]:
            return pyproject_data["tool"]["poetry"]["version"]
        elif "project" in pyproject_data:
            return pyproject_data["project"]["version"]
        else:
            return "unknown"
    except FileNotFoundError:
        logger.debug("pyproject.toml not found when reading API version")
        return "unknown"
    except Exception as e:
        logger.exception("error reading pyproject.toml for API version")
        return "unknown"

