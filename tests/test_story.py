import json
import os
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "story.py"


def run_script(cwd, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def git(cwd, *args):
    env = os.environ.copy()
    env.update({"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.com", "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.com"})
    return subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=cwd, env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def make_repo(tmp_path):
    git(tmp_path, "init", "-b", "main")
    (tmp_path / "README.md").write_text("base\n")
    git(tmp_path, "add", "README.md")
    git(tmp_path, "commit", "-m", "docs: base")
    git(tmp_path, "checkout", "-b", "feature")
    return tmp_path


def test_json_output_shape(tmp_path):
    data = json.loads(run_script(tmp_path).stdout)
    assert set(data) == {"commits", "files_changed", "suggested_title"}


def test_empty_non_repo_is_safe(tmp_path):
    data = json.loads(run_script(tmp_path).stdout)
    assert data == {"commits": [], "files_changed": [], "suggested_title": ""}


def test_collects_commits_since_base(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "app.py").write_text("print('x')\n")
    git(repo, "add", "app.py")
    git(repo, "commit", "-m", "feat: add app")
    data = json.loads(run_script(repo, "--base", "main").stdout)
    assert data["commits"][0]["subject"] == "feat: add app"


def test_collects_file_stats(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "app.py").write_text("one\ntwo\n")
    git(repo, "add", "app.py")
    git(repo, "commit", "-m", "feat: add app")
    data = json.loads(run_script(repo).stdout)
    assert data["files_changed"] == [{"path": "app.py", "additions": 2, "deletions": 0}]


def test_falls_back_to_master(tmp_path):
    git(tmp_path, "init", "-b", "master")
    (tmp_path / "README.md").write_text("base\n")
    git(tmp_path, "add", "README.md")
    git(tmp_path, "commit", "-m", "docs: base")
    git(tmp_path, "checkout", "-b", "feature")
    (tmp_path / "x.txt").write_text("x\n")
    git(tmp_path, "add", "x.txt")
    git(tmp_path, "commit", "-m", "feat: add x")
    data = json.loads(run_script(tmp_path, "--base", "main").stdout)
    assert data["suggested_title"] == "feat: add x"


def test_binary_numstat_is_safe(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "logo.bin").write_bytes(b"\x00\x01\x02")
    git(repo, "add", "logo.bin")
    git(repo, "commit", "-m", "chore: add binary")
    data = json.loads(run_script(repo).stdout)
    assert data["files_changed"] == [{"path": "logo.bin", "additions": 0, "deletions": 0}]
