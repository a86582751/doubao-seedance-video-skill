#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


def find_tool(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    raise RuntimeError(f"{name} not found on PATH.")


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"Command failed: {' '.join(cmd)}")


def ffprobe_duration(path: Path) -> float:
    ffprobe = find_tool("ffprobe")
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return float(result.stdout.strip())


def ffprobe_has_audio(path: Path) -> bool:
    ffprobe = find_tool("ffprobe")
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return bool(result.stdout.strip())


def safe_stem(index: int, path: Path) -> str:
    return f"clip{index:02d}_{''.join(ch if ch.isalnum() or ch in '._-' else '_' for ch in path.stem)[:48]}"


def command_pack(args: argparse.Namespace) -> int:
    ffmpeg = find_tool("ffmpeg")
    output_dir = args.output_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_visual_review_pack"
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "fps": args.fps,
        "thumb_width": args.thumb_width,
        "clips": [],
        "review_instruction": (
            "Inspect contact sheets and dense frames. Return text only: pass/fail, "
            "recommended trim start/end, visible defects, repeated beats, and regenerate advice."
        ),
    }
    for index, video_text in enumerate(args.videos, 1):
        video = Path(video_text).resolve()
        duration = ffprobe_duration(video)
        clip_dir = output_dir / safe_stem(index, video)
        frame_dir = clip_dir / "frames"
        frame_dir.mkdir(parents=True, exist_ok=True)
        contact = clip_dir / "contact_sheet.jpg"
        start_frame = clip_dir / "start.jpg"
        end_frame = clip_dir / "end.jpg"

        run([
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video),
            "-vf",
            f"fps={args.fps},scale={args.thumb_width}:-1",
            str(frame_dir / "frame_%04d.jpg"),
        ])
        frame_count = len(list(frame_dir.glob("frame_*.jpg")))
        cols = max(1, args.tile_cols)
        rows = max(1, math.ceil(frame_count / cols))
        if frame_count:
            run([
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-framerate",
                "1",
                "-i",
                str(frame_dir / "frame_%04d.jpg"),
                "-vf",
                f"tile={cols}x{rows}:padding=6:margin=6:color=white",
                "-frames:v",
                "1",
                str(contact),
            ])
        for timestamp, target in ((min(0.15, duration / 2), start_frame), (max(0, duration - 0.2), end_frame)):
            run([
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{timestamp:.3f}",
                "-i",
                str(video),
                "-frames:v",
                "1",
                str(target),
            ])
        manifest["clips"].append({
            "index": index,
            "path": str(video),
            "duration": duration,
            "frame_dir": str(frame_dir),
            "contact_sheet": str(contact) if contact.exists() else "",
            "start_frame": str(start_frame),
            "end_frame": str(end_frame),
            "suggested_edl_item": {
                "path": str(video),
                "start": 0.0,
                "end": duration,
                "reason": "replace with visual review decision",
                "regenerate": False,
            },
        })
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"review_dir": str(output_dir), "manifest": str(manifest_path)}, ensure_ascii=False, indent=2))
    return 0


def command_apply_edl(args: argparse.Namespace) -> int:
    ffmpeg = find_tool("ffmpeg")
    edl = json.loads(args.edl.read_text(encoding="utf-8-sig"))
    clips = edl.get("clips")
    if not isinstance(clips, list) or not clips:
        raise ValueError("EDL JSON must contain a non-empty clips array.")
    output = args.output or Path(edl.get("output") or args.edl.with_suffix(".mp4"))
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [ffmpeg, "-y"]
    segments: list[dict[str, Any]] = []
    for item in clips:
        ranges = item.get("keep_ranges")
        if isinstance(ranges, list) and ranges:
            for keep_range in ranges:
                segment = dict(item)
                segment["start"] = keep_range.get("start", item.get("start", 0))
                segment["end"] = keep_range.get("end", item.get("end"))
                segment["beat"] = keep_range.get("reason", item.get("beat", item.get("reason", "")))
                segments.append(segment)
        else:
            segments.append(item)
    if not segments:
        raise ValueError("EDL contained clips, but no editable segments were found.")
    for item in segments:
        cmd += ["-i", str(Path(item["path"]))]
    filters: list[str] = []
    concat_inputs: list[str] = []
    for index, item in enumerate(segments):
        start = float(item.get("start", 0))
        end = float(item["end"])
        if end <= start:
            raise ValueError(f"Clip {index + 1} has invalid start/end: {start}/{end}")
        duration = end - start
        filters.append(f"[{index}:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,fps=24,format=yuv420p[v{index}]")
        if ffprobe_has_audio(Path(item["path"])):
            filters.append(
                f"[{index}:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS,"
                f"aresample=48000,aformat=sample_rates=48000:channel_layouts=stereo[a{index}]"
            )
        else:
            filters.append(
                f"anullsrc=channel_layout=stereo:sample_rate=48000,"
                f"atrim=duration={duration:.6f},asetpts=PTS-STARTPTS[a{index}]"
            )
        concat_inputs.append(f"[v{index}][a{index}]")
    filters.append("".join(concat_inputs) + f"concat=n={len(segments)}:v=1:a=1[v][a]")
    cmd += [
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-c:v",
        "libx264",
        "-preset",
        args.preset,
        "-crf",
        str(args.crf),
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        args.audio_bitrate,
        "-movflags",
        "+faststart",
        str(output),
    ]
    run(cmd)
    print(json.dumps({"output": str(output)}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare dense frame review packs and apply assembly EDLs for Seedance clips.")
    sub = parser.add_subparsers(dest="command", required=True)
    pack = sub.add_parser("pack", help="Extract dense frames and contact sheets for disposable visual-review subagents.")
    pack.add_argument("--video", dest="videos", action="append", required=True, help="Input video path. Repeat for multiple clips.")
    pack.add_argument("--output-dir", type=Path, required=True)
    pack.add_argument("--fps", type=float, default=2.0)
    pack.add_argument("--thumb-width", type=int, default=320)
    pack.add_argument("--tile-cols", type=int, default=8)
    pack.set_defaults(func=command_pack)

    apply_edl = sub.add_parser("apply-edl", help="Apply an assembly edit decision list with FFmpeg.")
    apply_edl.add_argument("--edl", type=Path, required=True)
    apply_edl.add_argument("--output", type=Path, default=None)
    apply_edl.add_argument("--crf", type=int, default=20)
    apply_edl.add_argument("--preset", default="medium")
    apply_edl.add_argument("--audio-bitrate", default="160k")
    apply_edl.set_defaults(func=command_apply_edl)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
