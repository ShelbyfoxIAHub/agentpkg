"""Plugin registries backed by Python entry points.

Each registry has built-in entries plus entry points discovered lazily from an
``agentpkg.*`` group. Built-ins always win over entry points with the same name.
Setting ``AGENTPKG_DISABLE_PLUGINS=1`` disables entry-point discovery. Plugin
code is only ever loaded from installed distributions, never from package
contents.
"""

import os
import sys
from typing import Any, Dict, List

from agentpkg.errors import MissingDependencyError, PluginError

GROUPS = {
    "parsers": "agentpkg.parsers",
    "indexers": "agentpkg.indexers",
    "connectors": "agentpkg.connectors",
    "skills": "agentpkg.skills",
    "backends": "agentpkg.backends",
}


def _entry_points(group: str) -> list:
    if os.environ.get("AGENTPKG_DISABLE_PLUGINS") == "1":
        return []
    from importlib import metadata

    found = metadata.entry_points()
    if hasattr(found, "select"):
        return list(found.select(group=group))
    return list(found.get(group, []))  # Python 3.9


class Registry:
    def __init__(self, kind: str, group: str):
        self.kind = kind
        self.group = group
        self._builtin: Dict[str, Any] = {}
        self._loaded: Dict[str, Any] = {}
        self.errors: Dict[str, str] = {}

    def register(self, name: str, obj: Any) -> None:
        """Register a built-in or programmatic plugin (factory or instance)."""
        self._builtin[name] = obj

    def _entry_point_map(self) -> Dict[str, Any]:
        return {ep.name: ep for ep in _entry_points(self.group)}

    def names(self) -> List[str]:
        return sorted(set(self._builtin).union(self._entry_point_map()))

    def get(self, name: str) -> Any:
        if name in self._builtin:
            return self._builtin[name]
        if name in self._loaded:
            return self._loaded[name]
        entry = self._entry_point_map().get(name)
        if entry is None:
            available = ", ".join(self.names()) or "(none)"
            raise PluginError(
                "Unknown {} plugin {!r}. Available: {}".format(self.kind, name, available)
            )
        try:
            obj = entry.load()
        except ImportError as error:
            missing = getattr(error, "name", None) or str(error)
            raise MissingDependencyError(
                "{} plugin {!r} needs an optional dependency that is not installed "
                "({}). Install the extra or package that provides it.".format(
                    self.kind.capitalize(), name, missing
                )
            ) from error
        except Exception as error:
            raise PluginError(
                "Could not load {} plugin {!r}: {}".format(self.kind, name, error)
            ) from error
        self._loaded[name] = obj
        return obj

    def create(self, name: str, *args, **kwargs) -> Any:
        """Instantiate a plugin: call it if callable, else return it as-is."""
        obj = self.get(name)
        return obj(*args, **kwargs) if callable(obj) else obj

    def create_all(self) -> List[Any]:
        """Instantiate every loadable plugin (broken ones are recorded in ``errors``)."""
        instances = []
        for name in self.names():
            try:
                instances.append(self.create(name))
            except (PluginError, TypeError) as error:
                self.errors[name] = str(error)
        return instances


parsers = Registry("parser", GROUPS["parsers"])
indexers = Registry("indexer", GROUPS["indexers"])
connectors = Registry("connector", GROUPS["connectors"])
skill_providers = Registry("skills provider", GROUPS["skills"])
backends = Registry("backend", GROUPS["backends"])

REGISTRIES = {
    "parsers": parsers,
    "indexers": indexers,
    "connectors": connectors,
    "skills": skill_providers,
    "backends": backends,
}


def load_builtin_plugins() -> None:
    """Import modules that register built-in plugins (idempotent)."""
    import agentpkg.connectors  # noqa: F401
    import agentpkg.indexing  # noqa: F401
    import agentpkg.skills  # noqa: F401


def describe_plugins() -> Dict[str, Dict[str, str]]:
    load_builtin_plugins()
    result = {}
    for key, registry in REGISTRIES.items():
        builtin = set(registry._builtin)
        result[key] = {
            name: "builtin" if name in builtin else "entry-point"
            for name in registry.names()
        }
    return result
