"""Explicit consent gates for anything that could execute package-provided tooling."""

import sys
from typing import Callable, Optional, Sequence

from agentpkg.errors import ConsentError


def require_consent(
    kind: str,
    name: str,
    details: str,
    allow: Sequence[str],
    assume_yes: bool = False,
    confirm: Optional[Callable[[str], bool]] = None,
) -> None:
    """Raise ConsentError unless ``name`` is allowlisted and confirmed.

    Two independent steps are required: the name must appear in ``allow`` (the
    ``--allow`` flag) and the user must confirm interactively, or pass
    ``--yes`` explicitly. Nothing is ever approved implicitly.
    """
    if name not in allow:
        raise ConsentError(
            "Package-provided {kind} {name!r} was not approved. Review it, then "
            "re-run with --allow {name}.".format(kind=kind, name=name)
        )
    if assume_yes:
        return
    if confirm is None:
        if not sys.stdin.isatty():
            raise ConsentError(
                "Confirmation required for {} {!r} but input is not interactive; "
                "pass --yes to confirm.".format(kind, name)
            )
        confirm = _ask
    if not confirm("{}\n{}\nRun this {}?".format(name, details, kind)):
        raise ConsentError("Declined: {} {!r} was not run.".format(kind, name))


def _ask(message: str) -> bool:
    print(message + " [y/N] ", end="", file=sys.stderr, flush=True)
    return sys.stdin.readline().strip().lower() in ("y", "yes")
