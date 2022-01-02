# Copyright (C) 2015-2022 by the RBniCS authors
#
# This file is part of RBniCS-related actions.
#
# SPDX-License-Identifier: MIT
"""
Script to check that outputs and unnecessary metadata are not contained in jupyter notebooks to be stored in git.

Acknowledgements:
  * https://github.com/kynan/nbstripout/blob/master/nbstripout/_utils.py
  * https://github.com/kynan/nbstripout/issues/96
  * https://gist.github.com/francesco-ballarin/379ba630499559fa1072b2c526e57706
"""

import io
import sys

import nbformat


class MetadataError(RuntimeError):
    """Custom runtime error with informative error message."""

    def __init__(self, metadata: str, filename: str) -> None:
        super().__init__(
            metadata + " found in notebook " + filename + ".\nPlease\n"
            + "\t(1) install the jupyter_notebook_config.py hook available at "
            + "https://gist.github.com/francesco-ballarin/379ba630499559fa1072b2c526e57706\n"
            + "\t(2) open again each ipynb file that you changed, and save them again from "
            + "the jupyter web interface (in order for the newly installed hook to act), and\n"
            + "\t(3) rebase any commit that had changed ipynb files in order to remove unnecessary "
            + "metadata from git history."
        )


def check_recursive(d: dict, key: str) -> bool:
    """
    Check if undesired metadata is stored in a dictionary of metadata.

    Parameters
    ----------
    d : dict
        A dictionary representing the metadata of the notebook. The dictionary may
        possibly contain other dictionaries.
    key : str
        Name of a undesired metadata, possibly containing a dot to represent nested metadata.

    Returns
    -------
    bool
        Presence of the metadata in the dictionary.
    """
    nested = key.split(".")
    current = d
    for k in nested[:-1]:
        if hasattr(current, "get"):
            current = current.get(k, {})
        else:
            return False
    if not hasattr(current, "pop"):
        return False
    if nested[-1] in current:
        return True
    else:
        return False


def check_metadata(filename: str) -> None:
    """Check a jupyter notebook for undesired metadata."""
    # Unnecessary keys
    keys = {
        "metadata": [
            "collapsed",
            "celltoolbar",
            "kernel_spec.display_name",
            "kernel_spec.name",
            "language_info.codemirror_mode.version",
            "language_info.pygments_lexer",
            "language_info.version",
            "notify_time",
            "scrolled",
            "toc",
            "varInspector"
        ],
        "cell": {
            "metadata": [
                "code_folding",
                "collapsed",
                "ExecuteTime",
                "execution",
                "heading_collapsed",
                "hidden",
                "init_cell",
                "scrolled",
                "tags"
            ]
        }
    }

    # Read in notebook content
    with io.open(filename, "r", encoding="utf8") as f:
        nb = nbformat.read(f, as_version=nbformat.NO_CONVERT)

    # Check metadata fields
    for field in keys["metadata"]:
        if check_recursive(nb.metadata, field):
            raise MetadataError("Metadata " + field, filename)

    for cell in nb.cells:

        # Check for cell outputs
        if "outputs" in cell and len(cell["outputs"]) > 0:
            raise MetadataError("Cell outputs", filename)

        # Check for cell execution counts
        if "execution_count" in cell and cell["execution_count"] is not None:
            raise MetadataError("Cell execution counts", filename)

        # Check cell metadata fields
        if "metadata" in cell:
            for field in keys["cell"]["metadata"]:
                if check_recursive(cell.metadata, field):
                    raise MetadataError("Cell metadata " + field, filename)


if __name__ == "__main__":
    # Get notebook name
    assert len(sys.argv) == 2
    filename = sys.argv[1]
    print("Checking metadata in file", filename)

    # Check metadata
    check_metadata(filename)
