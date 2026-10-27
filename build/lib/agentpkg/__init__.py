"""Portable semantic packages for AI agents."""

__version__ = "0.1.0"
SPEC_VERSION = "1.0"

from agentpkg.builder import create_package
from agentpkg.loader import inspect_package, unpack_package
from agentpkg.parsers import parse_file
from agentpkg.reader import read_package

__all__ = [
    "SPEC_VERSION",
    "__version__",
    "create_package",
    "inspect_package",
    "parse_file",
    "read_package",
    "unpack_package",
]
