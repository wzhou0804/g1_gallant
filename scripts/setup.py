"""Rebuild the isolated workspace from the local Isaac Sim seed and pinned sources."""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd=ROOT):
    subprocess.run([str(arg) for arg in args], cwd=cwd, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=Path, default=ROOT.parent / "go2_omniverse")
    args = parser.parse_args()
    if not (ROOT / ".venv/bin/python").exists():
        source_python = args.seed / ".cache-g1/python311"
        source_packages = args.seed / ".venv-g1-sim/lib/python3.11/site-packages"
        if not source_python.is_dir() or not source_packages.is_dir():
            parser.error("--seed must contain .cache-g1/python311 and .venv-g1-sim (Isaac Sim 5.1 / Isaac Lab 2.3.2).")
        if not (ROOT / ".python311").exists():
            run("cp", "-a", "--reflink=auto", source_python, ROOT / ".python311")
        run(ROOT / ".python311/bin/python", "-m", "venv", ROOT / ".venv")
        run("cp", "-a", "--reflink=auto", str(source_packages) + "/.", ROOT / ".venv/lib/python3.11/site-packages")

    (ROOT / "vendor").mkdir(exist_ok=True)
    sources = json.loads((ROOT / "sources.json").read_text())
    for name, source in sources.items():
        path = ROOT / "vendor" / name
        if not path.exists():
            run("git", "clone", "--depth", "1", source["url"], path)
        current = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip()
        if current != source["commit"]:
            run("git", "fetch", "--depth", "1", "origin", source["commit"], cwd=path)
            run("git", "checkout", "--detach", source["commit"], cwd=path)
        patch = ROOT / "patches" / f"{name}.patch"
        applied = subprocess.run(["git", "apply", "--reverse", "--check", str(patch)], cwd=path, capture_output=True)
        if applied.returncode != 0:
            run("git", "apply", "--check", patch, cwd=path)
            run("git", "apply", patch, cwd=path)

    python = ROOT / ".venv/bin/python"
    run(python, "-m", "pip", "install", "-c", ROOT / "constraints.txt", "-r", ROOT / "requirements-training.lock.txt", "--extra-index-url", "https://download.pytorch.org/whl/cu128")
    run(python, "-m", "pip", "install", "--no-deps", "--no-build-isolation", "-e", ROOT / "vendor/active-adaptation", "-e", ROOT / "vendor/Gallant")
    run(python, "-c", "from active_adaptation.project_loading.discovery import discover_projects; from active_adaptation.project_loading.manifest import save_projects; p=discover_projects(); [i.update(enabled=(n=='gallant')) for g in p.values() for n,i in g.items()]; save_projects(p)")
    run(python, "-m", "pip", "check")
    print("Ready: ./scripts/train.sh")


if __name__ == "__main__":
    main()
