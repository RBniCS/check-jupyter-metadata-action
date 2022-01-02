# Copyright (C) 2015-2022 by the RBniCS authors
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
    """Test the check_metadata script for a correctly formatted notebook."""
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
    """Test the check_metadata script for various incorrectly formatted notebooks."""
    with pytest.raises(check_metadata.MetadataError) as excinfo:
        check_metadata.check_metadata(
            os.path.join(root_directory, "tests", "data", "fail", notebook_file))
    assert expected_error in str(excinfo.value)
