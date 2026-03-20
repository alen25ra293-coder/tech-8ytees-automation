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

    Uses edge-tts with a warm, natural-sounding voice at human pacing.
    Falls back to gTTS if edge-tts fails (3 attempts with retry).

    Returns True on success, False on total failure.
    """
    if not script_text or len(script_text.strip()) < 10:
        print("❌ Script text is empty — cannot generate voiceover.")
        return False

    # Write to temp file to avoid command-line length limits on Windows
    temp_file = "temp_script.txt"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(script_text)

    success = False
    for attempt in range(1, 4):
        if _try_edge_tts(temp_file):
            success = True
            break
        print(f"⚠️  edge-tts attempt {attempt} failed. Retrying in 3s...")
        time.sleep(3)

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
    print("🎙️ Generating voiceover with edge-tts...")

    # Voice hierarchy — try most natural first, fall back if unavailable
    voice_options = [
        # BrianNeural — newest, warmest, most human-sounding (2024)
        ("en-US-BrianNeural",      "+8%",  "+2Hz"),
        # ChristopherNeural — deep, energetic, good fallback
        ("en-US-ChristopherNeural", "+5%", "+0Hz"),
        # GuyNeural — natural casual American voice
        ("en-US-GuyNeural",        "+5%",  "+0Hz"),
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
                print(f"✅ Voiceover ready! Voice: {voice}, Rate: {rate}, Pitch: {pitch} ({size_kb} KB)")
                return True
            else:
                err = result.stderr.strip()[:200]
                print(f"⚠️  Voice {voice} failed: {err}")
                # Try next voice
                continue
        except FileNotFoundError:
            print("❌ edge-tts not found. Install with: pip install edge-tts")
            return False
        except subprocess.TimeoutExpired:
            print(f"❌ edge-tts timed out for voice {voice}.")
            continue
        except Exception as e:
            print(f"❌ edge-tts error with {voice}: {e}")
            continue

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
