"""Utils functions."""
import inspect
import os
from datetime import datetime
from functools import wraps

import click
import titlecase


def iter_prompt(old_dict):
    """Yield dicts with user-input as values."""
    for (key, val) in old_dict.items():
        prompt_text = titlecase.titlecase(key.replace("_", " "))
        yield {key: click.prompt(prompt_text, default=val, show_default=bool(val))}


def dict_prompt(**old_dict):
    """Return dict with user-input as values."""
    new_dict = {}
    for (key, val) in old_dict.items():
        prompt_text = titlecase.titlecase(key.replace("_", " "))
        new_dict[key] = click.prompt(prompt_text, default=val, show_default=bool(val))
    return new_dict


def now_str(time=False):
    """Return string to be used as time-stamp."""
    now = datetime.now()
    return now.strftime(f"%Y-%m-%d{('_%H:%M:%S' if time else '')}")


def force_argtypes(*arg_types, **kwarg_types):
    """Enforce arg-types for function."""

    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(
                *[a if isinstance(a, t) else t(a) for a, t in zip(args, arg_types)],
                **{
                    k: v
                    if k not in kwarg_types or isinstance(v, kwarg_types[k])
                    else kwarg_types[k](v)
                    for k, v in kwargs.items()
                },
            )

        return wrapper

    return inner


def defaults_from_dict(arg_dict, as_type=None):
    """Replace ``None`` as default value of kwargs by the ones found in ``arg_dict``."""

    def inner(func):
        default_kwargs = {
            k: v.default for k, v in inspect.signature(func).parameters.items()
        }
        new_defaults = {
            k: v or (arg_dict[k] if not as_type else as_type(arg_dict[k]))
            for k, v in default_kwargs.items()
        }

        @wraps(func)
        def wrapper(*args, **kwargs):
            for k, v in new_defaults.items():
                kwargs.setdefault(k, v)
            return func(
                *args,
                **kwargs,
            )

        return wrapper

    return inner


def kwargs_to_flags(**kwargs):
    """Convert `kwargs` to flags to pass on to CLI."""
    flag_strings = []
    for (key, val) in kwargs.items():
        if isinstance(val, bool):
            if val:
                flag_strings.append(f"--{key}")
        else:
            flag_strings.append(f"--{key}={val}")
    return " ".join(flag_strings)


class CD:
    """Context manager for changing the CWD to :attr:`new_path`."""

    def __init__(self, new_path):
        self.new_path = os.path.expanduser(new_path)
        self.saved_path = None

    def __enter__(self):
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)
