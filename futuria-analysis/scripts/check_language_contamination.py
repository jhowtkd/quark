#!/usr/bin/env python3
"""Reporting language contamination scanner.

Scans a configured scope and compares actual forbidden-script findings against the
expected contamination baseline captured in config/language_policy.json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FORBIDDEN_PATTERNS: dict[str, re.Pattern[str]] = {
    "cjk": re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]"),
    "kana": re.compile(r"[\u3040-\u30ff]"),
    "hangul": re.compile(r"[\uac00-\ud7af]"),
    "cyrillic": re.compile(r"[\u0400-\u04ff\u0500-\u052f]"),
    "fullwidth": re.compile(r"[\u3000-\u303f\uff00-\uffef]"),
}


@dataclass
class FileScanResult:
    path: str
    surface: str
    expected_contamination: bool
    contaminated: bool
    categories: list[str]
    exists: bool
    notes: str | None = None

    @property
    def policy_breach(self) -> bool:
        return (not self.exists) or (self.contaminated != self.expected_contamination)


def load_policy(policy_path: Path) -> dict[str, Any]:
    with policy_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def detect_categories(text: str) -> list[str]:
    return [name for name, pattern in FORBIDDEN_PATTERNS.items() if pattern.search(text)]


def scan_file(path: Path) -> tuple[bool, list[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    categories = detect_categories(text)
    return bool(categories), categories


def resolve_scope_entries(policy: dict[str, Any], scope: str) -> list[dict[str, Any]]:
    scopes = policy.get("scopes", {})
    if scope not in scopes:
        available = ", ".join(sorted(scopes)) or "<none>"
        raise SystemExit(f"Unknown scope '{scope}'. Available scopes: {available}")
    return scopes[scope].get("entries", [])


def evaluate_scope(policy: dict[str, Any], scope: str, repo_root: Path) -> list[FileScanResult]:
    results: list[FileScanResult] = []
    for entry in resolve_scope_entries(policy, scope):
        relative_path = entry["path"]
        target = repo_root / relative_path
        if target.exists():
            contaminated, categories = scan_file(target)
            exists = True
        else:
            contaminated, categories, exists = False, [], False
        results.append(
            FileScanResult(
                path=relative_path,
                surface=entry.get("surface", "unknown"),
                expected_contamination=bool(entry.get("expected_contamination", False)),
                contaminated=contaminated,
                categories=categories,
                exists=exists,
                notes=entry.get("notes"),
            )
        )
    return results


def print_report(scope: str, results: list[FileScanResult]) -> None:
    contaminated_count = sum(1 for result in results if result.contaminated)
    breach_count = sum(1 for result in results if result.policy_breach)
    print(
        f"scope={scope} entries={len(results)} contaminated={contaminated_count} "
        f"policy_breaches={breach_count}"
    )
    for result in results:
        categories = ",".join(result.categories) if result.categories else "none"
        status = "BREACH" if result.policy_breach else "OK"
        existence = "missing" if not result.exists else "present"
        print(
            f"[{status}] {result.path} | surface={result.surface} | expected={result.expected_contamination} "
            f"actual={result.contaminated} | categories={categories} | {existence}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scan files for forbidden-script contamination.")
    parser.add_argument("--scope", required=True, help="Policy scope to scan, e.g. reporting")
    parser.add_argument(
        "--policy",
        default="config/language_policy.json",
        help="Path to policy JSON file (default: config/language_policy.json)",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root used to resolve relative paths (default: current directory)",
    )
    parser.add_argument(
        "--fail-on-policy-breach",
        action="store_true",
        help="Return non-zero when actual findings diverge from policy baseline.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    policy_path = Path(args.policy)
    if not policy_path.is_absolute():
        policy_path = (repo_root / policy_path).resolve()

    policy = load_policy(policy_path)
    results = evaluate_scope(policy, args.scope, repo_root)
    print_report(args.scope, results)

    breach_count = sum(1 for result in results if result.policy_breach)
    if args.fail_on_policy_breach and breach_count:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
