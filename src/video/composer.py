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
        # Using eq + hue instead of complex curves for better FFmpeg compatibility
        color_grade = (
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            "setsar=1,eq=contrast=1.15:brightness=0.03:saturation=1.25:gamma=0.9"
        )

        if video_clips:
            print(f"🎬 Standardizing {len(video_clips)} background clips...")
            for i, clip in enumerate(video_clips):
                if not os.path.exists(clip):
                    continue
                out = f"scaled_{i}.mp4"
                res = subprocess.run([
                    "ffmpeg", "-y", "-i", clip, "-vf", color_grade,
                    "-r", "30", "-c:v", "libx264", "-an", "-preset", "ultrafast", out
                ], capture_output=True, text=True)
                if res.returncode == 0 and os.path.exists(out):
                    scaled_clips.append(out)
                else:
                    # Retry once WITHOUT any filters if it fails
                    print(f"   ⚠️ Filter failed on clip {i}, retrying without filter...")
                    res_retry = subprocess.run([
                        "ffmpeg", "-y", "-i", clip,
                        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
                        "-r", "30", "-c:v", "libx264", "-an", "-preset", "ultrafast", out
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

        main_cmd = ["ffmpeg", "-y", "-i", bg, "-i", "voiceover.mp3"]
        if ass_file and os.path.exists(ass_file):
            esc = ass_file.replace("\\", "/").replace(":", "\\:")
            main_cmd.extend(["-vf", f"ass='{esc}'"])
            print("   Subtitle burn-in: ASS (word-level, bottom-third)")
        else:
            print("   ⚠️ No subtitles available — rendering without.")

        main_cmd.extend([
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac",
            "-t", str(video_duration),
            "-shortest",
            "main_video.mp4"
        ])

        res = subprocess.run(main_cmd, capture_output=True, text=True, timeout=600)
        if res.returncode != 0:
            print(f"❌ Main render failed: {res.stderr[-800:]}")
            return False
        print("✅ Main video rendered.")

        # ── 5. End-card CTA slide (6 sec) ─────────────────────────────────
        print("🎬 Creating end-card CTA slide...")
        _create_end_card()

        # ── 6. Concat main + end-card ──────────────────────────────────────
        with open("final_concat.txt", "w") as f:
            f.write("file 'main_video.mp4'\n")
            if os.path.exists("end_card.mp4"):
                f.write("file 'end_card.mp4'\n")

        res2 = subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", "final_concat.txt", "-c", "copy", "output.mp4"
        ], capture_output=True, text=True, timeout=120)

        if res2.returncode != 0 or not os.path.exists("output.mp4"):
            os.rename("main_video.mp4", "output.mp4")
            print("⚠️  End-card concat failed — video saved without end-card.")
        else:
            total = video_duration + 6
            print(f"✅ Final video ready: output.mp4 ({total:.1f}s incl. 6s CTA)")

        # ── 7. Cleanup ───────────────────────────────────────────────────
        for f in scaled_clips + (video_clips or []):
            _rm(f)
        for f in ["clips.txt", "bg_looped.mp4", "main_video.mp4", "end_card.mp4",
                  "final_concat.txt", "subtitles_words.vtt", "subtitles.srt",
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
    Professional subtitle style:
    - Font: Liberation Sans Bold, size 55
    - White text with thin cyan outline (borderw=3)
    - Semi-transparent black box behind text
    - Bottom-third position (MarginV=300 from bottom)
    - Centered (Alignment=2)
    """
    with open(src, "r", encoding="utf-8") as f:
        content = f.read()

    # ASS colour format: &HAABBGGRR
    # White:              &H00FFFFFF
    # Cyan outline:       &H00FFFF00  (B=FF, G=FF, R=00)
    # Semi-transparent black box: &H88000000 (alpha=88)
    new_style = (
        "Style: Default,"
        "Liberation Sans,"  # Font (available on GitHub Actions)
        "55,"               # Fontsize — fits within 1080px width
        "&H00FFFFFF,"       # PrimaryColour: white text
        "&H000000FF,"       # SecondaryColour
        "&H88000000,"       # BackColour: semi-transparent black box
        "&H00FFFF00,"       # OutlineColour: cyan
        "-1,0,0,0,"         # Bold, Italic, Underline, Strikeout
        "100,100,"          # ScaleX, ScaleY
        "0,"                # Spacing
        "0,"                # Angle
        "3,"                # BorderStyle: 3 = opaque box behind text
        "3,"                # Outline: 3px cyan border
        "1,"                # Shadow
        "2,"                # Alignment: 2 = bottom centre
        "10,10,300,0"       # MarginL, MarginR, MarginV (300 = bottom third), Encoding
    )

    content = re.sub(r"^Style: Default,.*$", new_style, content, flags=re.MULTILINE)

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


# ── End-card CTA: animated colored buttons (NO emojis) ───────────────────────
def _create_end_card(duration: float = 6.0):
    """
    6-second end card with colored button blocks (no emojis — ffmpeg can't render them).
    Layout: dark background + 3 colored pill buttons (red/purple/orange) + text.
    Fade-in simulated via drawbox using expr for time-based alpha.
    """
    font = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    font2 = "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
    chosen_font = font if os.path.exists(font) else (font2 if os.path.exists(font2) else "")

    ff = f":fontfile={chosen_font}" if chosen_font else ""

    # Layout planned for 1080x1920:
    # Top: "BEFORE YOU LEAVE..." text ~y=340
    # Button 1 (red Subscribe):    y=500-640
    # Button 2 (purple Instagram): y=700-840
    # Button 3 (orange Like):      y=900-1040
    # Bottom: small watermark

    vf = (
        # Dark navy background
        "drawbox=x=0:y=0:w=1080:h=1920:color=0x06091A@1.0:t=fill,"
        # Subtle top accent line (white)
        "drawbox=x=80:y=60:w=920:h=4:color=0xFFFFFF@0.5:t=fill,"
        # Subtle bottom accent line
        "drawbox=x=80:y=1860:w=920:h=4:color=0xFFFFFF@0.5:t=fill,"

        # Header text
        f"drawtext=text='BEFORE YOU LEAVE...'{ff}:fontsize=58:"
        "fontcolor=0xCCCCCC:x=(w-text_w)/2:y=300:"
        "shadowcolor=black:shadowx=2:shadowy=2,"

        # ── Button 1: SUBSCRIBE (red box) ─────────────────────────────────
        "drawbox=x=80:y=460:w=920:h=150:color=0xCC0000@1.0:t=fill,"
        "drawbox=x=80:y=460:w=920:h=150:color=0xFF4444@1.0:t=2,"
        f"drawtext=text='SUBSCRIBE on YouTube'{ff}:fontsize=64:"
        "fontcolor=white:x=(w-text_w)/2:y=515:"
        "shadowcolor=0x880000:shadowx=3:shadowy=3,"

        # ── Button 2: FOLLOW (purple box) ─────────────────────────────────
        "drawbox=x=80:y=660:w=920:h=150:color=0x7B2FBE@1.0:t=fill,"
        "drawbox=x=80:y=660:w=920:h=150:color=0x9B4FDE@1.0:t=2,"
        f"drawtext=text='Follow @Tech8ytees on Instagram'{ff}:fontsize=52:"
        "fontcolor=white:x=(w-text_w)/2:y=717:"
        "shadowcolor=0x440088:shadowx=2:shadowy=2,"

        # ── Button 3: LIKE (orange/gold box) ──────────────────────────────
        "drawbox=x=80:y=860:w=920:h=150:color=0xC85000@1.0:t=fill,"
        "drawbox=x=80:y=860:w=920:h=150:color=0xFF7700@1.0:t=2,"
        f"drawtext=text='SMASH THE LIKE NOW'{ff}:fontsize=68:"
        "fontcolor=white:x=(w-text_w)/2:y=913:"
        "shadowcolor=0x882200:shadowx=3:shadowy=3,"

        # Sub-text below buttons
        f"drawtext=text='It only takes 0.5 seconds :)'{ff}:fontsize=44:"
        "fontcolor=0x888888:x=(w-text_w)/2:y=1055:"
        "shadowcolor=black:shadowx=1:shadowy=1,"

        # Channel watermark at bottom
        f"drawtext=text='@Tech8ytees'{ff}:fontsize=46:"
        "fontcolor=0xFF6600:x=(w-text_w)/2:y=1800:"
        "shadowcolor=black:shadowx=2:shadowy=2"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=black:size=1080x1920:rate=30:duration={duration}",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast",
        "-t", str(duration),
        "end_card.mp4"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if res.returncode != 0 or not os.path.exists("end_card.mp4"):
        print(f"⚠️ End card render failed — using simple fallback")
        # Simple solid-color fallback (no emojis, no complex filter)
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=0x06091A:size=1080x1920:rate=30:duration={duration}",
            "-vf", (
                f"drawbox=x=80:y=460:w=920:h=150:color=0xCC0000@1.0:t=fill,"
                f"drawtext=text='SUBSCRIBE':{f'fontfile={chosen_font}:' if chosen_font else ''}fontsize=80:fontcolor=white:x=(w-text_w)/2:y=515,"
                f"drawbox=x=80:y=660:w=920:h=150:color=0x7B2FBE@1.0:t=fill,"
                f"drawtext=text='FOLLOW':{f'fontfile={chosen_font}:' if chosen_font else ''}fontsize=80:fontcolor=white:x=(w-text_w)/2:y=717,"
                f"drawbox=x=80:y=860:w=920:h=150:color=0xC85000@1.0:t=fill,"
                f"drawtext=text='LIKE':{f'fontfile={chosen_font}:' if chosen_font else ''}fontsize=80:fontcolor=white:x=(w-text_w)/2:y=913"
            ),
            "-c:v", "libx264", "-preset", "fast",
            "-t", str(duration), "end_card.mp4"
        ], capture_output=True)

    if os.path.exists("end_card.mp4"):
        print("✅ End-card CTA created.")


def _rm(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
