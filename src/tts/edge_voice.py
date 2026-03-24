"""
Voiceover Generator — Tech 8ytees
Priority : ElevenLabs  (human-quality, free tier 10k chars/mo)
Fallback 1: Kokoro TTS  (offline, open-source, very natural)
Fallback 2: edge-tts    (Microsoft Neural voices, may fail on CI)
Fallback 3: gTTS        (last resort)
Subtitles  : openai-whisper → synced .vtt (word-level timestamps)
"""
import os
import random
import re
import time
import subprocess
import json
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont

# Optional imports for TTS engines (moved to top)
try:
    from kokoro import KPipeline
    import soundfile as sf
    import numpy as np
    _KOKORO_AVAILABLE = True
except ImportError:
    _KOKORO_AVAILABLE = False
    KPipeline = None
    sf = None
    np = None

try:
    from gtts import gTTS
    _GTTS_AVAILABLE = True
except ImportError:
    _GTTS_AVAILABLE = False
    gTTS = None

try:
    import whisper  # type: ignore
    _WHISPER_AVAILABLE = True
except ImportError:
    _WHISPER_AVAILABLE = False
    whisper = None


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
    # e.g., "**entire**" → "entire" (not "asterisk asterisk entire asterisk asterisk")
    clean_text = _sanitize_for_tts(script_text)
    if clean_text != script_text:
        print("🧹 Cleaned markdown from script text for TTS.")

    # ── 1. ElevenLabs (best: indistinguishable from human) ───────────────────
    if _try_elevenlabs(clean_text):
        _generate_subtitles_from_audio("voiceover.mp3", clean_text)
        return True

    # ── 2. Kokoro TTS (offline, excellent quality) ───────────────────────────
    if _try_kokoro(clean_text):
        _generate_subtitles_from_audio("voiceover.mp3", clean_text)
        return True

    # ── 3. edge-tts (may be blocked on GitHub Actions) ───────────────────────
    temp_file = "temp_script.txt"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(clean_text)

    for attempt in range(1, 4):
        if _try_edge_tts(temp_file):
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return True
        print(f"⚠️  edge-tts attempt {attempt} failed. Retrying in 3s...")
        time.sleep(3)

    # ── 4. Final fallback: gTTS ───────────────────────────────────────────────
    print("🎙️ Falling back to gTTS...")
    if _try_gtts(clean_text):
        if os.path.exists(temp_file):
            os.remove(temp_file)
        _generate_subtitles_from_audio("voiceover.mp3", clean_text)
        return True

    if os.path.exists(temp_file):
        os.remove(temp_file)

    return False


# ── ElevenLabs TTS ────────────────────────────────────────────────────────────

def _try_elevenlabs(script_text: str) -> bool:
    """
    ElevenLabs free tier: 10,000 characters/month.
    Voice: Adam (voice_id = pNInz6obpgDQGcFmaJgB) — natural American male.
    Requires: ELEVENLABS_API_KEY env var set in GitHub secrets.
    """
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        print("⚠️  ELEVENLABS_API_KEY not set — skipping ElevenLabs.")
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
            print("❌ ElevenLabs: invalid API key.")
        elif resp.status_code == 429:
            print("⚠️  ElevenLabs: quota exceeded — falling back.")
        else:
            try:
                err = resp.json().get("detail", {}).get("message", resp.text[:200])
            except Exception:
                err = resp.text[:200]
            print(f"⚠️  ElevenLabs error {resp.status_code}: {err}")

    except Exception as e:
        print(f"⚠️  ElevenLabs failed: {e}")

    return False




# ── Kokoro TTS ─────────────────────────────────────────────────────────────────

def _try_kokoro(script_text: str) -> bool:
    """
    Kokoro-82M: offline, open-source, extremely natural voice.
    Requires: pip install kokoro>=0.9.4 soundfile numpy
    Models auto-download on first use (~326 MB, cached after).
    """
    if not _KOKORO_AVAILABLE:
        print("⚠️  Kokoro not installed — skipping (will try edge-tts next).")
        return False

    try:
        print("🎙️ Generating voiceover with Kokoro TTS (human-quality)...")

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

    except Exception as e:
        print(f"⚠️  Kokoro failed: {e}")
        return False


# ── Edge TTS ───────────────────────────────────────────────────────────────────

def get_random_voice() -> tuple[str, str, str]:
    """Returns a random energetic energetic voice with slightly randomized rate/pitch."""
    voices = [
        # US Voices
        "en-US-BrianNeural",
        "en-US-ChristopherNeural",
        "en-US-GuyNeural",
        "en-US-EricNeural",
        "en-US-SteffanNeural",
        # AU/UK Voices (often sound more sophisticated/authoritative)
        "en-AU-WilliamNeural",
        "en-GB-RyanNeural",
        "en-GB-ThomasNeural",
    ]
    voice = random.choice(voices)
    
    # Randomize rate/pitch slightly (approx ±3%)
    rate_val = 18 + random.randint(-4, 4)
    pitch_val = random.randint(-2, 2)
    
    return voice, f"+{rate_val}%", f"{pitch_val}Hz"


def _try_edge_tts(script_file: str) -> bool:
    """Run edge-tts and return True on success. Randomizes voice for variety."""
    voice, rate, pitch = get_random_voice()
    print(f"🎙️ Generating voiceover with edge-tts (Voice: {voice})...")

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
            print(f"✅ edge-tts ready! ({size_kb} KB)")
            return True
        
        # Fallback to a safe voice if random one fails
        print(f"⚠️  Voice {voice} failed, trying safe fallback...")
        cmd[2] = "en-US-BrianNeural"
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ edge-tts failed: {e}")
        return False


# ── gTTS fallback ──────────────────────────────────────────────────────────────

def _try_gtts(script_text: str) -> bool:
    """Run gTTS (Google TTS) as a last-resort fallback."""
    if not _GTTS_AVAILABLE:
        print("⚠️  gTTS not installed — skipping.")
        return False

    print("🎙️ Generating voiceover with gTTS (Fallback)...")
    try:
        tts = gTTS(text=script_text, lang="en", tld="com")
        tts.save("voiceover.mp3")
        
        # Create a dummy subtitles file for gTTS if it doesn't exist
        if not os.path.exists("subtitles.vtt"):
            with open("subtitles.vtt", "w") as f:
                f.write("WEBVTT\n\n00:00:00.000 --> 00:00:10.000\n(Voiceover)")
        return True
    except Exception as e:
        print(f"❌ gTTS error: {e}")
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
