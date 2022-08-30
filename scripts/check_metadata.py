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

import glob
import io
import sys
import typing

import nbformat


class MetadataError(RuntimeError):
    """Custom runtime error with informative error message."""

    def __init__(self, metadata: str, filename: str) -> None:
        super().__init__(metadata + " found in notebook " + filename)


def check_recursive(d: typing.Dict[str, typing.Any], key: str) -> bool:
    """
    Check if undesired metadata is stored in a dictionary of metadata.

    Parameters
    ----------
    d
        A dictionary representing the metadata of the notebook. The dictionary may
        possibly contain other dictionaries.
    key
        Name of a undesired metadata, possibly containing a dot to represent nested metadata.

    Returns
    -------
    :
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
    keys: typing.Dict[str, typing.Any] = {
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
        nb = nbformat.read(f, as_version=nbformat.NO_CONVERT)  # type: ignore[no-untyped-call]

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


def check_files(pattern: str, expect_failure: bool) -> None:
    """Check all files matching a pattern for undesired metadata."""
    metadata_errors = list()
    for f in glob.glob(pattern, recursive=True):
        print("Checking file", f, "for metadata")
        try:
            check_metadata(f)
        except MetadataError as e:
            metadata_errors.append(str(e))

    if not expect_failure:
        if len(metadata_errors) > 0:
            raise RuntimeError(
                "The following metadata errors have been found in " + str(len(metadata_errors)) + " notebooks:"
                + "\n\t* " + "\n\t* ".join(metadata_errors)
                + "\nPlease do the following:\n"
                + "\t(1) install nbstripout and nbdime on your machine.\n"
                + "\t(2) download the jupyter_notebook_config.py available at\n"
                + "https://github.com/RBniCS/check-jupyter-metadata-action/blob/main/"
                + ".jupyter/jupyter_notebook_config.py\n"
                + "\t(3) replace the REPOSITORY_NAME_PLACEHOLDER with the name of your repository, "
                + "and save the file in a jupyter config path (for instance $HOME/.jupyter; "
                + "further available config paths can be obtained from jupyter --paths). "
                + "Such file provides a custom hook to strip output from jupyter notebooks to be stored in git.\n"
                + "\t(4) in the same folder, create the file jupyter_server_config.py as a symbolic link "
                + "to jupyter_notebook_config.py. The former is required by jupyter lab, while "
                + "jupyter notebook uses the latter.\n"
                + "\t(5) go to your repository clone and run\n"
                + "nbdime config-git --enable\n"
                + "This allows to configure custom diff and merge commands for *.ipynb files.\n"
                + "\t(6) open again each ipynb file that you changed, and save them again from "
                + "the jupyter web interface (in order for the newly installed hook to act), and\n"
                + "\t(7) rebase any commit that had changed ipynb files in order to remove unnecessary "
                + "metadata from git history."
            )
    else:
        if len(metadata_errors) == 0:
            raise RuntimeError("Failure was expected, but not metadata error occurred.")


if __name__ == "__main__":
    assert len(sys.argv) == 3
    check_files(sys.argv[1], True if sys.argv[2] == "true" else False)
