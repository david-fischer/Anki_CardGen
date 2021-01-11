#!/usr/bin/env python3
"""Script to render jinja-blocks in ``README.md``."""
import glob
import re
import subprocess

import jinja2
import toml

JINJA_BLOCK_REGEX = r"<!-- jinja-block (\w*)(.*)jinja-block \1-->"
JINJA_OUT_REGEX = r"<!-- jinja-out %s.*-->"


def get_reqs_urls_summaries():
    with open("pyproject.toml") as file:
        parsed_toml = toml.load(file)
    reqs = [
        req
        for req in parsed_toml["tool"]["poetry"]["dependencies"].keys()
        if req != "python"
    ]
    urls = []
    summaries = []
    for package in reqs:
        pip_info = execute_command(f"pip show {package}")
        url = re.search("^Home-page: (.*)", pip_info, re.MULTILINE)[1]
        summary = re.search("^Summary: (.*)", pip_info, re.MULTILINE)[1]
        urls.append(url)
        summaries.append(summary)
    return reqs, urls, summaries


# https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
def escape_ansi(string):
    """Remove ansi-codes from help text."""
    ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", string)


def execute_command(command_string, remove_ansi=True):
    """
    Call command string in shell-environment.

    Args:
        remove_ansi: Defaults to True. If True, ansi-codes are removed from output.

    """
    out = (
        subprocess.check_output(command_string, shell=True, stderr=subprocess.STDOUT)
        .decode("utf-8")
        .strip()
    )
    return escape_ansi(out) if remove_ansi else out


def get_jinja_out_regex(block_name):
    return (
        rf"(?<=<!-- jinja-out {block_name} start-->)"
        r".*"
        rf"(?=<!-- jinja-out {block_name} end-->)"
    )


def get_jinja_blocks(string):
    return re.findall(JINJA_BLOCK_REGEX, string, flags=re.DOTALL)


def render_single_block(block, **kwargs):
    template = jinja2.Template(
        block,
        line_statement_prefix="$",
        line_comment_prefix="$$",
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    return template.render(**kwargs)


def refresh_single_output(file_string, block_name, replacement):
    pattern = get_jinja_out_regex(block_name)
    return re.sub(pattern, replacement, file_string, flags=re.DOTALL)


def get_render_kwargs():
    img_files = sorted(glob.glob("screenshots/*.png"))
    words = [
        {"name": name.split("/")[-2], "sides": sorted(glob.glob(f"{name}*.png"))}
        for name in sorted(glob.glob("screenshots/*/"))
    ]
    comment_tag = "<!-- -->"
    reqs, urls, summaries = get_reqs_urls_summaries()
    dep_strings = [
        f" * [{req}]({url}) - {summary}"
        for req, url, summary in zip(reqs, urls, summaries)
    ]
    return {**locals(), "execute_command": execute_command}


def main():
    file_name = "README.md"
    with open(file_name, "r") as file:
        file_string = file.read()

    render_kwargs = get_render_kwargs()
    for name, block in get_jinja_blocks(file_string):
        out_block = render_single_block(block, **render_kwargs)
        print(name)
        print(out_block)
        file_string = refresh_single_output(file_string, name, out_block)
    with open(file_name, "w") as file:
        file.write(file_string)


if __name__ == "__main__":
    main()
