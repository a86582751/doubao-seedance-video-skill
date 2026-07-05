#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


ENV_FILE = Path.home() / ".codex" / "seedance.env"
DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "doubao-seedance-2-0-260128"
DEFAULT_CREATE_PATH = "/contents/generations/tasks"
DEFAULT_STATUS_PATH = "/contents/generations/tasks/{task_id}"
DEFAULT_LIST_PATH = "/contents/generations/tasks"
SUCCESS_STATUSES = {"succeeded", "success", "completed", "done"}
FAILURE_STATUSES = {"failed", "error", "cancelled", "canceled", "expired"}
MODEL_PROFILES = {
    "seedance-2.0": {
        "model_id": "doubao-seedance-2-0-260128",
        "label": "Doubao Seedance 2.0",
        "goal": "highest_quality",
        "recommendation": "Use when image quality, coherence, 1080p/4k output, or final delivery quality matters most.",
        "supported_resolutions": ["480p", "720p", "1080p", "4k"],
    },
    "fast": {
        "model_id": "doubao-seedance-2-0-fast-260128",
        "label": "Doubao Seedance 2.0 Fast",
        "goal": "balanced_speed_cost",
        "recommendation": "Use for drafts, iterations, and scenes where speed/cost matter more than maximum quality.",
        "supported_resolutions": ["480p", "720p"],
    },
    "mini": {
        "model_id": "doubao-seedance-2-0-mini-260615",
        "label": "Doubao Seedance 2.0 Mini",
        "goal": "lowest_cost",
        "recommendation": "Use for lowest-cost tests, rough blocking, and high-volume simple shots.",
        "supported_resolutions": ["480p", "720p"],
    },
}
MODEL_ALIASES = {
    "2.0": "doubao-seedance-2-0-260128",
    "seedance": "doubao-seedance-2-0-260128",
    "seedance-2.0": "doubao-seedance-2-0-260128",
    "quality": "doubao-seedance-2-0-260128",
    "doubao-seedance-2-0": "doubao-seedance-2-0-260128",
    "fast": "doubao-seedance-2-0-fast-260128",
    "seedance-fast": "doubao-seedance-2-0-fast-260128",
    "mini": "doubao-seedance-2-0-mini-260615",
    "cheap": "doubao-seedance-2-0-mini-260615",
}
MODEL_ID_TO_PROFILE = {value["model_id"]: value for value in MODEL_PROFILES.values()}
OFFICIAL_PRICE_NO_VIDEO = {
    "doubao-seedance-2-0-260128": {"480p": 46.0, "720p": 46.0, "1080p": 51.0, "4k": 26.0},
    "doubao-seedance-2-0-fast-260128": {"480p": 37.0, "720p": 37.0},
    "doubao-seedance-2-0-mini-260615": {"480p": 23.0, "720p": 23.0},
}
OFFICIAL_PRICE_WITH_VIDEO = {
    "doubao-seedance-2-0-260128": {"480p": 28.0, "720p": 28.0, "1080p": 31.0, "4k": 16.0},
    "doubao-seedance-2-0-fast-260128": {"480p": 22.0, "720p": 22.0},
    "doubao-seedance-2-0-mini-260615": {"480p": 14.0, "720p": 14.0},
}
RESOURCE_PACKAGE_BASE_PRICE_PER_MILLION = {
    "doubao-seedance-2-0-260128": 28.0,
    "doubao-seedance-2-0-fast-260128": 22.0,
    "doubao-seedance-2-0-mini-260615": 14.0,
}
OFFICIAL_16_9_TOKENS_5S = {
    "480p": 50220.0,
    "720p": 108000.0,
    "1080p": 243000.0,
    "4k": 972000.0,
}
DIMENSIONS = {
    ("480p", "16:9"): (832, 480),
    ("720p", "16:9"): (1280, 720),
    ("1080p", "16:9"): (1920, 1080),
    ("4k", "16:9"): (3840, 2160),
    ("480p", "21:9"): (1120, 480),
    ("720p", "21:9"): (1680, 720),
    ("1080p", "21:9"): (2520, 1080),
    ("4k", "21:9"): (5040, 2160),
    ("480p", "4:3"): (640, 480),
    ("720p", "4:3"): (960, 720),
    ("1080p", "4:3"): (1440, 1080),
    ("4k", "4:3"): (2880, 2160),
    ("480p", "9:16"): (480, 832),
    ("720p", "9:16"): (720, 1280),
    ("1080p", "9:16"): (1080, 1920),
    ("4k", "9:16"): (2160, 3840),
    ("480p", "1:1"): (640, 640),
    ("720p", "1:1"): (960, 960),
    ("1080p", "1:1"): (1440, 1440),
    ("4k", "1:1"): (2160, 2160),
    ("480p", "3:4"): (480, 640),
    ("720p", "3:4"): (720, 960),
    ("1080p", "3:4"): (1080, 1440),
    ("4k", "3:4"): (2160, 2880),
}


def load_env_file(path: Path = ENV_FILE) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


ENV_FALLBACK = load_env_file()


def env(name: str, default: str = "", *fallbacks: str) -> str:
    for key in (name, *fallbacks):
        value = os.environ.get(key)
        if value:
            return value
    for key in (name, *fallbacks):
        value = ENV_FALLBACK.get(key)
        if value:
            return value
    return default


def env_bool(name: str, default: bool, *fallbacks: str) -> bool:
    value = env(name, str(default).lower(), *fallbacks).strip().lower()
    return value in {"1", "true", "yes", "y", "on"}


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return value[:4] + "*" * max(4, len(value) - 8) + value[-4:]


def endpoint(base_url: str, path: str) -> str:
    return urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))


def http_json(method: str, url: str, api_key: str, payload: Any | None = None, timeout: int = 120) -> Any:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Authorization": f"Bearer {api_key}"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            data = response.read()
            if not data:
                return {}
            return json.loads(data.decode("utf-8"))
    except HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {exc.reason}: {body_text}") from exc
    except URLError as exc:
        raise RuntimeError(f"Network error calling {url}: {exc.reason}") from exc


def deep_get(data: Any, *path: str) -> Any:
    current = data
    for part in path:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def first_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, list):
        for item in value:
            found = first_string(item)
            if found:
                return found
    if isinstance(value, dict):
        for key in ("video_url", "last_frame_url", "content_url", "output", "outputs", "url", "file", "href"):
            found = first_string(value.get(key))
            if found:
                return found
    return None


def extract_task_id(data: Any) -> str:
    candidates = [
        deep_get(data, "data", "task_id"),
        deep_get(data, "data", "id"),
        data.get("task_id") if isinstance(data, dict) else None,
        data.get("id") if isinstance(data, dict) else None,
    ]
    for candidate in candidates:
        if candidate:
            return str(candidate)
    raise RuntimeError("Task was created but no task id was found: " + json.dumps(data, ensure_ascii=False)[:2000])


def extract_status(data: Any) -> str:
    candidates = [
        deep_get(data, "data", "status"),
        deep_get(data, "data", "state"),
        data.get("status") if isinstance(data, dict) else None,
        data.get("state") if isinstance(data, dict) else None,
    ]
    for candidate in candidates:
        if candidate:
            return str(candidate).lower()
    return "unknown"


def extract_video_url(data: Any) -> str | None:
    return first_string(
        deep_get(data, "content", "video_url")
        or deep_get(data, "data", "content", "video_url")
        or deep_get(data, "data", "video_url")
        or deep_get(data, "data", "output")
        or deep_get(data, "data", "outputs")
        or (data.get("video_url") if isinstance(data, dict) else None)
        or (data.get("output") if isinstance(data, dict) else None)
        or (data.get("outputs") if isinstance(data, dict) else None)
    )


def extract_last_frame_url(data: Any) -> str | None:
    return first_string(
        deep_get(data, "content", "last_frame_url")
        or deep_get(data, "data", "content", "last_frame_url")
        or deep_get(data, "data", "last_frame_url")
        or (data.get("last_frame_url") if isinstance(data, dict) else None)
    )


def error_message(data: Any) -> str:
    return first_string(
        deep_get(data, "error", "message")
        or deep_get(data, "data", "error", "message")
        or deep_get(data, "message")
        or deep_get(data, "msg")
    ) or ""


def image_to_data_uri(path_text: str) -> str:
    if path_text.startswith("<") and path_text.endswith(">"):
        return path_text
    if re.match(r"^(https?://|asset://|data:)", path_text, flags=re.I):
        return path_text
    path = Path(path_text)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")
    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def build_content(prompt: str, images: list[str], roles: list[str]) -> list[dict[str, Any]]:
    if not prompt.strip():
        raise ValueError("Prompt is required.")
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt.strip()}]
    for index, image in enumerate(images):
        item: dict[str, Any] = {"type": "image_url", "image_url": {"url": image_to_data_uri(image)}}
        if index < len(roles) and roles[index]:
            item["role"] = roles[index]
        content.append(item)
    return content


@dataclass
class Config:
    api_key: str
    base_url: str
    model: str
    create_path: str
    status_path_template: str
    list_path: str
    poll_interval: float
    max_wait_minutes: int

    @classmethod
    def from_env(cls) -> "Config":
        api_key = env("SEEDANCE_API_KEY", "", "ARK_API_KEY").strip()
        if not api_key:
            raise ValueError(f"Missing SEEDANCE_API_KEY or ARK_API_KEY. Set it in the process env or {ENV_FILE}.")
        return cls(
            api_key=api_key,
            base_url=env("SEEDANCE_BASE_URL", DEFAULT_BASE_URL).strip(),
            model=env("SEEDANCE_MODEL", DEFAULT_MODEL).strip(),
            create_path=env("SEEDANCE_CREATE_PATH", DEFAULT_CREATE_PATH).strip(),
            status_path_template=env("SEEDANCE_STATUS_PATH_TEMPLATE", DEFAULT_STATUS_PATH).strip(),
            list_path=env("SEEDANCE_LIST_PATH", DEFAULT_LIST_PATH).strip(),
            poll_interval=float(env("SEEDANCE_POLL_INTERVAL", "5")),
            max_wait_minutes=int(env("SEEDANCE_MAX_WAIT_MINUTES", "30")),
        )

    def masked(self) -> dict[str, Any]:
        return {
            "api_key": mask_secret(self.api_key),
            "base_url": self.base_url,
            "model": self.model,
            "create_path": self.create_path,
            "status_path_template": self.status_path_template,
            "list_path": self.list_path,
            "poll_interval": self.poll_interval,
            "max_wait_minutes": self.max_wait_minutes,
            "env_file": str(ENV_FILE),
        }


def media_to_url(path_text: str) -> str:
    if path_text.startswith("<") and path_text.endswith(">"):
        return path_text
    if re.match(r"^(https?://|asset://|data:)", path_text, flags=re.I):
        return path_text
    path = Path(path_text)
    if not path.exists():
        raise FileNotFoundError(f"Media file not found: {path}")
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def build_content_item(kind: str, value: str, role: str = "") -> dict[str, Any]:
    kind = kind.strip()
    if kind == "text":
        return {"type": "text", "text": value}
    if kind == "draft_task":
        return {"type": "draft_task", "draft_task": {"id": value}}
    if kind not in {"image_url", "video_url", "audio_url"}:
        raise ValueError(f"Unsupported content type: {kind}")
    key = kind
    item: dict[str, Any] = {"type": kind, key: {"url": media_to_url(value)}}
    if role:
        item["role"] = role
    return item


def make_payload(args: argparse.Namespace, config: Config, content: list[dict[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": args.model or config.model,
        "content": content,
        "generate_audio": bool(args.generate_audio),
        "watermark": bool(args.watermark),
        "return_last_frame": bool(args.return_last_frame),
    }
    if bool(args.camera_fixed):
        payload["camera_fixed"] = True
    if args.duration is not None:
        payload["duration"] = int(args.duration)
    if getattr(args, "frames", None) is not None:
        payload["frames"] = int(args.frames)
    if args.resolution:
        payload["resolution"] = args.resolution
    if args.ratio:
        payload["ratio"] = args.ratio
    for attr, key in [
        ("seed", "seed"),
        ("service_tier", "service_tier"),
        ("execution_expires_after", "execution_expires_after"),
        ("callback_url", "callback_url"),
        ("priority", "priority"),
    ]:
        value = getattr(args, attr, None)
        if value not in (None, ""):
            payload[key] = value
    if getattr(args, "draft", False):
        payload["draft"] = True
    if getattr(args, "web_search", False):
        payload["tools"] = [{"type": "web_search"}]
    if getattr(args, "extra_json", None):
        extra = json.loads(args.extra_json)
        if not isinstance(extra, dict):
            raise ValueError("--extra-json must be a JSON object.")
        payload.update(extra)
    return payload


def create_task(config: Config, payload: dict[str, Any]) -> tuple[str, Any]:
    data = http_json("POST", endpoint(config.base_url, config.create_path), config.api_key, payload, timeout=120)
    return extract_task_id(data), data


def get_task(config: Config, task_id: str) -> Any:
    path = config.status_path_template.format(task_id=task_id)
    return http_json("GET", endpoint(config.base_url, path), config.api_key, None, timeout=60)


def delete_task(config: Config, task_id: str) -> Any:
    path = config.status_path_template.format(task_id=task_id)
    return http_json("DELETE", endpoint(config.base_url, path), config.api_key, None, timeout=60)


def list_tasks(config: Config, query: dict[str, str]) -> Any:
    if query:
        from urllib.parse import urlencode

        path = config.list_path + ("&" if "?" in config.list_path else "?") + urlencode(query)
    else:
        path = config.list_path
    return http_json("GET", endpoint(config.base_url, path), config.api_key, None, timeout=60)


def poll_task(config: Config, task_id: str) -> Any:
    started = time.time()
    last_data: Any = None
    while True:
        data = get_task(config, task_id)
        last_data = data
        status = extract_status(data)
        print(json.dumps({"task_id": task_id, "status": status, "video_url": bool(extract_video_url(data)), "last_frame_url": bool(extract_last_frame_url(data))}, ensure_ascii=False), flush=True)
        if status in SUCCESS_STATUSES:
            return data
        if status in FAILURE_STATUSES:
            msg = error_message(data)
            raise RuntimeError(f"Seedance task failed: {status}" + (f" - {msg}" if msg else ""))
        if time.time() - started > config.max_wait_minutes * 60:
            raise TimeoutError(f"Timed out waiting for {task_id}. Last response: {json.dumps(last_data, ensure_ascii=False)[:2000]}")
        time.sleep(max(1.0, config.poll_interval))


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text)[:80] or "seedance"


def download_url(url: str, output_dir: Path, label: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = ".mp4" if ".mp4" in url.lower().split("?", 1)[0] else Path(url.split("?", 1)[0]).suffix or ".mp4"
    path = output_dir / f"{timestamp}_{safe_name(label)}{suffix}"
    counter = 1
    while path.exists():
        path = output_dir / f"{timestamp}_{safe_name(label)}_{counter:02d}{suffix}"
        counter += 1
    request = Request(url, headers={"User-Agent": "Codex Seedance CLI"})
    with urlopen(request, timeout=240) as response, path.open("wb") as file:
        shutil.copyfileobj(response, file)
    return path


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_text_or_literal(value: str) -> str:
    try:
        path = Path(value)
        if path.exists():
            return path.read_text(encoding="utf-8-sig")
    except (OSError, ValueError):
        pass
    return value


def parse_prompt_items(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, list):
        prompts: list[str] = []
        for item in data:
            if isinstance(item, str):
                prompts.append(item)
            elif isinstance(item, dict) and item.get("prompt"):
                prompts.append(str(item["prompt"]))
        return prompts
    if isinstance(data, dict) and isinstance(data.get("prompts"), list):
        return [str(item.get("prompt") if isinstance(item, dict) else item) for item in data["prompts"]]
    raise ValueError("Prompts JSON must be a list of strings, a list of {prompt}, or {prompts:[...]}.")


def find_ffmpeg() -> str | None:
    for candidate in (
        shutil.which("ffmpeg"),
        str(Path("tools") / "ffmpeg" / "bin" / "ffmpeg.exe"),
        str(Path("tools") / "ffmpeg" / "ffmpeg.exe"),
    ):
        if candidate and Path(candidate).exists():
            return candidate
    return None


def concat_videos(paths: list[Path], output_path: Path) -> Path:
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("FFmpeg not found. Install ffmpeg or omit --concat.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as list_file:
        list_path = Path(list_file.name)
        for path in paths:
            escaped = str(path.resolve()).replace("'", "'\\''")
            list_file.write(f"file '{escaped}'\n")
    try:
        cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_path), "-c", "copy", str(output_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_path), "-c:v", "libx264", "-c:a", "aac", str(output_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "ffmpeg concat failed")
        return output_path
    finally:
        list_path.unlink(missing_ok=True)


def normalize_model(value: str) -> str:
    key = (value or "").strip()
    if not key:
        return ""
    return MODEL_ALIASES.get(key.lower(), key)


def choose_model(goal: str, resolution: str) -> tuple[str, str]:
    normalized_goal = (goal or "quality").strip().lower()
    if normalized_goal in {"quality", "best", "highest"}:
        return "doubao-seedance-2-0-260128", "highest quality requested"
    if normalized_goal in {"balanced", "fast", "speed"}:
        if resolution in {"1080p", "4k"}:
            return "doubao-seedance-2-0-260128", "Fast is documented for 480p/720p, so high resolution falls back to Seedance 2.0"
        return "doubao-seedance-2-0-fast-260128", "balanced speed and cost requested"
    if normalized_goal in {"cheap", "lowest", "cost", "mini"}:
        if resolution in {"1080p", "4k"}:
            return "doubao-seedance-2-0-260128", "Mini is documented for 480p/720p, so high resolution falls back to Seedance 2.0"
        return "doubao-seedance-2-0-mini-260615", "lowest cost requested"
    if resolution in {"1080p", "4k"}:
        return "doubao-seedance-2-0-260128", "auto selected Seedance 2.0 for high-resolution output"
    return "doubao-seedance-2-0-fast-260128", "auto selected Fast for ordinary 480p/720p iteration"


def price_for(model: str, resolution: str, has_video_input: bool) -> float | None:
    table = OFFICIAL_PRICE_WITH_VIDEO if has_video_input else OFFICIAL_PRICE_NO_VIDEO
    model_prices = table.get(model, {})
    return model_prices.get(resolution) or model_prices.get("default")


def resource_package_base_price_for(model: str) -> float | None:
    return RESOURCE_PACKAGE_BASE_PRICE_PER_MILLION.get(model)


def extract_usage_tokens(data: Any) -> float | None:
    candidates = [
        deep_get(data, "usage", "completion_tokens"),
        deep_get(data, "usage", "total_tokens"),
        deep_get(data, "data", "usage", "completion_tokens"),
        deep_get(data, "data", "usage", "total_tokens"),
        deep_get(data, "response", "usage", "completion_tokens"),
        deep_get(data, "response", "usage", "total_tokens"),
    ]
    for candidate in candidates:
        if isinstance(candidate, (int, float)) and candidate > 0:
            return float(candidate)
        if isinstance(candidate, str):
            try:
                value = float(candidate)
            except ValueError:
                continue
            if value > 0:
                return value
    return None


def payload_has_video_input(payload: dict[str, Any]) -> bool:
    content = payload.get("content", [])
    if not isinstance(content, list):
        return False
    return any(isinstance(item, dict) and item.get("type") == "video_url" for item in content)


def estimate_tokens_for_settings(
    resolution: str,
    ratio: str,
    fps: float,
    output_duration: float,
    count: int = 1,
    input_video_duration: float = 0,
    width: int = 0,
    height: int = 0,
    use_official_examples: bool = True,
) -> tuple[float | None, float | None, float | None, int | None, int | None]:
    key = (resolution, ratio)
    if width and height:
        resolved_width, resolved_height = width, height
    elif key in DIMENSIONS:
        resolved_width, resolved_height = DIMENSIONS[key]
    elif ratio == "adaptive":
        resolved_width, resolved_height = DIMENSIONS.get((resolution, "16:9"), (1280, 720))
    else:
        return None, None, None, None, None
    total_seconds = output_duration + input_video_duration
    formula_tokens = resolved_width * resolved_height * fps * total_seconds / 1024 * count
    official_example_tokens = None
    if not (width and height) and ratio == "16:9" and resolution in OFFICIAL_16_9_TOKENS_5S:
        official_example_tokens = OFFICIAL_16_9_TOKENS_5S[resolution] / 5 * total_seconds * count
    billing_tokens = official_example_tokens if use_official_examples and official_example_tokens is not None else formula_tokens
    return billing_tokens, formula_tokens, official_example_tokens, resolved_width, resolved_height


def make_billing_summary(
    model: str,
    resolution: str,
    has_video_input: bool,
    billing_tokens: float | None,
    token_source: str,
) -> dict[str, Any]:
    official_price = price_for(model, resolution, has_video_input)
    package_base_price = resource_package_base_price_for(model)
    resource_package_debit_ratio = None
    resource_package_tokens = None
    resource_package_equivalent_cost = None
    if billing_tokens is not None and official_price is not None and package_base_price and package_base_price > 0:
        resource_package_debit_ratio = official_price / package_base_price
        resource_package_tokens = billing_tokens * resource_package_debit_ratio
        resource_package_equivalent_cost = resource_package_tokens / 1_000_000 * package_base_price
    return {
        "model": model,
        "resolution": resolution,
        "has_video_input": has_video_input,
        "token_source": token_source,
        "billing_tokens": billing_tokens,
        "official_price_per_million_rmb": official_price,
        "estimated_pay_as_you_go_cost_rmb": (billing_tokens / 1_000_000 * official_price) if billing_tokens is not None and official_price is not None else None,
        "resource_package_base_price_per_million_rmb": package_base_price,
        "resource_package_debit_ratio": resource_package_debit_ratio,
        "resource_package_tokens_estimated": resource_package_tokens,
        "resource_package_equivalent_cost_rmb": resource_package_equivalent_cost,
    }


def billing_summary_for_payload(payload: dict[str, Any], response_data: Any | None = None) -> dict[str, Any]:
    model = normalize_model(str(payload.get("model") or DEFAULT_MODEL))
    resolution = str(payload.get("resolution") or "720p")
    ratio = str(payload.get("ratio") or "16:9")
    fps = 24.0
    duration = float(payload.get("duration") or 10)
    if payload.get("frames") and not payload.get("duration"):
        try:
            duration = float(payload["frames"]) / fps
        except (TypeError, ValueError):
            duration = 10.0
    has_video_input = payload_has_video_input(payload)
    usage_tokens = extract_usage_tokens(response_data) if response_data is not None else None
    token_source = "api_usage" if usage_tokens is not None else "local_estimate"
    warning = None
    billing_tokens = usage_tokens
    formula_tokens = None
    official_example_tokens = None
    width = None
    height = None
    if billing_tokens is None:
        billing_tokens, formula_tokens, official_example_tokens, width, height = estimate_tokens_for_settings(
            resolution=resolution,
            ratio=ratio,
            fps=fps,
            output_duration=duration,
            count=1,
            input_video_duration=0,
        )
    summary = make_billing_summary(model, resolution, has_video_input, billing_tokens, token_source)
    summary.update({
        "ratio": ratio,
        "fps": fps,
        "output_duration": duration,
        "formula_tokens": formula_tokens,
        "official_16_9_example_tokens": official_example_tokens,
        "width": width,
        "height": height,
        "note": "Use api_usage when available; otherwise this is a local estimate. Resource-package debit uses official_price / model package base price.",
    })
    if has_video_input and usage_tokens is None:
        warning = "Payload contains video input, but API usage was unavailable and reference-video duration is unknown; local estimate may be low."
    if warning:
        summary["warning"] = warning
    return summary


def aggregate_billing_summaries(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not items:
        return None
    total_tokens = sum(float(item.get("billing_tokens") or 0) for item in items)
    total_cash = sum(float(item.get("estimated_pay_as_you_go_cost_rmb") or 0) for item in items)
    total_package_tokens = sum(float(item.get("resource_package_tokens_estimated") or 0) for item in items)
    total_package_cost = sum(float(item.get("resource_package_equivalent_cost_rmb") or 0) for item in items)
    return {
        "segments": len(items),
        "billing_tokens": total_tokens,
        "estimated_pay_as_you_go_cost_rmb": total_cash,
        "resource_package_tokens_estimated": total_package_tokens,
        "resource_package_equivalent_cost_rmb": total_package_cost,
        "token_sources": sorted({str(item.get("token_source")) for item in items if item.get("token_source")}),
        "note": "Aggregate of per-segment billing summaries. Final FFmpeg editing itself does not consume Seedance tokens.",
    }


def model_profile(model: str) -> dict[str, Any]:
    return MODEL_ID_TO_PROFILE.get(model, {"model_id": model, "label": model, "recommendation": "Custom or unknown model id.", "supported_resolutions": []})


def add_common_generation_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--duration", type=int, default=int(env("SEEDANCE_DURATION", "10")), help="Output duration in seconds. Official Seedance 2.0 range is 4-15 seconds.")
    parser.add_argument("--frames", type=int, default=None, help="Optional frame count. If set, official API treats frames as higher priority than duration where supported.")
    parser.add_argument("--resolution", default=env("SEEDANCE_RESOLUTION", "720p"))
    parser.add_argument("--ratio", default=env("SEEDANCE_RATIO", "16:9"))
    parser.add_argument("--model", default="")
    parser.add_argument("--generate-audio", action=argparse.BooleanOptionalAction, default=env_bool("SEEDANCE_GENERATE_AUDIO", True))
    parser.add_argument("--watermark", action=argparse.BooleanOptionalAction, default=env_bool("SEEDANCE_WATERMARK", False))
    parser.add_argument("--return-last-frame", action=argparse.BooleanOptionalAction, default=env_bool("SEEDANCE_RETURN_LAST_FRAME", False))
    parser.add_argument("--camera-fixed", action=argparse.BooleanOptionalAction, default=env_bool("SEEDANCE_CAMERA_FIXED", False))
    parser.add_argument("--draft", action="store_true", help="Create a Draft video where supported, e.g. Seedance 1.5 pro.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--service-tier", default=env("SEEDANCE_SERVICE_TIER", ""), help="e.g. default or flex where supported.")
    parser.add_argument("--execution-expires-after", type=int, default=None)
    parser.add_argument("--callback-url", default=env("SEEDANCE_CALLBACK_URL", ""))
    parser.add_argument("--priority", type=int, default=None)
    parser.add_argument("--web-search", action="store_true", help="Add tools=[{'type':'web_search'}] where supported.")
    parser.add_argument("--extra-json", default="", help="Merge an additional JSON object into the create payload.")
    parser.add_argument("--output-dir", type=Path, default=Path.cwd() / "outputs")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--show-config", action="store_true")
    parser.add_argument("--no-download", action="store_true")


def command_generate(args: argparse.Namespace) -> int:
    config = Config.from_env()
    if args.payload_json:
        payload = json.loads(read_text_or_literal(args.payload_json))
        if not isinstance(payload, dict):
            raise ValueError("--payload-json must be a JSON object.")
        payload.setdefault("model", args.model or config.model)
    elif args.content_json:
        content = json.loads(read_text_or_literal(args.content_json))
        if isinstance(content, dict) and isinstance(content.get("content"), list):
            content = content["content"]
        if not isinstance(content, list):
            raise ValueError("--content-json must be a content array or an object with content array.")
    elif args.draft_task:
        content = [build_content_item("draft_task", args.draft_task)]
    else:
        content = build_content(args.prompt, args.image or [], args.image_role or [])
        for value, role in zip(args.video or [], args.video_role or []):
            content.append(build_content_item("video_url", value, role))
        for index, value in enumerate(args.video or []):
            if index >= len(args.video_role or []):
                content.append(build_content_item("video_url", value, "reference_video"))
        for value, role in zip(args.audio or [], args.audio_role or []):
            content.append(build_content_item("audio_url", value, role))
        for index, value in enumerate(args.audio or []):
            if index >= len(args.audio_role or []):
                content.append(build_content_item("audio_url", value, "reference_audio"))
        payload = make_payload(args, config, content)
    if args.show_config:
        print(json.dumps(config.masked(), ensure_ascii=False, indent=2))
    if args.dry_run:
        safe_payload = json.loads(json.dumps(payload, ensure_ascii=False))
        for item in safe_payload.get("content", []):
            if item.get("type") == "image_url":
                url = item.get("image_url", {}).get("url", "")
                if url.startswith("data:"):
                    item["image_url"]["url"] = url[:40] + "...<base64 omitted>"
        print(json.dumps({"dry_run": True, "payload": safe_payload}, ensure_ascii=False, indent=2))
        return 0
    task_id, create_data = create_task(config, payload)
    final_data = poll_task(config, task_id) if not args.create_only else create_data
    video_url = extract_video_url(final_data) or extract_video_url(create_data)
    last_frame_url = extract_last_frame_url(final_data) or extract_last_frame_url(create_data)
    result: dict[str, Any] = {
        "task_id": task_id,
        "video_url": video_url,
        "last_frame_url": last_frame_url,
        "billing_summary": billing_summary_for_payload(payload, final_data),
        "response": final_data,
    }
    if video_url and not args.no_download:
        result["local_path"] = str(download_url(video_url, args.output_dir, task_id))
    result_path = args.output_dir / f"{safe_name(task_id)}.json"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(result_path, result)
    result["result_json"] = str(result_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_status(args: argparse.Namespace) -> int:
    config = Config.from_env()
    data = get_task(config, args.task_id)
    result: dict[str, Any] = {
        "task_id": args.task_id,
        "status": extract_status(data),
        "video_url": extract_video_url(data),
        "last_frame_url": extract_last_frame_url(data),
        "usage": data.get("usage") if isinstance(data, dict) else None,
        "response": data,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_delete(args: argparse.Namespace) -> int:
    config = Config.from_env()
    data = delete_task(config, args.task_id)
    print(json.dumps({"task_id": args.task_id, "deleted": True, "response": data}, ensure_ascii=False, indent=2))
    return 0


def command_list(args: argparse.Namespace) -> int:
    config = Config.from_env()
    query = {}
    for key in ("status", "model"):
        value = getattr(args, key)
        if value:
            query[key] = value
    for attr, key in [("limit", "limit"), ("page_size", "page_size"), ("created_after", "created_after"), ("created_before", "created_before")]:
        value = getattr(args, attr)
        if value not in (None, ""):
            query[key] = str(value)
    data = list_tasks(config, query)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def command_chain(args: argparse.Namespace) -> int:
    config = Config.from_env()
    prompts = parse_prompt_items(args.prompts_json)
    if not prompts:
        raise ValueError("No prompts found.")
    local_paths: list[Path] = []
    records: list[dict[str, Any]] = []
    initial_image_url = args.initial_image_url
    args.return_last_frame = True
    for index, prompt in enumerate(prompts, 1):
        print(f"Creating segment {index}/{len(prompts)}", flush=True)
        content = build_content(prompt, [initial_image_url] if initial_image_url else [], [])
        payload = make_payload(args, config, content)
        if args.dry_run:
            records.append({"index": index, "payload": payload})
            initial_image_url = f"<last_frame_url_from_segment_{index}>"
            continue
        task_id, create_data = create_task(config, payload)
        final_data = poll_task(config, task_id)
        video_url = extract_video_url(final_data) or extract_video_url(create_data)
        last_frame_url = extract_last_frame_url(final_data) or extract_last_frame_url(create_data)
        if not video_url:
            raise RuntimeError(f"Segment {index} succeeded but no video_url was found.")
        local_path = None if args.no_download else download_url(video_url, args.output_dir, f"{task_id}_part{index:02d}")
        if local_path:
            local_paths.append(local_path)
        records.append({
            "index": index,
            "prompt": prompt,
            "task_id": task_id,
            "video_url": video_url,
            "last_frame_url": last_frame_url,
            "local_path": str(local_path) if local_path else None,
            "billing_summary": billing_summary_for_payload(payload, final_data),
            "response": final_data,
        })
        if index < len(prompts):
            if not last_frame_url:
                raise RuntimeError(f"Segment {index} did not return last_frame_url.")
            initial_image_url = last_frame_url
    result: dict[str, Any] = {"segments": records}
    summaries = [record["billing_summary"] for record in records if isinstance(record.get("billing_summary"), dict)]
    aggregate = aggregate_billing_summaries(summaries)
    if aggregate:
        result["billing_summary"] = aggregate
    if args.concat and local_paths:
        output = args.output_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_seedance_chain.mp4"
        result["concat_path"] = str(concat_videos(local_paths, output))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result_path = args.output_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_seedance_chain.json"
    write_json(result_path, result)
    result["result_json"] = str(result_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_estimate(args: argparse.Namespace) -> int:
    key = (args.resolution, args.ratio)
    if args.width and args.height:
        width, height = args.width, args.height
    elif key in DIMENSIONS:
        width, height = DIMENSIONS[key]
    elif args.ratio == "adaptive":
        width, height = DIMENSIONS.get((args.resolution, "16:9"), (1280, 720))
    else:
        raise ValueError(f"Unknown dimensions for resolution={args.resolution}, ratio={args.ratio}. Pass --width and --height.")
    selected_model, model_reason = choose_model(args.goal, args.resolution)
    if args.model:
        selected_model = normalize_model(args.model)
        model_reason = "model explicitly provided"
    profile = model_profile(selected_model)
    if profile.get("supported_resolutions") and args.resolution not in profile["supported_resolutions"]:
        model_reason += f"; warning: {profile['label']} is not documented for {args.resolution}"
    total_seconds = args.duration + (args.input_video_duration if args.video_input else 0)
    billing_tokens, formula_tokens, official_example_tokens, _, _ = estimate_tokens_for_settings(
        resolution=args.resolution,
        ratio=args.ratio,
        fps=args.fps,
        output_duration=args.duration,
        count=args.count,
        input_video_duration=args.input_video_duration if args.video_input else 0,
        width=args.width,
        height=args.height,
        use_official_examples=args.use_official_examples,
    )
    official_price = args.price_per_million if args.price_per_million is not None else price_for(selected_model, args.resolution, args.video_input)
    package_base_price = (
        args.package_price_per_million
        if args.package_price_per_million is not None
        else resource_package_base_price_for(selected_model)
    )
    billing_summary = make_billing_summary(selected_model, args.resolution, args.video_input, billing_tokens, "local_estimate")
    if args.price_per_million is not None or args.package_price_per_million is not None:
        billing_summary = make_billing_summary(selected_model, args.resolution, args.video_input, billing_tokens, "local_estimate")
        billing_summary["official_price_per_million_rmb"] = official_price
        billing_summary["resource_package_base_price_per_million_rmb"] = package_base_price
        if billing_tokens is not None and official_price is not None and package_base_price and package_base_price > 0:
            ratio = official_price / package_base_price
            tokens = billing_tokens * ratio
            billing_summary["resource_package_debit_ratio"] = ratio
            billing_summary["resource_package_tokens_estimated"] = tokens
            billing_summary["resource_package_equivalent_cost_rmb"] = tokens / 1_000_000 * package_base_price
            billing_summary["estimated_pay_as_you_go_cost_rmb"] = billing_tokens / 1_000_000 * official_price
    result: dict[str, Any] = {
        "model": selected_model,
        "model_label": profile.get("label"),
        "model_reason": model_reason,
        "supported_resolutions": profile.get("supported_resolutions", []),
        "width": width,
        "height": height,
        "fps": args.fps,
        "output_duration": args.duration,
        "input_video_duration": args.input_video_duration if args.video_input else 0,
        "count": args.count,
        "formula": "(input_video_duration + output_duration) * output_width * output_height * fps / 1024 * count",
        "formula_tokens": formula_tokens,
        "official_16_9_example_tokens": official_example_tokens,
        "billing_tokens_used_for_cost": billing_tokens,
        "official_price_per_million_rmb": billing_summary.get("official_price_per_million_rmb"),
        "estimated_pay_as_you_go_cost_rmb": billing_summary.get("estimated_pay_as_you_go_cost_rmb"),
        "resource_package_base_price_per_million_rmb": billing_summary.get("resource_package_base_price_per_million_rmb"),
        "resource_package_debit_ratio": billing_summary.get("resource_package_debit_ratio"),
        "resource_package_tokens_estimated": billing_summary.get("resource_package_tokens_estimated"),
        "resource_package_tokens_per_clip": (billing_summary.get("resource_package_tokens_estimated") / args.count) if billing_summary.get("resource_package_tokens_estimated") is not None and args.count else None,
        "resource_package_equivalent_cost_rmb": billing_summary.get("resource_package_equivalent_cost_rmb"),
        "note": "Pay-as-you-go cost uses the official scenario price. Resource packages debit model-specific package tokens by official_price / package_base_price; API usage.completion_tokens is authoritative after generation.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate videos with Doubao Seedance 2.0 on Volcano Ark.")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Create, poll, and optionally download one video.")
    gen.add_argument("--prompt", default="")
    gen.add_argument("--image", action="append", help="Image URL, asset:// id, data URI, or local image path. Repeatable.")
    gen.add_argument("--image-role", action="append", default=[], help="Optional image role, e.g. first_frame or last_frame. Repeatable.")
    gen.add_argument("--video", action="append", help="Video URL, asset:// id, data URI, or local video path. Repeatable.")
    gen.add_argument("--video-role", action="append", default=[], help="Optional video role, usually reference_video. Repeatable.")
    gen.add_argument("--audio", action="append", help="Audio URL, asset:// id, data URI, or local audio path. Repeatable.")
    gen.add_argument("--audio-role", action="append", default=[], help="Optional audio role, usually reference_audio. Repeatable.")
    gen.add_argument("--draft-task", default="", help="Create final video from an existing draft task id.")
    gen.add_argument("--content-json", default="", help="Raw content array JSON, path to JSON, or object containing content.")
    gen.add_argument("--payload-json", default="", help="Raw full create-task payload JSON or path. Missing model defaults to configured model.")
    gen.add_argument("--create-only", action="store_true")
    add_common_generation_args(gen)
    gen.set_defaults(func=command_generate)

    status = sub.add_parser("status", help="Fetch one task status.")
    status.add_argument("task_id")
    status.set_defaults(func=command_status)

    delete = sub.add_parser("delete", help="Cancel queued task or delete a task record.")
    delete.add_argument("task_id")
    delete.set_defaults(func=command_delete)

    list_parser = sub.add_parser("list", help="List tasks using query parameters supported by Ark.")
    list_parser.add_argument("--status", default="")
    list_parser.add_argument("--model", default="")
    list_parser.add_argument("--limit", type=int, default=None)
    list_parser.add_argument("--page-size", type=int, default=None)
    list_parser.add_argument("--created-after", default="")
    list_parser.add_argument("--created-before", default="")
    list_parser.set_defaults(func=command_list)

    chain = sub.add_parser("chain", help="Generate continuous segments using last frame as next first frame.")
    chain.add_argument("--prompts-json", type=Path, required=True)
    chain.add_argument("--initial-image-url", default="")
    chain.add_argument("--concat", action="store_true")
    add_common_generation_args(chain)
    chain.set_defaults(func=command_chain)

    estimate = sub.add_parser("estimate", help="Estimate video tokens.")
    estimate.add_argument("--duration", type=float, default=10)
    estimate.add_argument("--resolution", default="720p")
    estimate.add_argument("--ratio", default="16:9")
    estimate.add_argument("--fps", type=float, default=24)
    estimate.add_argument("--count", type=int, default=1)
    estimate.add_argument("--width", type=int, default=0)
    estimate.add_argument("--height", type=int, default=0)
    estimate.add_argument("--model", default="", help="Model id or alias: quality, fast, mini, cheap.")
    estimate.add_argument("--goal", default="quality", choices=["quality", "balanced", "cheap", "auto"], help="Choose a model by task goal when --model is omitted.")
    estimate.add_argument("--video-input", action="store_true", help="Estimate the pricing path that includes video input/reference.")
    estimate.add_argument("--input-video-duration", type=float, default=0, help="Seconds of video input/reference. Used only with --video-input.")
    estimate.add_argument("--price-per-million", type=float, default=None, help="Override official RMB price per million tokens.")
    estimate.add_argument("--package-price-per-million", "--package-base-price-per-million", dest="package_price_per_million", type=float, default=None, help="Override the resource package base RMB price per million package tokens. Defaults to the selected model's package base price.")
    estimate.add_argument("--use-official-examples", action=argparse.BooleanOptionalAction, default=True, help="For 16:9 presets, use official screenshot token examples for cost.")
    estimate.set_defaults(func=command_estimate)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
