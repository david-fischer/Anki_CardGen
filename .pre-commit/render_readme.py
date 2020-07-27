#!/usr/bin/env python3
"""Script to render the README jinja template."""
import glob
import os

import jinja2


def main(path, overwrite=False):
    """Main function."""
    with open(path, "r") as file:
        template_string = file.read()

    template = jinja2.Template(
        template_string,
        line_statement_prefix="$",
        line_comment_prefix="$$",
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    img_files = sorted(glob.glob("screenshots/*.png"))
    words = [
        {"name": name.split("/")[-2], "sides": sorted(glob.glob(f"{name}*.png"))}
        for name in sorted(glob.glob("screenshots/*/"))
    ]
    rendered = template.render(words=words, img_files=img_files)

    # remove ".pre-commit/" and ".jinja" extension from path
    out_path = os.path.basename(os.path.splitext(path)[0])
    if not os.path.exists(out_path) or overwrite:
        with open(out_path, "w") as file:
            file.write(rendered)
    else:
        raise os.error("File exists. To overwrite, set -o flag.")


for file in glob.glob(".pre-commit/*.jinja"):
    main(file, overwrite=True)
