import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_language_contamination.py"


def run_scanner(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
    )


def test_reporting_scope_passes_when_findings_match_policy(tmp_path: Path) -> None:
    clean_file = tmp_path / "clean.txt"
    contaminated_file = tmp_path / "contaminated.txt"
    clean_file.write_text("Prediction Report\nAll output is English only.\n", encoding="utf-8")
    contaminated_file.write_text("Prediction Report\n未来预测报告\n", encoding="utf-8")

    policy = {
        "scopes": {
            "reporting": {
                "entries": [
                    {
                        "path": str(clean_file.relative_to(tmp_path)),
                        "surface": "clean-source",
                        "expected_contamination": False,
                    },
                    {
                        "path": str(contaminated_file.relative_to(tmp_path)),
                        "surface": "known-dirty-artifact",
                        "expected_contamination": True,
                    },
                ]
            }
        }
    }
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(policy), encoding="utf-8")

    result = run_scanner(
        "--policy",
        str(policy_path),
        "--scope",
        "reporting",
        "--repo-root",
        str(tmp_path),
        "--fail-on-policy-breach",
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "policy_breaches=0" in result.stdout
    assert "entries=2" in result.stdout


def test_reporting_scope_fails_when_unexpected_contamination_is_found(tmp_path: Path) -> None:
    unexpected_file = tmp_path / "unexpected.txt"
    unexpected_file.write_text("Crowd Behavior\n趋势展望与风险提示\n", encoding="utf-8")

    policy = {
        "scopes": {
            "reporting": {
                "entries": [
                    {
                        "path": str(unexpected_file.relative_to(tmp_path)),
                        "surface": "clean-source",
                        "expected_contamination": False,
                    }
                ]
            }
        }
    }
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(policy), encoding="utf-8")

    result = run_scanner(
        "--policy",
        str(policy_path),
        "--scope",
        "reporting",
        "--repo-root",
        str(tmp_path),
        "--fail-on-policy-breach",
        cwd=REPO_ROOT,
    )

    assert result.returncode != 0
    assert "policy_breaches=1" in result.stdout
    assert "unexpected.txt" in result.stdout
