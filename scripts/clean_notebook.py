# Copyright (C) 2015-2026 by the RBniCS authors
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

import os
import re
import time
import typing

import nbformat
import nbstripout


# -----------------------------
# Standalone notebook cleaning
# -----------------------------
def clean_notebook(os_path: str) -> None:
    """Strip outputs, metadata, and trailing spaces from a notebook file."""
    if not os.path.exists(os_path):
        return

    # Only process notebooks in certain repositories
    if not any(repository_name in os.path.dirname(os_path) for repository_name in ("REPOSITORY_NAME_PLACEHOLDER",)):
        return

    # Skip untitled notebooks
    if re.match(r"Untitled[0-9]*.ipynb$", os.path.basename(os_path)):
        return

    # Read notebook
    with open(os_path, encoding="utf8") as f:
        nb = nbformat.read(f, as_version=nbformat.NO_CONVERT)  # type: ignore[no-untyped-call]

    # Strip outputs and unnecessary metadata
    extrakeys = [
        "metadata.celltoolbar", "metadata.kernel_spec.display_name", "metadata.kernel_spec.name",
        "metadata.language_info.codemirror_mode.version", "metadata.language_info.pygments_lexer",
        "metadata.language_info.version", "metadata.toc", "metadata.notify_time", "metadata.varInspector",
        "cell.metadata.heading_collapsed", "cell.metadata.hidden", "cell.metadata.code_folding",
        "cell.metadata.tags", "cell.metadata.init_cell", "cell.metadata.scrolled",
        "cell.metadata.execution"
    ]
    nbstripout.strip_output(nb, keep_id=True, keep_output=False, keep_count=False, extra_keys=extrakeys)

    # Strip trailing whitespaces in code cells
    for cell in nb.cells:
        if cell.get("cell_type") == "code":
            cell["source"] = "\n".join(line.rstrip() for line in cell["source"].splitlines())

    # Write back
    with open(os_path, "w", encoding="utf8") as f:
        nbformat.write(nb, f)  # type: ignore[no-untyped-call]


# -----------------------------
# Jupyter post-save hook
# -----------------------------
def post_save_hook(
    model: dict[typing.Any, typing.Any],
    os_path: str,
    contents_manager: typing.Any,  # noqa: ANN401
    **kwargs: typing.Any  # noqa: ANN401
) -> None:
    """Jupyter post-save hook to clean notebooks automatically."""
    if model.get("type") != "notebook":
        return

    # Lock file mechanism
    tmp_path = os.path.join("/tmp", "jupyter_strip_output_hook", os_path + ".lock")
    os.makedirs(os.path.dirname(tmp_path), exist_ok=True)

    log = getattr(contents_manager, "log", None)

    while os.path.exists(tmp_path):
        time.sleep(1)
        if log:
            log.info(f"File {os_path} is currently locked: waiting...")

    # Create lock
    open(tmp_path, "w", encoding="utf8").close()
    if log:
        log.info(f"Created lock for {os_path}.")

    # Run the cleaning
    clean_notebook(os_path)

    # Remove lock
    os.remove(tmp_path)
    if log:
        log.info(f"Deleted lock for {os_path}.")


# Register the hook in Jupyter
try:
    c.FileContentsManager.post_save_hook = post_save_hook  # type: ignore[name-defined]
except NameError:
    # c is not defined outside Jupyter config
    pass


# -----------------------------
# CLI interface for VS Code / manual run
# -----------------------------
if __name__ == "__main__":
    import sys

    for notebook_file in sys.argv[1:]:
        clean_notebook(notebook_file)
