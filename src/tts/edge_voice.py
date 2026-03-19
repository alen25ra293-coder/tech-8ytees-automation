"""
Edge TTS Voiceover Generator
Uses Microsoft Edge TTS (edge-tts) — 100% free, high-quality, no API key needed.
Generates both the audio (MP3) and synced subtitles (VTT).
"""
import os
import time
import subprocess


def generate_voiceover(script_text: str) -> bool:
    """
    Generate voiceover + subtitles from script text.

    Uses edge-tts with an energetic male voice (+20% speed for viral pacing).
    Falls back to gTTS if edge-tts fails.

    Returns True on success, False on total failure.
    """
    if not script_text or len(script_text.strip()) < 10:
        print("❌ Script text is empty — cannot generate voiceover.")
        return False

    # Write to temp file to avoid command-line length limits on Windows
    temp_file = "temp_script.txt"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(script_text)

    success = _try_edge_tts(temp_file)

    # Clean up temp file
    if os.path.exists(temp_file):
        os.remove(temp_file)

    if success:
        return True

    # Fallback: gTTS (no subtitles, but keeps the pipeline running)
    print("🎙️ Falling back to gTTS...")
    return _try_gtts(script_text)


def _try_edge_tts(script_file: str) -> bool:
    """Run edge-tts and return True if it succeeds."""
    print("🎙️ Generating voiceover with edge-tts (fast & free)...")

    voice = "en-US-ChristopherNeural"   # Deep, energetic male voice
    rate  = "+20%"                       # Slightly faster — keeps viewers hooked

    cmd = [
        "edge-tts",
        "--voice", voice,
        "--rate",  rate,
        "-f", script_file,
        "--write-media",     "voiceover.mp3",
        "--write-subtitles", "subtitles.vtt",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and os.path.exists("voiceover.mp3"):
            size_kb = os.path.getsize("voiceover.mp3") // 1024
            print(f"✅ edge-tts voiceover and VTT subtitles generated successfully! ({size_kb} KB)")
            return True
        else:
            err = result.stderr.strip()[:200]
            print(f"❌ edge-tts failed: {err}")
            return False
    except FileNotFoundError:
        print("❌ edge-tts not found. Install with: pip install edge-tts")
        return False
    except subprocess.TimeoutExpired:
        print("❌ edge-tts timed out.")
        return False
    except Exception as e:
        print(f"❌ edge-tts error: {e}")
        return False


def _try_gtts(script_text: str) -> bool:
    """Fallback to gTTS (free, no subtitles generated)."""
    try:
        from gtts import gTTS
        print("🎙️ Generating voiceover with gTTS fallback...")
        tts = gTTS(text=script_text, lang="en", slow=False)
        tts.save("voiceover.mp3")
        size_kb = os.path.getsize("voiceover.mp3") // 1024
        print(f"✅ gTTS voiceover saved. ({size_kb} KB) Note: no subtitles with gTTS fallback.")
        return True
    except ImportError:
        print("❌ gTTS not installed. Run: pip install gTTS")
        return False
    except Exception as e:
        print(f"❌ gTTS failed: {e}")
        return False
