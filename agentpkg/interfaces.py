"""Stable, typing-friendly plugin interfaces (structural ``Protocol`` types).

Plugins do not need to import agentpkg to satisfy them.
"""

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

try:
    from typing import Protocol, runtime_checkable
except ImportError:  # pragma: no cover - Python < 3.8
    from typing_extensions import Protocol, runtime_checkable  # type: ignore

Message = Mapping[str, str]


@runtime_checkable
class Parser(Protocol):
    """Extracts text from file bytes. Entry-point group: ``agentpkg.parsers``."""

    suffixes: Sequence[str]  # lowercase, with dot, e.g. (".rst",)

    def parse(self, data: bytes, filename: str) -> str: ...


@runtime_checkable
class ModelConnector(Protocol):
    """Talks to a model. Entry-point group: ``agentpkg.connectors``.

    The registered object is a factory called as
    ``factory(model, *, base_url, api_key_env, allow_network, timeout)``.
    """

    def chat(
        self,
        messages: Sequence[Message],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str: ...

    def embed(self, texts: Sequence[str]) -> List[List[float]]: ...


@runtime_checkable
class Indexer(Protocol):
    """Builds ``index/`` artifacts. Entry-point group: ``agentpkg.indexers``.

    ``documents`` are dicts with ``path``, ``sha256`` and ``text``. Returns a
    mapping of archive path (``index/...``) to file bytes.
    """

    def build(
        self,
        documents: Sequence[Dict[str, Any]],
        connector: Optional[ModelConnector],
        options: Mapping[str, Any],
    ) -> Dict[str, bytes]: ...


@runtime_checkable
class SkillsProvider(Protocol):
    """Discovers skills. Entry-point group: ``agentpkg.skills``.

    ``package`` exposes ``manifest``, ``names`` and ``read(name) -> bytes``.
    Providers return objects with ``name``, ``description``, ``path``,
    ``command`` and ``to_dict()`` (``agentpkg.skills.Skill``).
    """

    def discover(self, package: Any) -> List[Any]: ...


@runtime_checkable
class VectorBackend(Protocol):
    """Ranks vectors. Entry-point group: ``agentpkg.backends`` (``kind = "vector"``)."""

    kind: str

    def search(
        self,
        vectors: Sequence[Sequence[float]],
        query: Sequence[float],
        top_k: int,
    ) -> List[Tuple[int, float]]: ...


@runtime_checkable
class GraphBackend(Protocol):
    """Reserved for graph stores. Group ``agentpkg.backends`` with ``kind = "graph"``."""

    kind: str

    def neighbors(self, node: str, limit: int) -> List[str]: ...
