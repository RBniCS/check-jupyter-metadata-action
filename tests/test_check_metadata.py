# Copyright (C) 2015-2024 by the RBniCS authors
#
# This file is part of RBniCS-related actions.
#
# SPDX-License-Identifier: MIT
"""Tests for the check_metadata script."""

import importlib
import os
import sys
import types

import pytest


@pytest.fixture
def root_directory() -> str:
    """Return the root directory of the repository."""
    return os.path.dirname(os.path.dirname(__file__))


@pytest.fixture
def check_metadata(root_directory: str) -> types.ModuleType:
    """Load the check_metadata module."""
    sys.path.insert(0, os.path.join(root_directory, "scripts"))
    check_metadata = importlib.import_module("check_metadata")
    sys.path.pop(0)
    return check_metadata


def test_check_metadata_success(check_metadata: types.ModuleType, root_directory: str) -> None:
    """Test the check_metadata function for a correctly formatted notebook."""
    check_metadata.check_metadata(
        os.path.join(root_directory, "tests", "data", "success", "success.ipynb"))


@pytest.mark.parametrize(
    "notebook_file,expected_error",
    [
        ("fail_cell_execution_count.ipynb", "Cell execution counts found"),
        ("fail_cell_metadata.ipynb", "Cell metadata collapsed found"),
        ("fail_cell_outputs.ipynb", "Cell outputs found"),
        ("fail_metadata.ipynb", "Metadata language_info.codemirror_mode.version found")
    ]
)
def test_check_metadata_fail(
    check_metadata: types.ModuleType, root_directory: str, notebook_file: str, expected_error: str
) -> None:
    """Test the check_metadata function for various incorrectly formatted notebooks."""
    with pytest.raises(check_metadata.MetadataError) as excinfo:
        check_metadata.check_metadata(
            os.path.join(root_directory, "tests", "data", "fail", notebook_file))
    assert expected_error in str(excinfo.value)


def test_check_files_success(check_metadata: types.ModuleType, root_directory: str) -> None:
    """Test the check_files for correctly formatted notebooks."""
    pattern = os.path.join(root_directory, "tests", "data", "success", "*.ipynb")
    check_metadata.check_files(pattern, False)
    with pytest.raises(RuntimeError) as excinfo:
        check_metadata.check_files(pattern, True)
    assert str(excinfo.value) == "Failure was expected, but not metadata error occurred."


def test_check_files_fail(check_metadata: types.ModuleType, root_directory: str) -> None:
    """Test the check_files for incorrectly formatted notebooks."""
    pattern = os.path.join(root_directory, "tests", "data", "fail", "*.ipynb")
    check_metadata.check_files(pattern, True)
    with pytest.raises(RuntimeError) as excinfo:
        check_metadata.check_files(pattern, False)
    assert "The following metadata errors have been found in 4 notebooks" in str(excinfo.value)
    print(str(excinfo.value))
