# SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Basic tests for the pn5180_tagomatic package."""

import pn5180_tagomatic


def test_version() -> None:
    """Test that version is defined."""
    assert hasattr(pn5180_tagomatic, "__version__")
    assert isinstance(pn5180_tagomatic.__version__, str)


def test_package_import() -> None:
    """Test that the package can be imported."""
    assert pn5180_tagomatic is not None
