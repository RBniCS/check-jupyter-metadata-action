# Copyright (C) 2015-2022 by the RBniCS authors
#
# This file is part of RBniCS-related actions.
#
# SPDX-License-Identifier: MIT
"""
Add a custom hook to strip outputs, unnecessary metadata and trailing spaces from notebooks.

Acknowledgements:
  * https://github.com/jupyterhub/jupyterhub/issues/1412
  * https://github.com/kynan/nbstripout/issues/96
  * https://github.com/jupyter/notebook/issues/1455
"""

import io
import os
import re
import time
import typing

import nbformat
import nbstripout
import notebook.services.contents.manager


def post_save_hook(
    model: dict, os_path: str, contents_manager: notebook.services.contents.manager.ContentsManager,
    **kwargs: typing.Any
) -> None:
    """Add a custom hook to strip outputs, unnecessary metadata and trailing spaces from notebooks."""
    # Only process notebooks
    if model["type"] != "notebook":
        return

    # Only process notebooks in repositories
    if not any(repository_name in os.path.dirname(os_path) for repository_name in (
            "REPOSITORY_NAME_PLACEHOLDER", )):
        return

    # Do not bother running if the notebook name ends with `Untitled[0-9]*`
    if re.compile(r"Untitled[0-9]*.ipynb$").search(os_path):
        return

    # Create a temporary directory for the lock file
    tmp_path = os.path.join("/tmp", "jupyter_strip_output_hook", os_path + ".lock")
    os.makedirs(os.path.dirname(tmp_path), exist_ok=True)

    # Wait until the lock file is present
    log = contents_manager.log
    while os.path.exists(tmp_path):
        time.sleep(1)
        log.info(f"File {os_path} is currently locked: waiting...")

    # Create lock file
    io.open(tmp_path, "w", encoding="utf8").close()
    log.info(f"Created lock for {os_path}.")

    # Read in notebook content
    with io.open(os_path, "r", encoding="utf8") as f:
        nb = nbformat.read(f, as_version=nbformat.NO_CONVERT)

    # Strip outputs and unnecessary keys
    extrakeys = [
        "metadata.celltoolbar", "metadata.kernel_spec.display_name", "metadata.kernel_spec.name",
        "metadata.language_info.codemirror_mode.version", "metadata.language_info.pygments_lexer",
        "metadata.language_info.version", "metadata.toc", "metadata.notify_time", "metadata.varInspector",
        "cell.metadata.heading_collapsed", "cell.metadata.hidden", "cell.metadata.code_folding",
        "cell.metadata.tags", "cell.metadata.init_cell", "cell.metadata.scrolled",
        "cell.metadata.execution"]
    nbstripout.strip_output(nb, keep_output=False, keep_count=False, extra_keys=extrakeys)

    # Strip trailing whitespaces
    for cell in nb.cells:
        if cell["cell_type"] == "code":
            cell["source"] = "\n".join([line.rstrip() for line in cell["source"].split("\n")])

    # Overwrite notebook content
    with io.open(os_path, "w", encoding="utf8") as f:
        nbformat.write(nb, f)

    # Delete lock file
    os.remove(tmp_path)
    log.info(f"Deleted lock for {os_path}.")


c.FileContentsManager.post_save_hook = post_save_hook  # noqa: F821
