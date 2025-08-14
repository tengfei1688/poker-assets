from pathlib import Path
from PIL import Image
import imagehash
from tqdm import tqdm
import shutil
import json


def phash(img_path: Path):
    with Image.open(img_path) as im:
        im = im.convert("RGB")
        return imagehash.phash(im)


def deduplicate(src_dir: Path, dst_dir: Path, threshold: int = 8):
    dst_dir.mkdir(parents=True, exist_ok=True)
    mapping = []
    kept = {}
    kept_order = []

    frames = sorted([p for p in src_dir.glob("*.jpg")])
    for p in tqdm(frames, desc="dedup"):
        h = phash(p)
        is_dup = False
        for kh in kept_order:
            if h - kh <= threshold:
                mapping.append({"duplicate": p.name, "kept": kept[kh]})
                is_dup = True
                break
        if not is_dup:
            kept[h] = p.name
            kept_order.append(h)
            shutil.copy2(p, dst_dir / p.name)

    report = {
        "total": len(frames),
        "kept": len(kept_order),
        "duplicates": len(mapping),
        "threshold": threshold,
        "kept_files": list({v for v in kept.values()}),
        "duplicates_map": mapping,
    }
    (dst_dir / "dedup_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main():
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="raw frames dir")
    ap.add_argument("--dst", required=True, help="clean frames dir")
    ap.add_argument("--threshold", type=int, default=8)
    args = ap.parse_args()

    report = deduplicate(Path(args.src), Path(args.dst), args.threshold)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()