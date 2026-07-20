#!/usr/bin/env python3
"""台本 JSON から音声を合成し mp3 を生成する（多言語対応）。

- 日本語 (ja): VOICEVOX Engine (http://localhost:50021) で合成
- その他の言語: edge-tts (Microsoft neural TTS) で合成

台本の配置:
    scripts/epNNN.json          … 日本語（原本）
    scripts/<lang>/epNNN.json   … 翻訳版 (en / es / pt ...)
出力:
    docs/audio/epNNN.mp3         … 日本語
    docs/<lang>/audio/epNNN.mp3  … 翻訳版
"""
import asyncio
import io
import json
import re
import time
from pathlib import Path

import requests
from pydub import AudioSegment

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ENGINE = "http://localhost:50021"

CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
LANGS = CONFIG["languages"]
SPEED = float(CONFIG.get("speedScale", 1.0))

PAUSE_SAME_MS = 180
PAUSE_TURN_MS = 400
MAX_CHUNK = 180
EDGE_RETRIES = 3


# ---------- VOICEVOX ----------

def wait_engine(timeout: int = 240) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{ENGINE}/version", timeout=5)
            if r.ok:
                print(f"VOICEVOX Engine version: {r.text.strip()}")
                return
        except requests.RequestException:
            pass
        time.sleep(3)
    raise RuntimeError("VOICEVOX Engine が起動しませんでした")


def split_text(text: str) -> list[str]:
    sentences = re.split(r"(?<=[。！？!?])", text)
    chunks: list[str] = []
    buf = ""
    for s in sentences:
        if not s:
            continue
        if len(buf) + len(s) > MAX_CHUNK and buf:
            chunks.append(buf)
            buf = s
        else:
            buf += s
    if buf:
        chunks.append(buf)
    return chunks


def synth_voicevox_line(text: str, speaker: int) -> AudioSegment:
    audio = AudioSegment.empty()
    for chunk in split_text(text):
        q = requests.post(
            f"{ENGINE}/audio_query",
            params={"text": chunk, "speaker": speaker},
            timeout=60,
        )
        q.raise_for_status()
        query = q.json()
        query["speedScale"] = SPEED
        query["prePhonemeLength"] = 0.05
        query["postPhonemeLength"] = 0.1
        w = requests.post(
            f"{ENGINE}/synthesis",
            params={"speaker": speaker},
            json=query,
            timeout=300,
        )
        w.raise_for_status()
        audio += AudioSegment.from_wav(io.BytesIO(w.content))
    return audio


# ---------- edge-tts ----------

def synth_edge_line(text: str, voice: str) -> AudioSegment:
    import edge_tts

    async def run() -> bytes:
        communicate = edge_tts.Communicate(text, voice)
        buf = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buf += chunk["data"]
        return buf

    last_err = None
    for attempt in range(EDGE_RETRIES):
        try:
            data = asyncio.run(run())
            if data:
                return AudioSegment.from_file(io.BytesIO(data), format="mp3")
            raise RuntimeError("edge-tts returned empty audio")
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"edge-tts failed for voice {voice}: {last_err}")


# ---------- 共通 ----------

def build_episode(path: Path, lang_cfg: dict) -> None:
    ep = json.loads(path.read_text(encoding="utf-8"))
    lang_dir = lang_cfg["dir"]
    out = DOCS / lang_dir / "audio" / f"ep{ep['id']}.mp3" if lang_dir else DOCS / "audio" / f"ep{ep['id']}.mp3"
    if out.exists():
        return

    engine = lang_cfg["engine"]
    voices = lang_cfg["voices"]
    print(f"[{lang_cfg['language']}] synthesizing ep{ep['id']}: {ep['title']}")

    audio = AudioSegment.silent(duration=400)
    prev_speaker = None
    for i, line in enumerate(ep["lines"]):
        spk = line["s"]
        pause = PAUSE_SAME_MS if spk == prev_speaker else PAUSE_TURN_MS
        if i > 0:
            audio += AudioSegment.silent(duration=pause)
        if engine == "voicevox":
            audio += synth_voicevox_line(line["t"], voices[spk])
        else:
            audio += synth_edge_line(line["t"], voices[spk])
        prev_speaker = spk
        if (i + 1) % 10 == 0 or i + 1 == len(ep["lines"]):
            print(f"  line {i + 1}/{len(ep['lines'])} done")

    audio += AudioSegment.silent(duration=600)
    audio = audio.set_frame_rate(44100).set_channels(1)
    out.parent.mkdir(parents=True, exist_ok=True)
    audio.export(
        out,
        format="mp3",
        bitrate="96k",
        tags={
            "title": ep["title"],
            "artist": CONFIG["author"],
            "album": lang_cfg["title"],
        },
    )
    print(f"  wrote {out.relative_to(ROOT)} ({out.stat().st_size / 1e6:.1f} MB, {len(audio) / 60000:.1f} min)")


def pending_for(lang_cfg: dict) -> list[Path]:
    lang_dir = lang_cfg["dir"]
    script_dir = ROOT / "scripts" / lang_dir if lang_dir else ROOT / "scripts"
    audio_dir = DOCS / lang_dir / "audio" if lang_dir else DOCS / "audio"
    result = []
    if not script_dir.exists():
        return result
    for p in sorted(script_dir.glob("ep*.json")):
        ep_id = json.loads(p.read_text(encoding="utf-8"))["id"]
        if not (audio_dir / f"ep{ep_id}.mp3").exists():
            result.append(p)
    return result


def main() -> None:
    work = {code: pending_for(cfg) for code, cfg in LANGS.items()}
    total = sum(len(v) for v in work.values())
    if total == 0:
        print("合成対象なし")
        return
    if any(work[code] and LANGS[code]["engine"] == "voicevox" for code in work):
        wait_engine()
    for code, paths in work.items():
        for p in paths:
            build_episode(p, LANGS[code])


if __name__ == "__main__":
    main()
