"""
SQL Job Scheduler - A system for managing GPU-intensive Python jobs
"""

import os

import tomli

try:
    with open("pyproject.toml", "rb") as f:
        pyproject = tomli.load(f)
        __version__ = pyproject["project"]["version"]
except Exception:
    __version__ = "unknown"


__all__ = ["LockFileUtils", "JobManager", "JobLister", "EmailNotifier", "JobRunner"]

modules_import_as_is = []

if os.getenv("STATIC_IMPORTS", "false").lower() == "true":
    from .configSetup import *
    from .EmailNotifier import *
    from .JobLister import *
    from .JobManager import *
    from .JobRunner import *
    from .LockFileUtils import *
else:
    # import modules accordingly
    for module in __all__:
        if module in modules_import_as_is:
            exec(f"from . import {module}")
        else:
            exec(f"from .{module} import *")
