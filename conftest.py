"""Test-only: the repo root is itself a plugin package (its __init__.py uses relative imports).

Pytest collects the root as a Package and, in Package.setup, imports __init__.py as a top-level
module, which fails on the relative imports. A conftest hook can't intercept the root (it is
collected through its parent's hook proxy), so skip that import for the root package only.
tests/test_plugin.py loads the package itself with the right package context.
"""
from pathlib import Path

from _pytest.python import Package

ROOT = Path(__file__).resolve().parent
_orig_setup = Package.setup


def _setup(self):
    if Path(self.path).resolve() == ROOT:
        return None
    return _orig_setup(self)


Package.setup = _setup
