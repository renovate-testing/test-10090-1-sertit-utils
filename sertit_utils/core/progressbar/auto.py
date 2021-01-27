"""
Enables multiple commonly used features.

Method resolution order:

- `sertit_utils.core.progressbar.arcypy` without import warnings
- `sertit_utils.core.progressbar.silent` for cases where progress bars aren't appropriate (e.g. celery)
- `sertit_utils.core.progressbar.tqdm` otherwise

Usage:
>>> from sertit_utils.core.progressbar.auto import progressbar
>>> for i in progressbar(range(100)):
...     ...
"""
import os
import sys
import warnings


def __is_console():
    if sys.stdout.isatty():  # Terminal is running
        return True

    if getattr(sys, 'gettrace', None) is not None:
        # This checks if a debugger is running
        # PyDevConsole starts a debugger session
        return True

    return False


def __get_progressbar():
    with warnings.catch_warnings():
        try:
            from .arcpy import progressbar as arcpy_progressbar
            return arcpy_progressbar
        except ModuleNotFoundError:
            pass # Ignore

        if not __is_console():
            from .silent import progressbar as silent_progressbar
            return silent_progressbar

        from .tqdm_auto import progressbar as tqdm_progressbar
        return tqdm_progressbar


progressbar = __get_progressbar()
__all__ = ["progressbar"]
