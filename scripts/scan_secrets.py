#!/usr/bin/env python3
"""
扫描仓库中可能泄露的密钥、Token 和敏感 URL。
返回 exit code 0 表示未发现，1 表示发现潜在泄露。
"""

import re
import subprocess
import sys
from pathlib import Path

# 允许扫描的文件（假阳性白名单）
ALLOWED_FILES = {
    ".env.example",
    ".env.beta.example",
    "scripts/scan_secrets.py",
}

# 扫描模式：(名称, 正则表达式)
PATTERNS = [
    ("OpenAI/Zep key", r"sk-[a-zA-Z0-9]{20,}"),
    ("Langfuse public key", r"pk-[a-zA-Z0-9]{20,}"),
    ("Langfuse public key (pk-lf)", r"pk-lf-[a-zA-Z0-9]{10,}"),
    ("Langfuse secret key (sk-lf)", r"sk-lf-[a-zA-Z0-9]{10,}"),
    ("Generic API key", r"api_key\s*=\s*[\"\'][a-zA-Z0-9]{32,}[\"\']"),
    ("Convex URL", r"https://[a-z0-9-]+\.convex\.cloud"),
]

# 行级假阳性规则：匹配到这些正则时跳过该行
LINE_ALLOWLIST = [
    # .env.example 中的占位符
    re.compile(r"your.*key.*here", re.IGNORECASE),
    re.compile(r"your.*project", re.IGNORECASE),
    re.compile(r"your.*api.*key", re.IGNORECASE),
    re.compile(r"your.*base.*url", re.IGNORECASE),
    re.compile(r"your.*model.*name", re.IGNORECASE),
    re.compile(r"your.*public.*key", re.IGNORECASE),
    re.compile(r"your.*secret.*key", re.IGNORECASE),
    # 明确的占位符提示
    re.compile(r"\b(example|placeholder|dummy|fake|mock|test|xxx+|yyy+)\b", re.IGNORECASE),
    # 注释行（支持 # 和 //）
    re.compile(r"^\s*(#|//)"),
]


def get_tracked_files():
    """获取 git 跟踪的所有文件列表。"""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except subprocess.CalledProcessError as e:
        print(f"Error running git ls-files: {e}", file=sys.stderr)
        sys.exit(2)


def is_line_allowed(line: str) -> bool:
    """检查某行是否命中假阳性白名单。"""
    for pattern in LINE_ALLOWLIST:
        if pattern.search(line):
            return True
    return False


def scan_file(filepath: str) -> list:
    """扫描单个文件，返回匹配的 (行号, 行内容, 模式名称) 列表。"""
    findings = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for lineno, line in enumerate(f, start=1):
                if is_line_allowed(line):
                    continue
                for name, pattern in PATTERNS:
                    if re.search(pattern, line):
                        findings.append((lineno, line.rstrip("\n"), name))
                        # 一行只报一次，避免同一行多个模式重复
                        break
    except (OSError, UnicodeDecodeError):
        # 忽略无法读取的文件（如二进制文件）
        pass
    return findings


def main():
    tracked_files = get_tracked_files()
    all_findings = []

    for filepath in tracked_files:
        if filepath in ALLOWED_FILES:
            continue
        # 也检查路径部分匹配（应对子目录情况）
        if any(filepath.endswith(allowed) for allowed in ALLOWED_FILES):
            continue

        findings = scan_file(filepath)
        for lineno, line, name in findings:
            all_findings.append((filepath, lineno, line, name))

    if all_findings:
        print("Potential secrets found:")
        for filepath, lineno, line, name in all_findings:
            print(f"  {filepath}:{lineno}  [{name}]  {line.strip()}")
        sys.exit(1)
    else:
        print("No secrets found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
