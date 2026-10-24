"""Exception types shared across agentpkg. All derive from built-ins the CLI reports."""


class PluginError(RuntimeError):
    """A plugin could not be found or loaded."""


class MissingDependencyError(PluginError):
    """A plugin needs an optional dependency that is not installed."""


class ConnectorError(RuntimeError):
    """A model connector failed or was configured unsafely."""


class ConsentError(RuntimeError):
    """The user has not explicitly approved a risky action."""
