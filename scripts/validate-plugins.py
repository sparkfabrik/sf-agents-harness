#!/usr/bin/env python3
"""Validate the plugin marketplace manifest and every plugin it lists.

Checks, in order:

1. `.claude-plugin/marketplace.json` parses and names at least one plugin.
2. Each listed plugin has a `name`, a `source` directory that exists, and a
   `version`; the plugin's own `.claude-plugin/plugin.json` parses and agrees on
   name and version; the plugin has a `README.md`.
3. Every `skills/*/SKILL.md` in a plugin has frontmatter with a `name` equal to
   its folder and a non-empty `description`.
4. Every `agents/*.agent.md` in a plugin has frontmatter with a non-empty `name`
   and `description`.

Exit status is 1 when any check fails; every failure is printed.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"

errors = []


def fail(message):
    errors.append(message)


def frontmatter(path):
    """Return the frontmatter fields of a Markdown file as a dict, or None."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    fields = {}
    for line in text[4:end].splitlines():
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if match:
            value = match.group(2).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                value = value[1:-1]
            fields[match.group(1)] = value
    return fields


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"{path.relative_to(ROOT)}: file missing")
    except json.JSONDecodeError as exc:
        fail(f"{path.relative_to(ROOT)}: invalid JSON ({exc})")
    return None


def check_skill(skill_dir):
    skill_md = skill_dir / "SKILL.md"
    rel = skill_md.relative_to(ROOT)
    if not skill_md.is_file():
        fail(f"{rel}: missing")
        return
    fields = frontmatter(skill_md)
    if fields is None:
        fail(f"{rel}: no frontmatter block")
        return
    if fields.get("name") != skill_dir.name:
        fail(f"{rel}: frontmatter name {fields.get('name')!r} does not match folder {skill_dir.name!r}")
    if not fields.get("description"):
        fail(f"{rel}: frontmatter description is missing or empty")


def check_agent(agent_md):
    rel = agent_md.relative_to(ROOT)
    fields = frontmatter(agent_md)
    if fields is None:
        fail(f"{rel}: no frontmatter block")
        return
    if not fields.get("name"):
        fail(f"{rel}: frontmatter name is missing or empty")
    if not fields.get("description"):
        fail(f"{rel}: frontmatter description is missing or empty")


def check_plugin(entry):
    name = entry.get("name")
    source = entry.get("source")
    version = entry.get("version")
    label = name or source or "<unnamed>"
    if not name:
        fail(f"marketplace plugin {label}: missing name")
    if not source:
        fail(f"marketplace plugin {label}: missing source")
        return
    if not version:
        fail(f"marketplace plugin {label}: missing version")
    plugin_dir = (ROOT / source).resolve()
    if not plugin_dir.is_dir():
        fail(f"marketplace plugin {label}: source {source} is not a directory")
        return
    manifest = load_json(plugin_dir / ".claude-plugin" / "plugin.json")
    if manifest is not None:
        if manifest.get("name") != name:
            fail(f"{label}: plugin.json name {manifest.get('name')!r} differs from marketplace name {name!r}")
        if manifest.get("version") != version:
            fail(f"{label}: plugin.json version {manifest.get('version')!r} differs from marketplace version {version!r}")
        if not manifest.get("description"):
            fail(f"{label}: plugin.json description is missing or empty")
    if not (plugin_dir / "README.md").is_file():
        fail(f"{label}: README.md missing")
    skills_dir = plugin_dir / "skills"
    if skills_dir.is_dir():
        for skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
            check_skill(skill_dir)
    agents_dir = plugin_dir / "agents"
    if agents_dir.is_dir():
        for agent_md in sorted(agents_dir.glob("*.agent.md")):
            check_agent(agent_md)


def main():
    marketplace = load_json(MARKETPLACE)
    if marketplace is None:
        return finish()
    if not marketplace.get("name"):
        fail("marketplace.json: missing name")
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        fail("marketplace.json: plugins must be a non-empty list")
        return finish()
    seen = set()
    for entry in plugins:
        if not isinstance(entry, dict):
            fail("marketplace.json: plugin entry is not an object")
            continue
        if entry.get("name") in seen:
            fail(f"marketplace.json: duplicate plugin name {entry.get('name')!r}")
        seen.add(entry.get("name"))
        check_plugin(entry)
    return finish()


def finish():
    if errors:
        for message in errors:
            print(f"::error::{message}")
        print(f"{len(errors)} plugin validation error(s)")
        return 1
    print("Plugin marketplace and manifests are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
