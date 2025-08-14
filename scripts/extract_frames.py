import subprocess
import shutil
import os
from pathlib import Path


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def extract_from_video(video_path: Path, out_dir: Path, fps: float = 2.0, max_frames: int | None = None, scale_width: int | None = None):
    ensure_dir(out_dir)
    if not has_ffmpeg():
        raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

    vf_parts = []
    if fps and fps > 0:
        vf_parts.append(f"fps={fps}")
    if scale_width and scale_width > 0:
        vf_parts.append(f"scale={scale_width}:-1")

    vf = ",".join(vf_parts) if vf_parts else "null"
    pattern = str(out_dir / "frame_%06d.jpg")

    cmd = ["ffmpeg", "-y", "-i", str(video_path), "-vf", vf, "-qscale:v", "2", pattern]
    subprocess.run(cmd, check=True)

    # enforce max_frames if specified (delete extras)
    if max_frames is not None and max_frames > 0:
        frames = sorted(out_dir.glob("frame_*.jpg"))
        for f in frames[max_frames:]:
            f.unlink()


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", type=str, required=True)
    ap.add_argument("--out", type=str, required=True)
    ap.add_argument("--fps", type=float, default=2.0)
    ap.add_argument("--max_frames", type=int, default=0)
    ap.add_argument("--scale_width", type=int, default=0)
    args = ap.parse_args()

    max_frames = args.max_frames if args.max_frames and args.max_frames > 0 else None
    scale_width = args.scale_width if args.scale_width and args.scale_width > 0 else None

    extract_from_video(Path(args.video), Path(args.out), args.fps, max_frames, scale_width)


if __name__ == "__main__":
    main()