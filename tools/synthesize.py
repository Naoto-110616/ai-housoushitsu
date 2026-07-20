#!/usr/bin/env python3
"""VOICEVOX Engine で台本 JSON から音声を合成し mp3 を生成する。

使い方:
    python tools/synthesize.py            # scripts/*.json のうち mp3 が無いものを全て合成
    python tools/synthesize.py scripts/ep001.json   # 指定した台本のみ合成

前提: VOICEVOX Engine が http://localhost:50021 で起動していること。
"""
import io
import json
import re
import sys
import time
from pathlib import Path

import requests
from pydub import AudioSegment

ROOT = Path(__file__).resolve().parent.parent
ENGINE = "http://localhost:50021"

CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
SPEAKERS = CONFIG["speakers"]
SPEED = float(CONFIG.get("speedScale", 1.0))

PAUSE_SAME_MS = 180   # 同一話者の文間ポーズ
PAUSE_TURN_MS = 400   # 話者交代時のポーズ
MAX_CHUNK = 180       # 1回の合成に渡す最大文字数


def wait_engine(timeout: int = 240) -> None:
    """エンジンの起動を待つ。"""
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
    """長文を文単位で MAX_CHUNK 以下に分割する。"""
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


def synth_chunk(text: str, speaker: int) -> AudioSegment:
    q = requests.post(
        f"{ENGINE}/audio_query",
        params={"text": text, "speaker": speaker},
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
    return AudioSegment.from_wav(io.BytesIO(w.content))


def build_episode(path: Path) -> None:
    ep = json.loads(path.read_text(encoding="utf-8"))
    out = ROOT / "docs" / "audio" / f"ep{ep['id']}.mp3"
    if out.exists():
        print(f"skip (exists): {out.name}")
        return

    print(f"synthesizing ep{ep['id']}: {ep['title']}")
    audio = AudioSegment.silent(duration=400)
    prev_speaker = None
    for i, line in enumerate(ep["lines"]):
        spk_key = line["s"]
        speaker_id = SPEAKERS[spk_key]
        pause = PAUSE_SAME_MS if spk_key == prev_speaker else PAUSE_TURN_MS
        if i > 0:
            audio += AudioSegment.silent(duration=pause)
        for chunk in split_text(line["t"]):
            audio += synth_chunk(chunk, speaker_id)
        prev_speaker = spk_key
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
            "album": CONFIG["title"],
        },
    )
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB, {len(audio) / 60000:.1f} min)")


def main() -> None:
    if len(sys.argv) > 1:
        targets = [Path(p) for p in sys.argv[1:]]
    else:
        targets = sorted((ROOT / "scripts").glob("ep*.json"))
    pending = [
        p for p in targets
        if not (ROOT / "docs" / "audio" / f"ep{json.loads(p.read_text(encoding='utf-8'))['id']}.mp3").exists()
    ]
    if not pending:
        print("合成対象なし")
        return
    wait_engine()
    for p in pending:
        build_episode(p)


if __name__ == "__main__":
    main()
