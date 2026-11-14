#!/usr/bin/env python3
"""Repo check: python3 check_package.py. The four plugin manifests must carry one version."""
import json

FILES = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".cursor-plugin/plugin.json", "gemini-extension.json")
versions = {f: json.load(open(f))["version"] for f in FILES}
assert len(set(versions.values())) == 1, f"versions differ: {versions}"
print("manifests agree on version", versions[FILES[0]])
