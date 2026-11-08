#!/usr/bin/env bash
# Layer 5A: Surgical Frame-Accurate Partial Video Splicer
# Adapted from higgsfield-ai/skills (higgsfield-faceless-video/scripts/assemble_partial_edit.sh)
# Usage: assemble_partial_edit.sh --source master_60fps.mp4 --manifest patches.json --out edited.mp4
set -euo pipefail

SOURCE=""
MANIFEST=""
OUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source) SOURCE="$2"; shift 2 ;;
    --manifest) MANIFEST="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    *) echo "ERROR: unknown argument $1" >&2; exit 2 ;;
  esac
done

for binary in ffmpeg ffprobe python3; do
  command -v "$binary" >/dev/null 2>&1 || { echo "ERROR: '$binary' not found" >&2; exit 1; }
done

[[ -f "$SOURCE" ]] || { echo "ERROR: --source file not found: $SOURCE" >&2; exit 1; }
[[ -f "$MANIFEST" ]] || { echo "ERROR: --manifest file not found: $MANIFEST" >&2; exit 1; }
[[ -n "$OUT" ]] || { echo "ERROR: --out is required" >&2; exit 1; }

TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

DIMS="$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$SOURCE")"
WIDTH="${DIMS%%,*}"
HEIGHT="${DIMS##*,}"
FPS_RAW="$(ffprobe -v error -select_streams v:0 -show_entries stream=avg_frame_rate -of csv=p=0 "$SOURCE")"
FPS="$(python3 -c "raw='$FPS_RAW'; n,_,d=raw.partition('/'); print(f'{float(n)/float(d) if d else float(n):.4f}')")"

CONCAT_LIST="$TMP/concat_list.txt"

python3 - "$SOURCE" "$MANIFEST" "$TMP" "$WIDTH" "$HEIGHT" "$FPS" "$CONCAT_LIST" <<'PY'
import json
import pathlib
import subprocess
import sys

source_mp4, manifest_path, tmp_dir, width, height, fps, concat_file = sys.argv[1:]
segments = json.loads(pathlib.Path(manifest_path).read_text(encoding="utf-8"))
if not isinstance(segments, list) or not segments:
    raise SystemExit("ERROR: patches.json must be a non-empty JSON array of segments")

concat_entries = []
for idx, seg in enumerate(segments):
    kind = seg.get("mode", "keep")
    start_s = float(seg["start_sec"])
    end_s = float(seg["end_sec"])
    dur_s = max(0.05, end_s - start_s)
    part_out = pathlib.Path(tmp_dir) / f"seg_{idx:03d}.ts"

    if kind == "patch":
        patch_video = seg["patch_video"]
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-i", patch_video,
            "-t", f"{dur_s:.4f}",
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps={fps}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "48000", "-ac", "2",
            str(part_out)
        ]
    else:
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-ss", f"{start_s:.4f}",
            "-t", f"{dur_s:.4f}",
            "-i", source_mp4,
            "-vf", f"fps={fps}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "48000", "-ac", "2",
            str(part_out)
        ]
    subprocess.run(cmd, check=True)
    concat_entries.append(f"file '{part_out.resolve()}'")

pathlib.Path(concat_file).write_text("\n".join(concat_entries) + "\n", encoding="utf-8")
PY

ffmpeg -y -v error -f concat -safe 0 -i "$CONCAT_LIST" \
  -c:v libx264 -preset fast -crf 17 -pix_fmt yuv420p -r "$FPS" \
  -c:a aac -b:a 192k "$TMP/assembled.mp4"

mv "$TMP/assembled.mp4" "$OUT"
echo "[assemble_partial_edit] Surgical splice completed -> $OUT"
