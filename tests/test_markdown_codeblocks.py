from __future__ import annotations

import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Iterable, Tuple

import pytest


FENCE_RE = re.compile(r"```(python|bash)\s*\n(.*?)\n```", re.DOTALL)


def _iter_md_files(root: Path) -> Iterable[Path]:
    for p in root.glob("*.md"):
        yield p
    for p in (root / "docs").glob("**/*.md") if (root / "docs").exists() else []:
        yield p


def _extract_blocks(text: str) -> Iterable[Tuple[str, str]]:
    for m in FENCE_RE.finditer(text):
        lang = m.group(1).strip().lower()
        code = m.group(2).strip()
        if code:
            yield lang, code


def _should_run_bash(code: str) -> bool:
    # Allow only if explicitly using uv run, and deny dangerous commands
    deny_fragments = ("sudo", " rm ", "rm -", "rm -rf", "install", "pytest")
    if "uv run" not in code:
        return False
    if any(frag in code for frag in deny_fragments):
        return False
    return True


@pytest.mark.unit
def test_markdown_codeblocks_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = Path.cwd()
    md_files = list(_iter_md_files(root))
    assert md_files, "No markdown files found to validate code blocks."

    # Run from an isolated temp dir
    monkeypatch.chdir(tmp_path)
    env = os.environ.copy()
    env.setdefault("RUN_LIVE_TESTS", "0")
    # Ensure the project src/ is importable in subprocesses
    src_path = str((root / "src").resolve())
    env["PYTHONPATH"] = f"{src_path}:{env.get('PYTHONPATH','')}"

    ran_any = False

    for md in md_files:
        text = md.read_text(encoding="utf-8", errors="ignore")
        for lang, code in _extract_blocks(text):
            if lang == "python":
                # Skip dependent snippets that reference an external context (e.g., 'client')
                if "client." in code and "client =" not in code and "MeteoSwissClient(" not in code:
                    continue
                # Skip DataFrame output examples (they show DataFrame representation, not executable code)
                if code.strip().startswith("#") and ("station_abbr" in code or "stationcode" in code) and "=" not in code:
                    continue
                # Skip code blocks that are just comments or examples without imports
                if not any(keyword in code for keyword in ["import", "from", "=", "def", "class", "print", "assert"]):
                    continue
                # Write snippet to temp file and run with uv
                py_file = tmp_path / f"snippet_{abs(hash(code))}.py"
                py_file.write_text(code, encoding="utf-8")
                cmd = ["uv", "run", "python", str(py_file)]
                res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
                assert (
                    res.returncode == 0
                ), f"Python snippet failed ({md}):\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
                ran_any = True
            elif lang == "bash" and _should_run_bash(code):
                # Write bash to temp file and execute
                sh_file = tmp_path / f"snippet_{abs(hash(code))}.sh"
                sh_file.write_text(code, encoding="utf-8")
                res = subprocess.run(["bash", str(sh_file)], env=env, capture_output=True, text=True, timeout=30)
                assert (
                    res.returncode == 0
                ), f"Bash snippet failed ({md}):\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
                ran_any = True

    if not ran_any:
        pytest.skip("No eligible code blocks to run in markdown files.")


