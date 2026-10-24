"""Skill model and discovery for package-declared skills.

Discovery only reads metadata. Executing a skill is a separate, consent-gated
step (see ``agentpkg.consent`` and ``run_skill``).
"""

import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import List, Optional

from agentpkg.consent import require_consent
from agentpkg.plugins import skill_providers

_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    path: str
    command: tuple = field(default_factory=tuple)
    source: str = "manifest"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "path": self.path,
            "command": list(self.command),
            "source": self.source,
        }


def parse_skill_markdown(text: str, path: str) -> Optional[Skill]:
    """Parse ``SKILL.md`` front matter (``key: value`` lines between ``---``)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    meta = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, separator, value = line.partition(":")
        if separator:
            meta[key.strip().lower()] = value.strip()
    else:
        return None
    name = meta.get("name", "")
    if not _NAME.match(name):
        return None
    command = ()
    raw = meta.get("command")
    if raw:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None
        if (
            isinstance(parsed, list)
            and len(parsed) <= 64
            and all(isinstance(part, str) and part and "\0" not in part for part in parsed)
        ):
            command = tuple(parsed)
    return Skill(name, meta.get("description", "")[:1000], path, command, "skill-md")


class ManifestSkillsProvider:
    """Skills declared in the manifest ``skills`` section."""

    name = "manifest"

    def discover(self, package) -> List[Skill]:
        return [
            Skill(
                item["name"],
                item.get("description", ""),
                item["path"],
                tuple(item.get("command", ())),
                "manifest",
            )
            for item in package.manifest.get("skills", [])
        ]


class SkillMdProvider:
    """``SKILL.md`` files anywhere under ``data/``."""

    name = "skill-md"

    def discover(self, package) -> List[Skill]:
        skills = []
        for name in package.names:
            if PurePosixPath(name).name.lower() == "skill.md" and name.startswith("data/"):
                try:
                    text = package.read(name).decode("utf-8")
                except (UnicodeDecodeError, ValueError):
                    continue
                skill = parse_skill_markdown(text, name)
                if skill is not None:
                    skills.append(skill)
        return skills


skill_providers.register("manifest", ManifestSkillsProvider)
skill_providers.register("skill-md", SkillMdProvider)


def discover_skills(package) -> List[Skill]:
    """Return skills from every provider; the first definition of a name wins."""
    found = {}
    for provider in skill_providers.create_all():
        for skill in provider.discover(package):
            found.setdefault(skill.name, skill)
    return sorted(found.values(), key=lambda skill: skill.name)


def run_skill(
    package,
    skill: Skill,
    allow: List[str],
    assume_yes: bool = False,
    timeout: int = 60,
    confirm=None,
) -> subprocess.CompletedProcess:
    """Run a skill's declared command after explicit allowlist and confirmation.

    The command runs without a shell, inside a temporary copy of ``data/`` and
    with a minimal environment (no inherited credentials).
    """
    from agentpkg.loader import unpack_package

    if not skill.command:
        raise ValueError("Skill {!r} declares no command".format(skill.name))
    first = PurePosixPath(skill.command[0])
    if first.is_absolute() or ".." in first.parts or "\\" in skill.command[0]:
        raise ValueError("Skill command must not point outside the package")
    require_consent(
        "skill",
        skill.name,
        "Command: {}".format(" ".join(skill.command)),
        allow,
        assume_yes=assume_yes,
        confirm=confirm,
    )
    with tempfile.TemporaryDirectory() as temporary:
        unpack_package(package.path, Path(temporary) / "pkg")
        workdir = Path(temporary) / "pkg" / "data"
        environment = {
            "PATH": os.environ.get("PATH", os.defpath),
            "HOME": temporary,
        }
        if os.name == "nt" and os.environ.get("SYSTEMROOT"):
            environment["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
        try:
            return subprocess.run(
                list(skill.command),
                cwd=str(workdir),
                env=environment,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError as error:
            raise ValueError("Skill command not found: {}".format(skill.command[0])) from error
        except subprocess.TimeoutExpired as error:
            raise RuntimeError("Skill timed out after {}s".format(timeout)) from error
