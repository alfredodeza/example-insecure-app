"""Runs the app and its workflows at every stage of the fixes, and checks what each step shows."""
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXES = ROOT / "fixes"
LEAKED = "practice_key_4f1d8c2b9e7a6035d1c8"
INJECTION = "' OR '1'='1' --"


PATCHES = {"app.py": ["parameterized-query.patch"],
           "tests.yml": ["pin-actions.patch", "least-privilege.patch"]}


def run_patch(path, patch, *flags):
    return subprocess.run(["patch", "-s", "-f", *flags, str(path), str(FIXES / patch)],
                          capture_output=True).returncode == 0


# The API key as a fresh clone has it, in the code, and after it moves to the environment.
KEY_IN_CODE = ("import hmac\nimport sqlite3\n", f'API_KEY = "{LEAKED}"')
KEY_FROM_ENV = ("import hmac\nimport os\nimport sqlite3\n",
                "# The key comes from the environment (uv run --env-file .env), never from the code.\n"
                'API_KEY = os.environ["PRACTICE_API_KEY"]')


def swap(path, old, new):
    text = path.read_text()
    for a, b in zip(old, new):
        text = text.replace(a, b)
    path.write_text(text)


def stage(tmp_path, *patches, target="app.py", key_from_env=False):
    """The file as a fresh clone has it, with these patches applied in order. Patches the
    repository already has are taken back out first, so this works at every step."""
    src = ROOT / target if target == "app.py" else ROOT / ".github" / "workflows" / target
    copy = tmp_path / Path(target).name
    shutil.copy(src, copy)
    for p in reversed(PATCHES[target]):
        if run_patch(copy, p, "-R", "--dry-run"):
            assert run_patch(copy, p, "-R")
    if target == "app.py":
        swap(copy, KEY_FROM_ENV, KEY_IN_CODE)
        assert KEY_IN_CODE[1] in copy.read_text()
        if key_from_env:
            swap(copy, KEY_IN_CODE, KEY_FROM_ENV)
    for p in patches:
        assert run_patch(copy, p), p
    return copy


def load(path, monkeypatch, key=None):
    if key is not None:
        monkeypatch.setenv("PRACTICE_API_KEY", key)
    name = f"app_{abs(hash(str(path)))}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module.app.test_client()


def test_health_and_search(tmp_path, monkeypatch):
    client = load(stage(tmp_path), monkeypatch)
    assert client.get("/health").get_json() == {"status": "ok"}
    titles = [b["title"] for b in client.get("/search?q=Flask").get_json()]
    assert titles == ["Flask documentation"]


def test_search_is_injectable_until_fixed(tmp_path, monkeypatch):
    client = load(stage(tmp_path, key_from_env=True), monkeypatch, key="k")
    assert len(client.get("/search", query_string={"q": INJECTION}).get_json()) == 3
    fixed = tmp_path / "fixed"
    fixed.mkdir()
    client = load(stage(fixed, "parameterized-query.patch", key_from_env=True), monkeypatch, key="k")
    assert client.get("/search", query_string={"q": INJECTION}).get_json() == []
    assert len(client.get("/search?q=documentation").get_json()) == 2


def test_hardcoded_key(tmp_path, monkeypatch):
    client = load(stage(tmp_path), monkeypatch)
    assert client.get("/bookmarks").status_code == 401
    assert client.get("/bookmarks", headers={"X-API-Key": LEAKED}).status_code == 200


def test_rotated_key(tmp_path, monkeypatch):
    client = load(stage(tmp_path, key_from_env=True), monkeypatch, key="practice_key_new")
    assert client.get("/bookmarks", headers={"X-API-Key": LEAKED}).status_code == 401
    assert client.get("/bookmarks", headers={"X-API-Key": "practice_key_new"}).status_code == 200


def test_make_key_writes_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = subprocess.run([sys.executable, str(ROOT / "make_key.py")], capture_output=True, text=True, check=True)
    assert out.stdout == "Wrote a new API key to .env\n"
    line = (tmp_path / ".env").read_text()
    assert line.startswith("PRACTICE_API_KEY=practice_key_") and LEAKED not in line


def zizmor(path):
    out = subprocess.run(["zizmor", "--offline", str(path)], capture_output=True, text=True,
                         env={"NO_COLOR": "1", "PATH": str(Path(sys.executable).parent)})
    return out.stdout + out.stderr


@pytest.mark.parametrize("patches, expect, absent", [
    ((), ["unpinned-uses", "excessive-permissions"], []),
    (("pin-actions.patch",), ["excessive-permissions"], ["unpinned-uses"]),
    (("pin-actions.patch", "least-privilege.patch"), ["No findings to report"], ["unpinned-uses", "excessive-permissions"]),
])
def test_tests_workflow(tmp_path, patches, expect, absent):
    out = zizmor(stage(tmp_path, *patches, target="tests.yml"))
    assert all(e in out for e in expect), out
    assert not any(a in out for a in absent), out


@pytest.mark.parametrize("name", ["release.yml", "dependency-review.yml"])
def test_other_workflows_are_clean(name):
    assert "No findings to report" in zizmor(ROOT / ".github" / "workflows" / name)
