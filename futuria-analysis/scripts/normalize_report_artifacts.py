#!/usr/bin/env python3
"""Remediation workflow for persisted report artifacts.

Scans persisted report artifacts for language contamination, provides dry-run reporting
of normalization/quarantine impact, and can safely remediate contaminated artifacts
or move them to quarantine.

Usage:
    # Dry-run scan of all reporting artifacts
    python3 scripts/normalize_report_artifacts.py --scope reporting --dry-run

    # Apply normalization (with backup)
    python3 scripts/normalize_report_artifacts.py --scope reporting --normalize

    # Quarantine contaminated artifacts
    python3 scripts/normalize_report_artifacts.py --scope reporting --quarantine

    # Apply both normalization and quarantine for remaining contamination
    python3 scripts/normalize_report_artifacts.py --scope reporting --normalize --quarantine
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

FORBIDDEN_PATTERNS: dict[str, re.Pattern[str]] = {
    "cjk": re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]"),
    "kana": re.compile(r"[\u3040-\u30ff]"),
    "hangul": re.compile(r"[\uac00-\ud7af]"),
    "cyrillic": re.compile(r"[\u0400-\u04ff\u0500-\u052f]"),
    "fullwidth": re.compile(r"[\u3000-\u303f\uff00-\uffef]"),
}

QUARANTINE_DIR = "backend/uploads/reports/.quarantine"
REPORTS_DIR = "backend/uploads/reports"
CONTAMINATED_SECTION_NAMES = [
    "预测场景与核心发现",
    "人群行为预测分析",
    "趋势展望与风险提示",
    "未来预测报告",
]


@dataclass
class ArtifactScanResult:
    path: str
    artifact_type: str
    contaminated: bool
    categories: list[str]
    line_count: int
    size_bytes: int
    needs_attention: bool
    recommended_action: str
    details: list[str] = field(default_factory=list)


@dataclass
class RemediationResult:
    artifact_path: str
    action: str
    success: bool
    backup_path: str | None = None
    error: str | None = None
    details: str | None = None


def detect_contamination(text: str) -> tuple[bool, list[str]]:
    """Detect forbidden script categories in text."""
    categories = [
        name for name, pattern in FORBIDDEN_PATTERNS.items()
        if pattern.search(text)
    ]
    return bool(categories), categories


def scan_artifact(path: Path) -> tuple[bool, list[str], list[str]]:
    """Scan a single artifact file for contamination."""
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="utf-8", errors="replace")
    
    contaminated, categories = detect_contamination(content)
    lines = content.split("\n")
    
    details = []
    for i, line in enumerate(lines, 1):
        line_contaminated, line_categories = detect_contamination(line)
        if line_contaminated:
            preview = line[:100].strip()
            details.append(f"  Line {i}: {[c for c in line_categories]} - {preview!r}")
    
    return contaminated, categories, details


def iter_report_artifacts(reports_dir: Path) -> Iterator[Path]:
    """Iterate over all report artifact files in the reports directory."""
    if not reports_dir.exists():
        return
    
    for report_dir in reports_dir.iterdir():
        if not report_dir.is_dir() or report_dir.name.startswith("."):
            continue
        
        for artifact_path in report_dir.iterdir():
            if artifact_path.is_file() and artifact_path.suffix in (
                ".md", ".txt", ".json", ".jsonl"
            ):
                yield artifact_path


def determine_action(
    artifact_path: Path,
    artifact_type: str,
    categories: list[str],
    dry_run: bool
) -> tuple[bool, str, list[str]]:
    """Determine if artifact needs attention and what action is recommended."""
    needs_attention = False
    recommended_action = "none"
    details = []
    
    if artifact_type == "console_log":
        if categories:
            recommended_action = "quarantine"
            needs_attention = True
            details.append("Console logs may contain tool output with contamination")
    elif artifact_type == "section":
        if categories:
            recommended_action = "normalize"
            needs_attention = True
            details.append("Section content should be normalized to English")
    elif artifact_type == "full_report":
        if categories:
            recommended_action = "quarantine"
            needs_attention = True
            details.append("Full reports with contamination should be quarantined for review")
    elif artifact_type == "progress":
        if categories:
            recommended_action = "normalize"
            needs_attention = True
            details.append("Progress metadata with section names should be normalized")
    elif artifact_type == "meta":
        if categories:
            recommended_action = "normalize"
            needs_attention = True
            details.append("Metadata with contaminated values should be normalized")
    elif artifact_type == "outline":
        if categories:
            recommended_action = "normalize"
            needs_attention = True
            details.append("Outline with contamination should be normalized")
    elif artifact_type == "agent_log":
        if categories:
            recommended_action = "quarantine"
            needs_attention = True
            details.append("Agent logs should be quarantined as evidence of contamination")
    
    return needs_attention, recommended_action, details


def get_artifact_type(path: Path) -> str:
    """Classify artifact by filename."""
    name = path.stem.lower()
    suffix = path.suffix.lower()
    
    if name == "console_log" or "log" in name:
        return "console_log"
    elif name.startswith("section_"):
        return "section"
    elif name == "full_report":
        return "full_report"
    elif name == "progress":
        return "progress"
    elif name == "meta":
        return "meta"
    elif name == "outline":
        return "outline"
    elif suffix == ".jsonl" or name == "agent_log":
        return "agent_log"
    else:
        return "unknown"


def scan_reports_scope(
    reports_dir: Path,
    dry_run: bool = True
) -> list[ArtifactScanResult]:
    """Scan all persisted report artifacts for contamination."""
    results: list[ArtifactScanResult] = []
    
    for artifact_path in iter_report_artifacts(reports_dir):
        try:
            stat = artifact_path.stat()
            content = artifact_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"  Warning: Could not read {artifact_path}: {e}", file=sys.stderr)
            continue
        
        contaminated, categories, scan_details = scan_artifact(artifact_path)
        artifact_type = get_artifact_type(artifact_path)
        needs_attention, recommended_action, action_details = determine_action(
            artifact_path, artifact_type, categories, dry_run
        )
        
        results.append(ArtifactScanResult(
            path=str(artifact_path),
            artifact_type=artifact_type,
            contaminated=contaminated,
            categories=categories,
            line_count=len(content.split("\n")),
            size_bytes=stat.st_size,
            needs_attention=needs_attention,
            recommended_action=recommended_action,
            details=scan_details + action_details
        ))
    
    return results


def create_backup(path: Path, backup_dir: Path) -> Path:
    """Create a timestamped backup of the file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{path.parent.name}_{path.name}.{timestamp}.bak"
    backup_path = backup_dir / backup_name
    backup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_path)
    return backup_path


def quarantine_artifact(path: Path, quarantine_dir: Path) -> RemediationResult:
    """Move an artifact to quarantine."""
    try:
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        
        rel_path = path.relative_to(path.parent.parent)
        dest_path = quarantine_dir / rel_path.name
        
        counter = 1
        while dest_path.exists():
            dest_path = quarantine_dir / f"{rel_path.stem}_{counter}{rel_path.suffix}"
            counter += 1
        
        shutil.copy2(path, dest_path)
        path.unlink()
        
        return RemediationResult(
            artifact_path=str(path),
            action="quarantine",
            success=True,
            backup_path=str(dest_path),
            details=f"Quarantined to {dest_path}"
        )
    except Exception as e:
        return RemediationResult(
            artifact_path=str(path),
            action="quarantine",
            success=False,
            error=str(e)
        )


def normalize_progress_json(path: Path) -> RemediationResult:
    """Normalize a progress.json file by removing non-ASCII section names."""
    try:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        
        original_completed = data.get("completed_sections", [])
        cleaned_completed = [
            s for s in original_completed
            if not detect_contamination(s)[0]
        ]
        
        if original_completed != cleaned_completed:
            data["completed_sections"] = cleaned_completed
            data["normalized_at"] = datetime.now().isoformat()
            data["original_sections"] = original_completed
            
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            
            return RemediationResult(
                artifact_path=str(path),
                action="normalize",
                success=True,
                details=f"Normalized {len(original_completed) - len(cleaned_completed)} contaminated section names"
            )
        else:
            return RemediationResult(
                artifact_path=str(path),
                action="normalize",
                success=True,
                details="No normalization needed"
            )
    except Exception as e:
        return RemediationResult(
            artifact_path=str(path),
            action="normalize",
            success=False,
            error=str(e)
        )


def normalize_outline_json(path: Path) -> RemediationResult:
    """Normalize an outline.json file by removing non-ASCII content."""
    try:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        
        normalized = False
        
        def clean_text(text: str) -> str:
            nonlocal normalized
            if detect_contamination(text)[0]:
                normalized = True
                return "[Normalized Section - English Translation Required]"
            return text
        
        def clean_sections(obj: Any) -> Any:
            nonlocal normalized
            if isinstance(obj, dict):
                return {k: clean_sections(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_sections(item) for item in obj]
            elif isinstance(obj, str):
                return clean_text(obj)
            return obj
        
        cleaned_data = clean_sections(data)
        
        if normalized:
            cleaned_data["normalized_at"] = datetime.now().isoformat()
            cleaned_data["needs_review"] = True
            
            path.write_text(
                json.dumps(cleaned_data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            
            return RemediationResult(
                artifact_path=str(path),
                action="normalize",
                success=True,
                details="Normalized non-ASCII content in outline"
            )
        else:
            return RemediationResult(
                artifact_path=str(path),
                action="normalize",
                success=True,
                details="No normalization needed"
            )
    except Exception as e:
        return RemediationResult(
            artifact_path=str(path),
            action="normalize",
            success=False,
            error=str(e)
        )


def normalize_meta_json(path: Path) -> RemediationResult:
    """Normalize a meta.json file by removing non-ASCII contamination."""
    try:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        
        normalized = False
        
        def clean_value(value: Any, key: str = "") -> Any:
            nonlocal normalized
            if isinstance(value, str):
                if detect_contamination(value)[0]:
                    normalized = True
                    return f"[Normalized: {key}]"
                return value
            elif isinstance(value, dict):
                return {k: clean_value(v, k) for k, v in value.items()}
            elif isinstance(value, list):
                return [clean_value(item, key) for item in value]
            return value
        
        cleaned_data = clean_value(data)
        
        if normalized:
            cleaned_data["normalized_at"] = datetime.now().isoformat()
            cleaned_data["contamination_remediated"] = True
            
            path.write_text(
                json.dumps(cleaned_data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            
            return RemediationResult(
                artifact_path=str(path),
                action="normalize",
                success=True,
                details="Normalized non-ASCII content in metadata"
            )
        else:
            return RemediationResult(
                artifact_path=str(path),
                action="normalize",
                success=True,
                details="No normalization needed"
            )
    except Exception as e:
        return RemediationResult(
            artifact_path=str(path),
            action="normalize",
            success=False,
            error=str(e)
        )


def normalize_section_md(path: Path) -> RemediationResult:
    """Normalize a section markdown file."""
    try:
        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")
        
        normalized_lines = []
        normalized_count = 0
        
        for line in lines:
            contaminated, categories = detect_contamination(line)
            if contaminated:
                normalized_lines.append(f"<!-- NORMALIZED: Contaminated content removed -->")
                normalized_count += 1
            else:
                normalized_lines.append(line)
        
        if normalized_count > 0:
            normalized_content = "\n".join(normalized_lines)
            path.write_text(normalized_content, encoding="utf-8")
            
            return RemediationResult(
                artifact_path=str(path),
                action="normalize",
                success=True,
                details=f"Normalized {normalized_count} contaminated lines"
            )
        else:
            return RemediationResult(
                artifact_path=str(path),
                action="normalize",
                success=True,
                details="No normalization needed"
            )
    except Exception as e:
        return RemediationResult(
            artifact_path=str(path),
            action="normalize",
            success=False,
            error=str(e)
        )


def normalize_artifact(path: Path) -> RemediationResult:
    """Normalize an artifact based on its type."""
    artifact_type = get_artifact_type(path)
    
    if artifact_type == "progress":
        return normalize_progress_json(path)
    elif artifact_type == "outline":
        return normalize_outline_json(path)
    elif artifact_type == "meta":
        return normalize_meta_json(path)
    elif artifact_type in ("section", "full_report"):
        return normalize_section_md(path)
    else:
        return RemediationResult(
            artifact_path=str(path),
            action="normalize",
            success=True,
            details=f"No normalization available for type: {artifact_type}"
        )


def apply_remediation(
    results: list[ArtifactScanResult],
    reports_dir: Path,
    quarantine_dir: Path,
    normalize: bool,
    quarantine: bool,
    dry_run: bool
) -> list[RemediationResult]:
    """Apply remediation actions to scanned artifacts."""
    remediation_results: list[RemediationResult] = []
    
    for result in results:
        if not result.needs_attention:
            continue
        
        path = Path(result.path)
        
        if dry_run:
            print(f"  [DRY-RUN] Would {result.recommended_action}: {result.path}")
            remediation_results.append(RemediationResult(
                artifact_path=result.path,
                action=result.recommended_action,
                success=True,
                details=f"[Dry-run] Would apply {result.recommended_action}"
            ))
            continue
        
        if result.recommended_action == "quarantine" and quarantine:
            res = quarantine_artifact(path, quarantine_dir)
            remediation_results.append(res)
            if res.success:
                print(f"  ✓ Quarantined: {result.path}")
            else:
                print(f"  ✗ Failed to quarantine: {result.path} - {res.error}")
        
        elif result.recommended_action == "normalize" and normalize:
            res = normalize_artifact(path)
            remediation_results.append(res)
            if res.success:
                print(f"  ✓ Normalized: {result.path} ({res.details})")
            else:
                print(f"  ✗ Failed to normalize: {result.path} - {res.error}")
    
    return remediation_results


def print_dry_run_report(
    scope: str,
    results: list[ArtifactScanResult],
    reports_dir: Path,
    quarantine_dir: Path
) -> None:
    """Print a dry-run report showing what would be remediated."""
    total = len(results)
    contaminated = sum(1 for r in results if r.contaminated)
    needs_attention = sum(1 for r in results if r.needs_attention)
    
    quarantine_count = sum(
        1 for r in results
        if r.needs_attention and r.recommended_action == "quarantine"
    )
    normalize_count = sum(
        1 for r in results
        if r.needs_attention and r.recommended_action == "normalize"
    )
    
    print(f"\n{'='*70}")
    print(f"REPORT ARTIFACT REMEDIATION DRY-RUN REPORT")
    print(f"{'='*70}")
    print(f"Scope: {scope}")
    print(f"Reports Directory: {reports_dir}")
    print(f"Quarantine Directory: {quarantine_dir}")
    print(f"\nSUMMARY:")
    print(f"  Total artifacts scanned: {total}")
    print(f"  Contaminated artifacts: {contaminated}")
    print(f"  Artifacts needing attention: {needs_attention}")
    print(f"    - Would quarantine: {quarantine_count}")
    print(f"    - Would normalize: {normalize_count}")
    print(f"\n{'='*70}")
    print(f"DETAILED FINDINGS:")
    print(f"{'='*70}\n")
    
    if not results:
        print("  No artifacts found in reports directory.")
        return
    
    for result in sorted(results, key=lambda r: (not r.needs_attention, r.path)):
        status = "⚠ NEEDS ATTENTION" if result.needs_attention else "✓ OK"
        print(f"  {status}")
        print(f"    Path: {result.path}")
        print(f"    Type: {result.artifact_type}")
        print(f"    Contaminated: {result.contaminated}")
        if result.categories:
            print(f"    Categories: {result.categories}")
        print(f"    Size: {result.size_bytes:,} bytes")
        print(f"    Lines: {result.line_count}")
        print(f"    Recommended action: {result.recommended_action}")
        
        if result.details:
            print(f"    Details:")
            for detail in result.details[:5]:
                print(f"      {detail}")
            if len(result.details) > 5:
                print(f"      ... and {len(result.details) - 5} more")
        
        print()
    
    print(f"\n{'='*70}")
    print(f"RECOMMENDED REMEDIATION STEPS:")
    print(f"{'='*70}")
    print(f"\n1. To quarantine contaminated artifacts:")
    print(f"   python3 scripts/normalize_report_artifacts.py --scope {scope} --quarantine")
    print(f"\n2. To normalize artifacts that can be cleaned:")
    print(f"   python3 scripts/normalize_report_artifacts.py --scope {scope} --normalize")
    print(f"\n3. To apply both normalization and quarantine:")
    print(f"   python3 scripts/normalize_report_artifacts.py --scope {scope} --normalize --quarantine")
    print(f"\n4. To just see this report again:")
    print(f"   python3 scripts/normalize_report_artifacts.py --scope {scope} --dry-run")
    print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Remediation workflow for persisted report artifacts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run scan (shows what needs remediation)
  python3 scripts/normalize_report_artifacts.py --scope reporting --dry-run

  # Apply normalization to cleanable artifacts
  python3 scripts/normalize_report_artifacts.py --scope reporting --normalize

  # Move contaminated artifacts to quarantine
  python3 scripts/normalize_report_artifacts.py --scope reporting --quarantine

  # Apply both with full remediation
  python3 scripts/normalize_report_artifacts.py --scope reporting --normalize --quarantine
        """
    )
    parser.add_argument(
        "--scope",
        default="reporting",
        help="Scope for remediation (default: reporting)"
    )
    parser.add_argument(
        "--reports-dir",
        default=REPORTS_DIR,
        help=f"Path to reports directory (default: {REPORTS_DIR})"
    )
    parser.add_argument(
        "--quarantine-dir",
        default=QUARANTINE_DIR,
        help=f"Path to quarantine directory (default: {QUARANTINE_DIR})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be remediated without making changes"
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Apply normalization to artifacts that can be cleaned"
    )
    parser.add_argument(
        "--quarantine",
        action="store_true",
        help="Move contaminated artifacts to quarantine"
    )
    parser.add_argument(
        "--fail-on-contamination",
        action="store_true",
        help="Return non-zero if any contamination is found (for CI)"
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir).resolve()
    quarantine_dir = Path(args.quarantine_dir).resolve()
    
    if not reports_dir.exists():
        print(f"Error: Reports directory not found: {reports_dir}", file=sys.stderr)
        return 1
    
    print(f"Scanning report artifacts in: {reports_dir}")
    results = scan_reports_scope(reports_dir, dry_run=args.dry_run)
    
    if args.dry_run:
        print_dry_run_report(args.scope, results, reports_dir, quarantine_dir)
        
        needs_attention = sum(1 for r in results if r.needs_attention)
        if args.fail_on_contamination and needs_attention > 0:
            print(f"\nContamination detected: {needs_attention} artifacts need remediation")
            return 1
        return 0
    
    if not args.normalize and not args.quarantine:
        print("Error: No action specified. Use --normalize, --quarantine, or --dry-run", file=sys.stderr)
        return 1
    
    remediation_results = apply_remediation(
        results,
        reports_dir,
        quarantine_dir,
        args.normalize,
        args.quarantine,
        dry_run=False
    )
    
    successful = sum(1 for r in remediation_results if r.success)
    failed = sum(1 for r in remediation_results if not r.success)
    
    print(f"\nRemediation complete:")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    
    if args.fail_on_contamination and failed > 0:
        return 1
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
