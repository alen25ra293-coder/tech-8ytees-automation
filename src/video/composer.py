import os
import re
import shutil
import subprocess


def create_video(title, video_clips):
    """
    Composes the final video:
    1. Scales/crops background clips to 1080x1920, applies cool blue color grade
    2. Concatenates into background loop
    3. Burns word-level subtitles (bottom-third, white+cyan outline, size 55)
    4. Appends 6-second animated colored-button end-card CTA
    """
    print("🎞️ Assembling final video with FFmpeg...")

    if not os.path.exists("voiceover.mp3"):
        print("❌ Voiceover file not found.")
        return False

    try:
        # ── 0. Get duration ──────────────────────────────────────────────────
        r = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", "voiceover.mp3"
        ], capture_output=True, text=True, timeout=10)
        duration = float(r.stdout.strip())
        video_duration = duration + 1.5

        # ── 1. Scale/crop each clip + color grade ─────────────────────────────
        scaled_clips = []
        # Punchy tech color grade: boosts contrast + saturation + subtle blue tint
        color_grade = (
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            "setsar=1,eq=contrast=1.2:brightness=0.04:saturation=1.3:gamma=0.92"
        )
        # Extra visual impact filter for the FIRST clip only
        # Fast zoom-in from 1.05x to 1.0x over 0.5s — creates kinetic energy
        first_clip_grade = (
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,"
            "zoompan=z='if(lt(t,0.5),1.05-0.05*t*2,1)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:fps=30,"
            "eq=contrast=1.2:brightness=0.04:saturation=1.3:gamma=0.92"
        )

        if video_clips:
            print(f"🎬 Standardizing {len(video_clips)} background clips...")
            for i, clip in enumerate(video_clips):
                if not os.path.exists(clip):
                    continue
                out = f"scaled_{i}.mp4"
                # First clip gets explosive zoom-in for instant visual impact
                vf = first_clip_grade if i == 0 else color_grade
                res = subprocess.run([
                    "ffmpeg", "-y", "-i", clip, "-vf", vf,
                    "-pix_fmt", "yuv420p", "-r", "30", "-c:v", "libx264", "-an", "-preset", "ultrafast", out
                ], capture_output=True, text=True)
                if res.returncode == 0 and os.path.exists(out):
                    scaled_clips.append(out)
                else:
                    # Retry once WITHOUT any filters if it fails
                    print(f"   ⚠️ Filter failed on clip {i}, retrying without filter...")
                    res_retry = subprocess.run([
                        "ffmpeg", "-y", "-i", clip,
                        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
                        "-pix_fmt", "yuv420p", "-r", "30", "-c:v", "libx264", "-an", "-preset", "ultrafast", out
                    ], capture_output=True, text=True)
                    
                    if res_retry.returncode == 0 and os.path.exists(out):
                        scaled_clips.append(out)
                        print(f"   ✅ Clip {i} recovered (no filter).")
                    else:
                        err_msg = res_retry.stderr[-500:] if res_retry.stderr else "Unknown error"
                        print(f"⚠️ Failed to standardize clip {i} even without filter: {err_msg}")

        # ── 2. Concatenate background ──────────────────────────────────────────
        bg = ""
        if scaled_clips:
            try:
                with open("clips.txt", "w") as f:
                    # Fill duration + buffer
                    repeats = int(video_duration / (len(scaled_clips) * 2)) + 2
                    for _ in range(repeats):
                        for c in scaled_clips:
                            # Use absolute paths for concat safety
                            abs_path = os.path.abspath(c).replace('\\', '/')
                            f.write(f"file '{abs_path}'\n")
                
                print("🎬 Concatenating background...")
                res = subprocess.run([
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", "clips.txt", "-c", "copy", "bg_looped.mp4"
                ], capture_output=True, text=True)
                
                if res.returncode == 0 and os.path.exists("bg_looped.mp4"):
                    bg = "bg_looped.mp4"
                else:
                    print(f"⚠️ Concatenation failed: {res.stderr[:200]}")
            except Exception as e:
                print(f"⚠️ Concat setup failed: {e}")

        # ── 3. Fallback: Solid color if no background produced ──────────────────
        if not bg:
            print("🎬 Using dark fallback background...")
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", f"color=c=0x06091A:s=1080x1920:d={int(video_duration)+2}",
                "-pix_fmt", "yuv420p", "-r", "30", "bg_looped.mp4"
            ], capture_output=True)
            bg = "bg_looped.mp4"

        # ── 3a. Convert VTT → word-level SRT → ASS (reliable burn-in) ───────────
        ass_file = None
        if os.path.exists("subtitles.vtt"):
            try:
                _split_vtt_to_words("subtitles.vtt", "subtitles_words.vtt", max_words=3)
                _vtt_to_srt("subtitles_words.vtt", "subtitles.srt")
                ass_result = subprocess.run([
                    "ffmpeg", "-y", "-i", "subtitles.srt", "subtitles_raw.ass"
                ], capture_output=True, text=True, timeout=30)
                if ass_result.returncode == 0 and os.path.exists("subtitles_raw.ass"):
                    _style_ass("subtitles_raw.ass", "subtitles.ass")
                    ass_file = os.path.abspath("subtitles.ass")
                    print(f"✅ Subtitle ASS ready ({ass_file})")
            except Exception as sub_err:
                print(f"⚠️ Subtitle conversion failed: {sub_err}")

        # ── 4. Main Render ──────────────────────────────────────────────────────
        print(f"🎬 Rendering main video (Source: {bg})...")

        # Check for optional background music
        bgm_file = None
        for candidate in ["bgm.mp3", "bgm.wav", "bgm.m4a"]:
            if os.path.exists(candidate):
                bgm_file = candidate
                break

        # Build FFmpeg command with subtitle + optional BGM
        import platform
        main_cmd = ["ffmpeg", "-y", "-i", bg, "-i", "voiceover.mp3"]

        if bgm_file:
            # Loop BGM to fill the whole duration
            main_cmd.extend(["-stream_loop", "-1", "-i", bgm_file])
            print(f"   🎵 Background music detected: {bgm_file}")

        # --- Video filter (subtitles) ---
        vf_filter = None
        if ass_file and os.path.exists(ass_file):
            esc = ass_file.replace("\\", "/")
            if platform.system() == "Windows" and len(esc) > 1 and esc[1] == ":":
                esc = esc[0] + "\\:" + esc[2:]
            vf_filter = f"ass='{esc}'"
            print("   Subtitle burn-in: ASS (word-level, bottom-third)")
        else:
            print("   ⚠️ No subtitles available — rendering without.")

        # --- Audio filter (mix voiceover + optional BGM) ---
        if bgm_file:
            # Mix voiceover (input 1) at full volume with BGM (input 2) at 12%
            af_filter = "[1:a]volume=1.0[vo];[2:a]volume=0.12[bg];[vo][bg]amix=inputs=2:duration=first[aout]"
            if vf_filter:
                main_cmd.extend(["-vf", vf_filter])
            main_cmd.extend(["-filter_complex", af_filter, "-map", "0:v", "-map", "[aout]"])
        else:
            if vf_filter:
                main_cmd.extend(["-vf", vf_filter])
            main_cmd.extend(["-map", "0:v", "-map", "1:a"])

        main_cmd.extend([
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac",
            "-t", str(video_duration),
            "-shortest",
            "output.mp4"
        ])

        res = subprocess.run(main_cmd, capture_output=True, text=True, timeout=600)
        if res.returncode != 0:
            print(f"❌ Main render failed: {res.stderr[-800:]}")
            return False
        print(f"✅ Final video ready: output.mp4 ({video_duration:.1f}s)")

        # ── 5. Cleanup ───────────────────────────────────────────────────
        for f in scaled_clips + (video_clips or []):
            _rm(f)
        for f in ["clips.txt", "bg_looped.mp4",
                  "subtitles_words.vtt", "subtitles.srt",
                  "subtitles_raw.ass", "subtitles.ass"]:
            _rm(f)

        return True

    except Exception as e:
        print(f"❌ Video assembly failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# ── VTT → SRT converter ─────────────────────────────────────────────────────
def _vtt_to_srt(vtt_path: str, srt_path: str):
    """Convert WebVTT to SRT (simpler, more compatible)."""
    with open(vtt_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r"\n{2,}", content.strip())
    srt_lines = []
    idx = 1

    for block in blocks:
        lines = block.strip().splitlines()
        ts_line = None
        text_lines = []
        for line in lines:
            if "-->" in line:
                ts_line = line
            elif line and not line.startswith("WEBVTT") and not line.isdigit() and not line.startswith("NOTE"):
                text_lines.append(line)

        if not ts_line or not text_lines:
            continue

        parts = ts_line.strip().split(" --> ")
        def _fix_ts(t):
            t = t.strip().replace(".", ",")
            if t.count(":") == 1:
                t = "00:" + t
            return t

        ts_srt = f"{_fix_ts(parts[0])} --> {_fix_ts(parts[1])}"
        srt_lines.append(str(idx))
        srt_lines.append(ts_srt)
        srt_lines.extend(text_lines)
        srt_lines.append("")
        idx += 1

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))

    print(f"   SRT written: {idx - 1} cues")


# ── Inject professional subtitle style into ASS ───────────────────────────────
def _style_ass(src: str, dst: str):
    """
    Viral-style subtitles (MrBeast / Ali Abdaal):
    - Canvas forced to 1080×1920 (9:16 vertical video)
    - Font: Impact Bold, size 58
    - White text with thick black outline (BorderStyle=1, Outline=4)
    - Bottom-third, centred (Alignment=2, MarginV=120)
    """
    with open(src, "r", encoding="utf-8") as f:
        content = f.read()

    # ── FIX: Force PlayRes to match our 1080×1920 video ──────────────────
    # FFmpeg's SRT→ASS default is 384×288 — all margins/sizes are relative
    # to PlayRes, so without this fix text is pushed off-screen.
    if "PlayResX" in content:
        content = re.sub(r"PlayResX:\s*\d+", "PlayResX: 1080", content)
    else:
        content = content.replace("[Script Info]", "[Script Info]\nPlayResX: 1080", 1)

    if "PlayResY" in content:
        content = re.sub(r"PlayResY:\s*\d+", "PlayResY: 1920", content)
    else:
        content = content.replace("PlayResX: 1080", "PlayResX: 1080\nPlayResY: 1920", 1)

    # ASS colour format: &HAABBGGRR
    # V4+ field order: Name, Fontname, Fontsize, Primary, Secondary, Outline, Back,
    #                  Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY,
    #                  Spacing, Angle, BorderStyle, Outline, Shadow,
    #                  Alignment, MarginL, MarginR, MarginV, Encoding
    new_style = (
        "Style: Default,"
        "Impact,"               # Font — bold, punchy, available everywhere
        "58,"                   # Fontsize (relative to PlayRes 1920)
        "&H00FFFFFF,"           # PrimaryColour: White
        "&H000000FF,"           # SecondaryColour: Red (unused)
        "&H00000000,"           # OutlineColour: Black (max contrast)
        "&H80000000,"           # BackColour: 50% transparent black shadow
        "-1,0,0,0,"             # Bold=Yes, Italic/Underline/Strike=No
        "100,100,"              # ScaleX, ScaleY
        "0,"                    # Spacing
        "0,"                    # Angle
        "1,"                    # BorderStyle: 1 = Outline + drop shadow
        "4,"                    # Outline thickness (thick for readability)
        "2,"                    # Shadow distance
        "2,"                    # Alignment: 2 = Bottom-Centre
        "20,20,120,0"           # MarginL, MarginR, MarginV=120px, Encoding
    )

    # Replace existing Default style
    if "Style: Default," in content:
        content = re.sub(r"Style: Default,.*", new_style, content)
    else:
        content += "\n" + new_style

    with open(dst, "w", encoding="utf-8") as f:
        f.write(content)


# ── VTT word-splitter: MrBeast style ─────────────────────────────────────────
def _split_vtt_to_words(src: str, dst: str, max_words: int = 3):
    """Re-chunk VTT so each cue contains at most max_words words."""
    try:
        with open(src, "r", encoding="utf-8") as f:
            content = f.read()

        cue_blocks = re.split(r"\n{2,}", content.strip())
        new_cues: list = ["WEBVTT\n"]
        cue_index = 1

        def _parse_time(t: str) -> float:
            parts = t.strip().split(":")
            if len(parts) == 3:
                h, m, s = parts
                return int(h) * 3600 + int(m) * 60 + float(s.replace(",", "."))
            elif len(parts) == 2:
                m, s = parts
                return int(m) * 60 + float(s.replace(",", "."))
            return 0.0

        def _fmt_time(t: float) -> str:
            h = int(t // 3600)
            m = int((t % 3600) // 60)
            s = t % 60
            return f"{h:02d}:{m:02d}:{s:06.3f}"

        for block in cue_blocks:
            lines = block.strip().splitlines()
            ts_line = None
            text_lines = []
            for line in lines:
                if "-->" in line:
                    ts_line = line
                elif line and not line.startswith("WEBVTT") and not line.isdigit():
                    text_lines.append(line)

            if not ts_line:
                continue

            try:
                start_str, end_str = ts_line.split("-->")
                start = _parse_time(start_str)
                end   = _parse_time(end_str)
            except Exception:
                continue

            text = " ".join(text_lines).strip()
            words = text.split()
            if not words:
                continue

            total_dur = end - start
            per_word_dur = total_dur / max(1, len(words))
            groups = [words[i:i + max_words] for i in range(0, len(words), max_words)]
            cur_t = start

            for group in groups:
                group_dur = len(group) * per_word_dur
                g_end = min(cur_t + group_dur, end)
                new_cues.append(
                    f"{cue_index}\n"
                    f"{_fmt_time(cur_t)} --> {_fmt_time(g_end)}\n"
                    f"{' '.join(group)}\n"
                )
                cue_index += 1
                cur_t = g_end

        with open(dst, "w", encoding="utf-8") as f:
            f.write("\n".join(new_cues))

        print(f"✅ Subtitle split into {cue_index - 1} word-level cues.")
    except Exception as e:
        print(f"⚠️  VTT split failed ({e}) — using original subtitles.")
        shutil.copy(src, dst)


def _rm(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
