"""
Voiceover Generator — Tech 8ytees
Priority : ElevenLabs  (human-quality, free tier 10k chars/mo)
Fallback 1: Kokoro TTS  (offline, open-source, very natural)
Fallback 2: edge-tts    (Microsoft Neural voices, may fail on CI)
Fallback 3: gTTS        (last resort)
Subtitles  : openai-whisper → synced .vtt (word-level timestamps)
"""
import os
import re
import time
import subprocess
import json

try:
    import requests
except ImportError:
    requests = None

import random


# ── Text sanitization (removes markdown that TTS would read aloud) ────────────

def _sanitize_for_tts(text: str) -> str:
    """
    Remove markdown formatting that TTS engines would read literally.
    Examples: **bold** → bold, *italic* → italic, `code` → code
    """
    # Remove bold: **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    # Remove italic: *text* or _text_ (single)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'\1', text)
    # Remove inline code: `text`
    text = re.sub(r'`(.+?)`', r'\1', text)
    # Remove strikethrough: ~~text~~
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    # Remove any remaining standalone asterisks or underscores
    text = re.sub(r'(?<!\w)\*+(?!\w)', '', text)
    text = re.sub(r'(?<!\w)_+(?!\w)', '', text)
    # Clean up any double spaces left behind
    text = re.sub(r'  +', ' ', text)
    return text.strip()


def _normalize_numbers(text: str) -> str:
    """
    Normalize currency and large numbers for TTS so they read naturally.
    ₹15000  ->  '15,000 rupees'   (NOT 'Rs. 15,000' which TTS reads as 'R S')
    ₹1,799  ->  '1,799 rupees'
    15000   ->  '15,000'          (bare numbers also get commas)
    """
    def _currency_replace(m):
        # Grab the number part, strip any existing commas, reformat with commas
        num_str = m.group(1).replace(',', '')
        try:
            formatted = "{:,}".format(int(num_str))
        except ValueError:
            formatted = num_str
        return f"{formatted} rupees"

    # Replace ₹NUMBER (with optional commas) → 'NUMBER rupees'
    text = re.sub(r'₹([\d,]+)', _currency_replace, text)

    # Add commas to any remaining bare 4+ digit numbers (no currency prefix)
    def _add_commas(m):
        num = m.group(0).replace(',', '')
        try:
            return "{:,}".format(int(num))
        except ValueError:
            return m.group(0)

    text = re.sub(r'\b\d{4,}\b', _add_commas, text)

    return text


def _post_process_vtt(vtt_path: str):
    """
    Restore '15,000 rupees' back to '₹15,000' in the final subtitle file.
    Because TTS engines spoke '15,000 rupees', Whisper/Edge-TTS wrote that in the VTT.
    We want the clean symbol format on screen.
    """
    if not os.path.exists(vtt_path):
        return
    with open(vtt_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Revert 'NUMBER rupees' back to '₹NUMBER' case-insensitively, handling internal spaces from Whisper
    import re as _re
    def _revert_currency(m):
        num_str = m.group(1).replace(' ', '')
        return f"₹{num_str}"
        
    text = _re.sub(r'\b([\d,\s]+)\s+rupees\b', _revert_currency, text, flags=_re.IGNORECASE)

    with open(vtt_path, "w", encoding="utf-8") as f:
        f.write(text)


# ── Public entry-point ────────────────────────────────────────────────────────

def generate_voiceover(script_text: str) -> bool:
    """
    Generate voiceover.mp3 + subtitles.vtt from script_text.
    Returns True on success, False on total failure.
    """
    if not script_text or len(script_text.strip()) < 10:
        print("❌ Script text is empty — cannot generate voiceover.")
        return False

    # Sanitize markdown formatting that TTS would read literally
    clean_text = _sanitize_for_tts(script_text)
    
    # Normalize currency for TTS engines so they don't read digits
    spoken_text = _normalize_numbers(clean_text)
    
    if spoken_text != clean_text:
        print("🧹 Normalized script text for TTS audio.")

    # ── 1. ElevenLabs (best: indistinguishable from human) ───────────────────
    if _try_elevenlabs(spoken_text):
        _generate_subtitles_from_audio("voiceover.mp3", clean_text)
        _post_process_vtt("subtitles.vtt")
        return True

    # ── 2. Kokoro TTS (offline, excellent quality) ───────────────────────────
    if _try_kokoro(spoken_text):
        _generate_subtitles_from_audio("voiceover.mp3", clean_text)
        _post_process_vtt("subtitles.vtt")
        return True

    # ── 3. edge-tts (may be blocked on GitHub Actions) ───────────────────────
    temp_file = "temp_script.txt"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(spoken_text)

    for attempt in range(1, 4):
        if _try_edge_tts(temp_file):
            if os.path.exists(temp_file):
                os.remove(temp_file)
            _post_process_vtt("subtitles.vtt")
            return True
        print(f"⚠️  edge-tts attempt {attempt} failed. Retrying in 3s...")
        time.sleep(3)

    if os.path.exists(temp_file):
        os.remove(temp_file)

    # ── 4. Final fallback: gTTS ───────────────────────────────────────────────
    print("🎙️ Falling back to gTTS...")
    if _try_gtts(spoken_text):
        _generate_subtitles_from_audio("voiceover.mp3", clean_text)
        _post_process_vtt("subtitles.vtt")
        return True

    return False


# ── ElevenLabs TTS ────────────────────────────────────────────────────────────

def _get_elevenlabs_key() -> str | None:
    """Get next ElevenLabs API key from rotation pool."""
    keys_raw = os.environ.get("ELEVENLABS_API_KEYS") or os.environ.get("ELEVENLABS_API_KEY", "")
    if not keys_raw:
        return None
    keys = [k.strip() for k in keys_raw.split(",") if k.strip()]
    if not keys:
        return None
    return random.choice(keys)


def _try_elevenlabs(script_text: str) -> bool:
    """
    ElevenLabs free tier: 10,000 characters/month per key.
    For quota management, supports multiple keys via ELEVENLABS_API_KEYS (comma-separated).
    Voice: Adam (voice_id = pNInz6obpgDQGcFmaJgB) — natural American male.
    Requires: ELEVENLABS_API_KEY or ELEVENLABS_API_KEYS env var.
    """
    if requests is None:
        print("⚠️  requests not installed — skipping ElevenLabs.")
        return False
    
    api_key = _get_elevenlabs_key()
    if not api_key:
        print("⚠️  ELEVENLABS_API_KEYS not set — skipping ElevenLabs.")
        return False

    print("🎙️ Generating voiceover with ElevenLabs (human-quality)...")

    # Adam voice — sounds like a real tech YouTuber
    VOICE_ID = "pNInz6obpgDQGcFmaJgB"

    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": script_text,
            "model_id": "eleven_turbo_v2",   # fastest, most credits-efficient
            "voice_settings": {
                "stability": 0.30,           # lower = more energetic/dynamic
                "similarity_boost": 0.82,    # high similarity to base voice
                "style": 0.50,               # higher expressiveness for punch
                "use_speaker_boost": True,
            },
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=60)

        if resp.status_code == 200:
            with open("voiceover.mp3", "wb") as f:
                f.write(resp.content)
            size_kb = os.path.getsize("voiceover.mp3") // 1024
            print(f"✅ ElevenLabs voiceover ready! ({size_kb} KB)")
            return True

        elif resp.status_code == 401:
            print("❌ ElevenLabs: invalid API key or key has leading/trailing whitespace.")
            _log_response_error(resp, "401 Unauthorized")
        elif resp.status_code == 429:
            print("⚠️  ElevenLabs: rate limited — falling back.")
        else:
            error_msg = _parse_response_error(resp)
            print(f"⚠️  ElevenLabs error {resp.status_code}: {error_msg}")

    except Exception as e:
        print(f"⚠️  ElevenLabs failed: {e}")

    return False


def _parse_response_error(resp) -> str:
    """Extract error message from ElevenLabs response with fallback handling."""
    try:
        data = resp.json()
        if isinstance(data, dict):
            # Try multiple error message paths
            error = (
                data.get("detail", {}).get("message") or
                data.get("message") or
                data.get("error") or
                str(data)[:200]
            )
            return error
    except Exception:
        pass
    return resp.text[:300]


def _log_response_error(resp, prefix: str = ""):
    """Log full response for debugging."""
    try:
        body = resp.json()
    except Exception:
        body = resp.text
    if prefix:
        print(f"   {prefix} response: {body}")





# ── Kokoro TTS ─────────────────────────────────────────────────────────────────

def _try_kokoro(script_text: str) -> bool:
    """
    Kokoro-82M: offline, open-source, extremely natural voice.
    Requires: pip install kokoro>=0.9.4 soundfile numpy
    Models auto-download on first use (~326 MB, cached after).
    """
    try:
        print("🎙️ Generating voiceover with Kokoro TTS (human-quality)...")
        from kokoro import KPipeline
        import soundfile as sf
        import numpy as np

        # af_heart = warm American female, very natural
        # am_adam  = natural American male
        # am_michael = slightly deeper American male
        voices = ["am_adam", "am_michael", "af_heart"]

        for voice in voices:
            try:
                pipeline = KPipeline(lang_code="a")  # 'a' = American English
                samples_list = []
                for _, _, audio in pipeline(script_text, voice=voice, speed=1.2):
                    # audio is a numpy float32 array at 24000 Hz
                    samples_list.append(audio)

                if not samples_list:
                    continue

                audio_data = np.concatenate(samples_list)
                # Save as WAV first, then convert to MP3 with ffmpeg
                sf.write("voiceover_raw.wav", audio_data, 24000)

                subprocess.run([
                    "ffmpeg", "-y", "-i", "voiceover_raw.wav",
                    "-codec:a", "libmp3lame", "-qscale:a", "2",
                    "voiceover.mp3"
                ], capture_output=True, timeout=60)

                if os.path.exists("voiceover.mp3") and os.path.getsize("voiceover.mp3") > 5000:
                    size_kb = os.path.getsize("voiceover.mp3") // 1024
                    print(f"✅ Kokoro voiceover ready! Voice: {voice} ({size_kb} KB)")
                    _rm("voiceover_raw.wav")
                    return True

            except Exception as ve:
                print(f"⚠️  Kokoro voice '{voice}' error: {ve}")
                continue

        return False

    except ImportError:
        print("⚠️  Kokoro not installed — skipping (will try edge-tts next).")
        return False
    except Exception as e:
        print(f"⚠️  Kokoro failed: {e}")
        return False


# ── Edge TTS ───────────────────────────────────────────────────────────────────

def _try_edge_tts(script_file: str) -> bool:
    """Run edge-tts and return True on success. Tries 3 voices in descending quality."""
    print("🎙️ Generating voiceover with edge-tts...")

    voice_options = [
        ("en-US-BrianNeural",       "+18%", "+2Hz"),
        ("en-US-ChristopherNeural", "+15%", "+0Hz"),
        ("en-US-GuyNeural",         "+15%", "+0Hz"),
    ]

    for voice, rate, pitch in voice_options:
        cmd = [
            "edge-tts",
            "--voice", voice,
            "--rate",  rate,
            "--pitch", pitch,
            "-f", script_file,
            "--write-media",     "voiceover.mp3",
            "--write-subtitles", "subtitles.vtt",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0 and os.path.exists("voiceover.mp3"):
                size_kb = os.path.getsize("voiceover.mp3") // 1024
                print(f"✅ edge-tts ready! Voice: {voice} ({size_kb} KB)")
                return True
            err = result.stderr.strip()[:200]
            print(f"⚠️  Voice {voice} failed: {err}")
        except FileNotFoundError:
            print("❌ edge-tts not installed.")
            return False
        except subprocess.TimeoutExpired:
            print(f"⏱️  edge-tts timed out for {voice}")
        except Exception as e:
            print(f"❌ edge-tts error ({voice}): {e}")

    return False


# ── gTTS fallback ──────────────────────────────────────────────────────────────

def _try_gtts(script_text: str) -> bool:
    """Last-resort fallback. Creates voiceover.mp3 without subtitles."""
    try:
        from gtts import gTTS
        print("🎙️ Generating voiceover with gTTS fallback...")
        tts = gTTS(text=script_text, lang="en", slow=False)
        tts.save("voiceover.mp3")
        size_kb = os.path.getsize("voiceover.mp3") // 1024
        print(f"✅ gTTS voiceover saved ({size_kb} KB).")
        return True
    except ImportError:
        print("❌ gTTS not installed.")
        return False
    except Exception as e:
        print(f"❌ gTTS failed: {e}")
        return False


# ── Whisper subtitle generation ────────────────────────────────────────────────

def _generate_subtitles_from_audio(audio_path: str, script_text: str) -> bool:
    """
    Use openai-whisper to transcribe the voiceover and produce a synced VTT.
    Falls back to a simple evenly-spaced VTT from the script if whisper fails.
    """
    if not os.path.exists(audio_path):
        return False

    # Try whisper
    try:
        print("📝 Generating synced subtitles with Whisper...")
        import whisper  # type: ignore
        model = whisper.load_model("base")
        result = model.transcribe(audio_path, task="transcribe", language="en",
                                  word_timestamps=True)
        _whisper_result_to_vtt(result, "subtitles.vtt")
        cue_count = _count_vtt_cues("subtitles.vtt")
        print(f"✅ Whisper subtitles: {cue_count} cues generated.")
        return True
    except ImportError:
        print("⚠️  openai-whisper not installed — using script-based VTT.")
    except Exception as e:
        print(f"⚠️  Whisper transcription failed ({e}) — using script-based VTT.")

    # Fallback: build VTT directly from the script text with uniform timing
    try:
        _script_to_vtt(audio_path, script_text, "subtitles.vtt")
        return True
    except Exception as e2:
        print(f"⚠️  Script-based VTT also failed: {e2}")
        return False


def _whisper_result_to_vtt(result: dict, out_path: str):
    """Convert a whisper transcription result (with word_timestamps) to WebVTT."""
    lines = ["WEBVTT\n"]
    idx = 1
    for seg in result.get("segments", []):
        words = seg.get("words", [])
        if not words:
            # fall back to segment-level
            s = seg["start"]
            e = seg["end"]
            text = seg["text"].strip()
            lines.append(f"{idx}\n{_vtt_time(s)} --> {_vtt_time(e)}\n{text}\n")
            idx += 1
            continue
        # 1–3 words per cue
        chunk: list = []
        chunk_start = words[0]["start"]
        for w in words:
            chunk.append(w["word"].strip())
            if len(chunk) >= 3:
                chunk_end = w["end"]
                lines.append(f"{idx}\n{_vtt_time(chunk_start)} --> {_vtt_time(chunk_end)}\n{' '.join(chunk)}\n")
                idx += 1
                chunk = []
                if words.index(w) + 1 < len(words):
                    chunk_start = words[words.index(w) + 1]["start"]
        if chunk:
            lines.append(f"{idx}\n{_vtt_time(chunk_start)} --> {_vtt_time(words[-1]['end'])}\n{' '.join(chunk)}\n")
            idx += 1

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _script_to_vtt(audio_path: str, text: str, out_path: str):
    """Build an evenly-spaced VTT from the script text alone (no audio alignment)."""
    duration = _get_audio_duration(audio_path) or 60.0
    words = text.split()
    if not words:
        return

    per_word = duration / len(words)
    lines = ["WEBVTT\n"]
    idx = 1
    i = 0
    while i < len(words):
        group = words[i:i + 3]
        t_start = i * per_word
        t_end   = min((i + len(group)) * per_word, duration)
        lines.append(f"{idx}\n{_vtt_time(t_start)} --> {_vtt_time(t_end)}\n{' '.join(group)}\n")
        idx += 1
        i += len(group)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✅ Script-based VTT: {idx - 1} cues written.")


def _vtt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def _get_audio_duration(path: str) -> float:
    try:
        r = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path
        ], capture_output=True, text=True, timeout=10)
        return float(r.stdout.strip())
    except Exception:
        return 60.0


def _count_vtt_cues(path: str) -> int:
    try:
        with open(path, encoding="utf-8") as f:
            return sum(1 for line in f if "-->" in line)
    except Exception:
        return 0


def _rm(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
