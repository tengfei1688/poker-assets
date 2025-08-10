import argparse, os, zipfile, json, shutil, glob, subprocess
from PIL import Image
import imagehash

IMG_EXT = {".png",".jpg",".jpeg",".bmp",".webp"}
VID_EXT = {".mp4",".mov",".mkv",".avi",".wmv"}


def find_first(patterns):
    for pat in patterns:
        matches = sorted(glob.glob(pat))
        if matches:
            return matches[0]
    return None


def extract_images_from_zip(zip_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    copied = 0
    with zipfile.ZipFile(zip_path, "r") as z:
        for m in z.infolist():
            _, ext = os.path.splitext(m.filename.lower())
            if ext in IMG_EXT:
                z.extract(m, out_dir)
                copied += 1
    return copied


def ffmpeg_extract_frames(video_path, out_dir, fps=2):
    os.makedirs(out_dir, exist_ok=True)
    cmd = [
        "ffmpeg","-hide_banner","-loglevel","error",
        "-i", video_path,
        "-vf", f"fps={fps}",
        os.path.join(out_dir, "frame_%06d.png")
    ]
    subprocess.check_call(cmd)


def list_images(root):
    files = []
    for r, _, fs in os.walk(root):
        for fn in fs:
            ext = os.path.splitext(fn.lower())[1]
            if ext in IMG_EXT:
                files.append(os.path.join(r, fn))
    files.sort()
    return files


def ensure_rgb(path):
    im = Image.open(path)
    if im.mode != "RGB":
        im = im.convert("RGB")
    return im


def dedup_images(src_files, out_dir, dup_thresh=4):
    os.makedirs(out_dir, exist_ok=True)
    kept = []
    hashes = []
    for fp in src_files:
        try:
            im = ensure_rgb(fp)
            h = imagehash.average_hash(im)
        except Exception:
            continue
        is_dup = any((h - prev) <= dup_thresh for prev in hashes)
        if not is_dup:
            dst = os.path.join(out_dir, f"img_{len(kept):06d}.png")
            im.save(dst, "PNG")
            kept.append(dst)
            hashes.append(h)
    return kept


def zip_dir(src_dir, zip_path):
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for root, _, files in os.walk(src_dir):
            for fn in files:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, src_dir)
                z.write(full, rel)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", help="Path to ZIP with images")
    ap.add_argument("--video", help="Path to video file")
    ap.add_argument("--fps", type=int, default=2)
    ap.add_argument("--dup_thresh", type=int, default=4)
    args = ap.parse_args()

    zip_path = args.zip or find_first(["*.zip"])
    vid_path = args.video or find_first(["*.mp4","*.mov","*.mkv","*.avi","*.wmv"])

    work = "work"
    outputs = "outputs"
    img_src = os.path.join(work, "images_src")
    frames_raw = os.path.join(work, "frames_raw")
    frames_clean = os.path.join(work, "frames_clean")

    for d in [work, outputs, img_src, frames_raw, frames_clean]:
        os.makedirs(d, exist_ok=True)

    stats = {
        "zip": zip_path,
        "video": vid_path,
        "fps": args.fps,
        "dup_thresh": args.dup_thresh,
    }

    zip_images = 0
    if zip_path and os.path.isfile(zip_path):
        zip_images = extract_images_from_zip(zip_path, img_src)
    stats["zip_images_found"] = zip_images

    raw_frames = 0
    if vid_path and os.path.isfile(vid_path):
        ffmpeg_extract_frames(vid_path, frames_raw, fps=args.fps)
        raw_frames = len(list_images(frames_raw))
    stats["video_frames_raw"] = raw_frames

    combined_list = []
    combined_list.extend(list_images(img_src))
    combined_list.extend(list_images(frames_raw))
    stats["combined_total"] = len(combined_list)

    kept = dedup_images(combined_list, frames_clean, dup_thresh=args.dup_thresh)
    stats["frames_clean"] = len(kept)

    zip_dir(frames_raw, os.path.join(outputs, "frames_raw.zip"))
    zip_dir(frames_clean, os.path.join(outputs, "frames_clean.zip"))
    with open(os.path.join(outputs, "report.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print("Done. Stats:\n", json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()