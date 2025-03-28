import os

__all__ = ["LockFileUtils", "JobManager", "JobLister", "EmailNotifier", "JobRunner"]

modules_import_as_is = []

if os.getenv("STATIC_IMPORTS", "false").lower() == "true":
    from .LockFileUtils import *
    from .JobManager import *
    from .JobLister import *
    from .EmailNotifier import *
    from .JobRunner import *
else:
    # import modules accordingly
    for module in __all__:
        if module in modules_import_as_is:
            exec(f"from . import {module}")
        else:
            exec(f"from .{module} import *")
