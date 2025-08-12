import hashlib
import tarfile
from pathlib import Path
import yaml
import subprocess
import sys
import os

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache"
RAW_DIR = ROOT / "frames_raw"
CLEAN_DIR = ROOT / "frames_clean"
OUT_DIR = ROOT / "outputs"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_run_id(cfg: dict) -> str:
    h = hashlib.sha256()
    for key in ("video_path", "fps", "max_frames", "scale_width", "dedup_threshold"):
        h.update(str(cfg.get(key)).encode())
    # include file hash
    vp = Path(cfg["video_path"])
    if vp.exists():
        h.update(sha256_file(vp).encode())
    return h.hexdigest()[:16]


def run(cmd: list[str]):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def main():
    cfg_path = ROOT / "config.yaml"
    if not cfg_path.exists():
        print("Missing config.yaml", file=sys.stderr)
        sys.exit(1)
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

    run_id = compute_run_id(cfg)
    print(f"Run ID: {run_id}")

    RAW_DIR.mkdir(exist_ok=True)
    CLEAN_DIR.mkdir(exist_ok=True)
    OUT_DIR.mkdir(exist_ok=True)
    CACHE.mkdir(exist_ok=True)

    # 1) extract frames
    raw_subdir = RAW_DIR / run_id
    clean_subdir = CLEAN_DIR / run_id
    if not raw_subdir.exists() or not any(raw_subdir.glob("*.jpg")):
        raw_subdir.mkdir(parents=True, exist_ok=True)
        run([
            sys.executable,
            str(ROOT / "scripts" / "extract_frames.py"),
            "--video",
            cfg["video_path"],
            "--out",
            str(raw_subdir),
            "--fps",
            str(cfg.get("fps", 2.0)),
            "--max_frames",
            str(cfg.get("max_frames", 0)),
            "--scale_width",
            str(cfg.get("scale_width", 0)),
        ])
    else:
        print("Skip extract: frames exist.")

    # 2) dedup
    if not (clean_subdir / "dedup_report.json").exists():
        run([
            sys.executable,
            str(ROOT / "scripts" / "dedup.py"),
            "--src",
            str(raw_subdir),
            "--dst",
            str(clean_subdir),
            "--threshold",
            str(cfg.get("dedup_threshold", 8)),
        ])
    else:
        print("Skip dedup: report exists.")

    # 3) package outputs
    tar_path = OUT_DIR / f"dataset_{run_id}.tar.gz"
    if not tar_path.exists():
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(clean_subdir, arcname=f"frames_clean_{run_id}")
        print(f"Packaged: {tar_path}")
    else:
        print("Skip package: archive exists.")

    # write summary
    summary = OUT_DIR / f"summary_{run_id}.txt"
    summary.write_text(
        f"run_id={run_id}\nvideo={cfg['video_path']}\n",
        encoding="utf-8",
    )
    print("Done.")


if __name__ == "__main__":
    main()