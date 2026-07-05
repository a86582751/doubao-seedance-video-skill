#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
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


def ffmpeg_encoder_works(ffmpeg: str, encoder: str) -> bool:
    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        "color=c=black:s=64x64:d=0.1:r=24",
        "-frames:v",
        "1",
        "-c:v",
        encoder,
        "-f",
        "null",
        "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def choose_video_encoder(ffmpeg: str, requested: str, crf: int, preset: str) -> tuple[str, list[str]]:
    env_choice = os.environ.get("SEEDANCE_FFMPEG_VIDEO_ENCODER", "").strip()
    choice = env_choice or requested
    if choice in {"libx264", "x264", "cpu"}:
        return "libx264", ["-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p"]

    hardware_args = {
        "h264_nvenc": ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", str(crf), "-pix_fmt", "yuv420p"],
        "h264_qsv": ["-c:v", "h264_qsv", "-global_quality", str(crf), "-preset", "veryfast", "-look_ahead", "0"],
        "h264_amf": ["-c:v", "h264_amf", "-quality", "speed", "-rc", "cqp", "-qp_i", str(crf), "-qp_p", str(crf), "-qp_b", str(crf)],
    }

    if choice and choice != "auto":
        if choice not in hardware_args:
            raise ValueError(f"Unsupported video encoder: {choice}")
        if ffmpeg_encoder_works(ffmpeg, choice):
            return choice, hardware_args[choice]
        raise RuntimeError(f"Requested video encoder is unavailable or failed its smoke test: {choice}")

    for encoder in ("h264_nvenc", "h264_qsv", "h264_amf"):
        if ffmpeg_encoder_works(ffmpeg, encoder):
            return encoder, hardware_args[encoder]
    return "libx264", ["-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p"]


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


def expand_edl_segments(clips: list[dict[str, Any]]) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    for source_index, item in enumerate(clips, 1):
        source_segment_id = (
            item.get("source_segment_id")
            or item.get("segment_id")
            or item.get("clip_id")
            or item.get("id")
            or f"source_{source_index:02d}"
        )
        ranges = item.get("keep_ranges")
        if isinstance(ranges, list) and ranges:
            for range_index, keep_range in enumerate(ranges, 1):
                segment = dict(item)
                segment["source_index"] = source_index
                segment["source_segment_id"] = source_segment_id
                segment["range_index"] = range_index
                segment["start"] = keep_range.get("start", item.get("start", 0))
                segment["end"] = keep_range.get("end", item.get("end"))
                segment["beat"] = keep_range.get("reason", item.get("beat", item.get("reason", "")))
                segments.append(segment)
        else:
            segment = dict(item)
            segment["source_index"] = source_index
            segment["source_segment_id"] = source_segment_id
            segment["range_index"] = 1
            segments.append(segment)
    return segments


def source_duration(path_text: str, fallback: Any = None) -> float | None:
    try:
        return ffprobe_duration(Path(path_text))
    except Exception:
        if fallback is None:
            return None
        try:
            return float(fallback)
        except (TypeError, ValueError):
            return None


def build_edl_summary(edl: dict[str, Any]) -> dict[str, Any]:
    clips = edl.get("clips")
    if not isinstance(clips, list) or not clips:
        raise ValueError("EDL JSON must contain a non-empty clips array.")
    segments = expand_edl_segments(clips)
    if not segments:
        raise ValueError("EDL contained clips, but no editable segments were found.")

    timeline: list[dict[str, Any]] = []
    output_cursor = 0.0
    kept_by_path: dict[str, list[tuple[float, float]]] = {}
    sources: dict[str, dict[str, Any]] = {}
    for item in segments:
        path = str(Path(item["path"]))
        start = float(item.get("start", 0))
        end = float(item["end"])
        if end <= start:
            raise ValueError(f"Clip has invalid start/end: {start}/{end}")
        duration = end - start
        source_info = sources.setdefault(path, {
            "path": path,
            "source_index": item.get("source_index"),
            "source_segment_id": item.get("source_segment_id"),
            "duration": source_duration(path, item.get("source_duration") or item.get("duration")),
        })
        source_info["duration"] = source_info.get("duration") or source_duration(path, item.get("source_duration") or item.get("duration"))
        kept_by_path.setdefault(path, []).append((start, end))
        timeline.append({
            "output_start": round(output_cursor, 3),
            "output_end": round(output_cursor + duration, 3),
            "duration": round(duration, 3),
            "source_path": path,
            "source_index": item.get("source_index"),
            "source_segment_id": item.get("source_segment_id"),
            "range_index": item.get("range_index", 1),
            "source_start": round(start, 3),
            "source_end": round(end, 3),
            "beat": item.get("beat", item.get("reason", "")),
            "keep_reason": item.get("reason", item.get("keep_reason", "")),
        })
        output_cursor += duration

    omitted_by_source: list[dict[str, Any]] = []
    for path, info in sources.items():
        duration = info.get("duration")
        kept_ranges = sorted(kept_by_path.get(path, []))
        omitted: list[dict[str, Any]] = []
        cursor = 0.0
        for start, end in kept_ranges:
            if start > cursor:
                omitted.append({"start": round(cursor, 3), "end": round(start, 3), "duration": round(start - cursor, 3)})
            cursor = max(cursor, end)
        if duration is not None and duration > cursor:
            omitted.append({"start": round(cursor, 3), "end": round(duration, 3), "duration": round(duration - cursor, 3)})
        omitted_by_source.append({
            "path": path,
            "source_index": info.get("source_index"),
            "source_segment_id": info.get("source_segment_id"),
            "source_duration": round(duration, 3) if duration is not None else None,
            "kept_ranges": [{"start": round(start, 3), "end": round(end, 3), "duration": round(end - start, 3)} for start, end in kept_ranges],
            "omitted_ranges": omitted,
        })

    return {
        "output": edl.get("output"),
        "total_duration": round(output_cursor, 3),
        "timeline": timeline,
        "omitted_by_source": omitted_by_source,
    }


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
    segments = expand_edl_segments(clips)
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
    encoder_name, video_encoder_args = choose_video_encoder(ffmpeg, args.video_encoder, args.crf, args.preset)
    cmd += [
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[v]",
        "-map",
        "[a]",
        *video_encoder_args,
        "-c:a",
        "aac",
        "-b:a",
        args.audio_bitrate,
        "-movflags",
        "+faststart",
        str(output),
    ]
    run(cmd)
    print(json.dumps({"output": str(output), "video_encoder": encoder_name}, ensure_ascii=False, indent=2))
    return 0


def command_summarize_edl(args: argparse.Namespace) -> int:
    edl = json.loads(args.edl.read_text(encoding="utf-8-sig"))
    summary = build_edl_summary(edl)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"summary": str(args.output), "total_duration": summary["total_duration"]}, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
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
    apply_edl.add_argument(
        "--video-encoder",
        default="auto",
        choices=["auto", "libx264", "h264_nvenc", "h264_qsv", "h264_amf"],
        help="Video encoder for EDL export. 'auto' smoke-tests hardware encoders and falls back to libx264.",
    )
    apply_edl.add_argument("--audio-bitrate", default="160k")
    apply_edl.set_defaults(func=command_apply_edl)

    summarize_edl = sub.add_parser("summarize-edl", help="Summarize kept and omitted EDL ranges as edit facts.")
    summarize_edl.add_argument("--edl", type=Path, required=True)
    summarize_edl.add_argument("--output", type=Path, default=None)
    summarize_edl.add_argument("--story", default="", help=argparse.SUPPRESS)
    summarize_edl.add_argument("--audio-style", default="", help=argparse.SUPPRESS)
    summarize_edl.set_defaults(func=command_summarize_edl)
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
