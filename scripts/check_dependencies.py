#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


REQUIRED_CODEX_SKILLS = {
    "doubao-seedream-image": "character/reference images for multi-role story videos",
    "doubao-seed-audio": "coherent long-video ambience, Foley, narration, dialogue, and subtitles",
    "volcengine-resource-query": "final Seedance Fast resource-package balance preflight",
}

REQUIRED_TOOLS = {
    "ffmpeg": "final trim, concat, mux, compression, and export",
    "ffprobe": "media inspection for review and edit tooling",
}

RECOMMENDED_ENV_FILES = {
    "seedance.env": "Ark key for Seedance and Seedream",
    "speech.env": "Speech key for Seed Audio",
    "volcengine-billing.env": "IAM AK/SK for resource-package balance checks",
}


def unique_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    out: list[Path] = []
    for path in paths:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            out.append(path)
    return out


def candidate_skill_roots() -> list[Path]:
    home = Path.home()
    roots = [
        Path(os.environ["CODEX_HOME"]) / "skills"
        if os.environ.get("CODEX_HOME")
        else home / ".codex" / "skills",
        home / ".codex" / "skills",
    ]
    return unique_paths(roots)


def candidate_ffmpeg_skill_paths() -> list[Path]:
    home = Path.home()
    paths = [home / ".agents" / "skills" / "ffmpeg"]
    paths.extend(root / "ffmpeg" for root in candidate_skill_roots())
    return unique_paths(paths)


def check_skill(name: str) -> dict[str, object]:
    roots = candidate_skill_roots()
    paths = [root / name for root in roots]
    installed = [path for path in paths if (path / "SKILL.md").exists()]
    return {
        "name": name,
        "ok": bool(installed),
        "found": [str(path) for path in installed],
        "checked": [str(path) for path in paths],
        "purpose": REQUIRED_CODEX_SKILLS[name],
    }


def check_ffmpeg_skill() -> dict[str, object]:
    paths = candidate_ffmpeg_skill_paths()
    installed = [path for path in paths if (path / "SKILL.md").exists()]
    return {
        "name": "ffmpeg skill",
        "ok": bool(installed),
        "found": [str(path) for path in installed],
        "checked": [str(path) for path in paths],
        "purpose": "advanced FFmpeg editing patterns",
    }


def check_tool(name: str) -> dict[str, object]:
    found = shutil.which(name)
    return {
        "name": name,
        "ok": bool(found),
        "found": found,
        "purpose": REQUIRED_TOOLS[name],
    }


def check_env_file(name: str) -> dict[str, object]:
    path = Path.home() / ".codex" / name
    return {
        "name": name,
        "ok": path.exists(),
        "path": str(path),
        "purpose": RECOMMENDED_ENV_FILES[name],
    }


def build_report() -> dict[str, object]:
    skills = [check_skill(name) for name in REQUIRED_CODEX_SKILLS]
    skills.append(check_ffmpeg_skill())
    tools = [check_tool(name) for name in REQUIRED_TOOLS]
    env_files = [check_env_file(name) for name in RECOMMENDED_ENV_FILES]
    required_ok = all(item["ok"] for item in skills + tools)
    return {
        "ok": required_ok,
        "skills": skills,
        "tools": tools,
        "recommended_env_files": env_files,
    }


def print_text(report: dict[str, object]) -> None:
    print("Doubao Seedance full-production dependency check")
    for item in report["skills"]:
        status = "OK" if item["ok"] else "MISSING"
        print(f"{status:7} skill: {item['name']} - {item['purpose']}")
        if item["ok"]:
            print(f"        found: {item['found'][0]}")
    for item in report["tools"]:
        status = "OK" if item["ok"] else "MISSING"
        print(f"{status:7} tool:  {item['name']} - {item['purpose']}")
        if item["ok"]:
            print(f"        found: {item['found']}")
    for item in report["recommended_env_files"]:
        status = "OK" if item["ok"] else "WARN"
        print(f"{status:7} env:   {item['name']} - {item['purpose']}")
        print(f"        path: {item['path']}")
    if not report["ok"]:
        print()
        print("Install the missing skills/tools before using the full long-video workflow.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check full doubao-seedance-video workflow dependencies.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
