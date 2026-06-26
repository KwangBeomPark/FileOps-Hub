from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SPEC_FILE = ROOT / "IntegratedDataTool.spec"
SETUP_SCRIPT = ROOT / "setup.iss"
DIST_DIR = ROOT / "dist"
APP_EXE = DIST_DIR / "IntegratedDataTool.exe"


def format_command(command: list[str]) -> str:
    if sys.platform == "win32":
        return subprocess.list2cmdline(command)
    return " ".join(command)


def run(command: list[str], *, required: bool = True) -> int:
    print(f"\n$ {format_command(command)}")
    completed = subprocess.run(command, cwd=ROOT)
    if required and completed.returncode != 0:
        raise SystemExit(completed.returncode)
    return completed.returncode


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def require_file(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"Required file is missing: {path}")


def read_inno_value(key: str) -> str:
    prefix = f"{key}="
    for line in SETUP_SCRIPT.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(prefix.lower()):
            return stripped.split("=", 1)[1].strip()
    raise SystemExit(f"Missing {key} in {SETUP_SCRIPT}")


def setup_exe_path() -> Path:
    return DIST_DIR / f"{read_inno_value('OutputBaseFilename')}.exe"


def ensure_app_not_running() -> None:
    if sys.platform != "win32":
        return
    completed = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq IntegratedDataTool.exe", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0 and "IntegratedDataTool.exe" in completed.stdout:
        raise SystemExit("IntegratedDataTool.exe is running. Close the app before building release artifacts.")


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def find_iscc() -> str | None:
    found = shutil.which("iscc")
    if found:
        return found
    candidates = [
        Path.home() / "AppData" / "Local" / "Programs" / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles", "")) / "Inno Setup 6" / "ISCC.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def verify_source_tree() -> None:
    require_file(SRC / "main.py")
    require_file(SPEC_FILE)
    require_file(SETUP_SCRIPT)
    require_file(ROOT / "requirements.txt")


def run_static_checks(skip_ruff: bool) -> None:
    run([sys.executable, "-m", "compileall", "-q", "src", "tools"])
    run([sys.executable, "-m", "pip", "check"])

    if skip_ruff:
        print("\nSkipping ruff check by request.")
        return

    if module_available("ruff"):
        run([sys.executable, "-m", "ruff", "check", "src", "--select", "E9,F,B"])
    else:
        print("\nRuff is not installed; skipping optional ruff check.")


def build_app(skip_pyinstaller: bool) -> None:
    if skip_pyinstaller:
        print("\nSkipping PyInstaller build by request.")
        require_file(APP_EXE)
        return

    if not module_available("PyInstaller"):
        raise SystemExit("PyInstaller is not installed. Run: python -m pip install -r requirements.txt")

    run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", str(SPEC_FILE)])
    require_file(APP_EXE)
    print(f"\nBuilt app: {APP_EXE}")
    print(f"Size: {APP_EXE.stat().st_size:,} bytes")
    print(f"SHA-256: {sha256(APP_EXE)}")


def build_installer(skip_installer: bool) -> None:
    if skip_installer:
        print("\nSkipping Inno Setup installer build by request.")
        return

    iscc = find_iscc()
    if not iscc:
        print("\nInno Setup compiler (iscc) was not found on PATH.")
        print(f"Install Inno Setup or run iscc manually to produce {setup_exe_path()}.")
        return

    run([iscc, str(SETUP_SCRIPT)])
    setup_exe = setup_exe_path()
    require_file(setup_exe)
    print(f"\nBuilt installer: {setup_exe}")
    print(f"Size: {setup_exe.stat().st_size:,} bytes")
    print(f"SHA-256: {sha256(setup_exe)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and build FileOps Hub release artifacts.")
    parser.add_argument("--skip-ruff", action="store_true", help="Skip optional ruff check.")
    parser.add_argument("--skip-pyinstaller", action="store_true", help="Do not rebuild the app exe.")
    parser.add_argument("--skip-installer", action="store_true", help="Do not build the Inno Setup installer.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    verify_source_tree()
    ensure_app_not_running()
    run_static_checks(skip_ruff=args.skip_ruff)
    build_app(skip_pyinstaller=args.skip_pyinstaller)
    build_installer(skip_installer=args.skip_installer)

    print("\nBuild checks completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
