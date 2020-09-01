#!/usr/bin/env python3
"""Script to render jinja-blocks in ``README.md``."""
import glob
import re

import jinja2

JINJA_BLOCK_REGEX = r"<!-- jinja-block (\w*)(.*)jinja-block \1-->"
JINJA_OUT_REGEX = r"<!-- jinja-out %s.*-->"


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
    return {**locals()}


def new_main():
    file_name = "README.md"
    with open(file_name, "r") as file:
        file_string = file.read()

    for name, block in get_jinja_blocks(file_string):
        render_kwargs = get_render_kwargs()
        out_block = render_single_block(block, **render_kwargs)
        file_string = refresh_single_output(file_string, name, out_block)
    with open(file_name, "w") as file:
        file.write(file_string)


if __name__ == "__main__":
    new_main()
