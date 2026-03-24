import os
import re
import shutil
import subprocess


def create_video(title, video_clips, hook_line=""):
    """
    Composes the final video optimized for <20% skip rate:
    1. Scales/crops background clips to 1080x1920, each trimmed to 3s max
    2. Concatenates into seamless background with constant visual change
    3. Burns bold title text overlay on first 3 seconds (bright yellow)
    4. Burns word-level subtitles (size 65, white + yellow keywords, bottom third above UI)
    5. Adds impact/whoosh sound on first frame for audio hook
    """
    print("🎞️ Assembling final video with FFmpeg...")

    if not os.path.exists("voiceover.mp3"):
        print("❌ Voiceover file not found.")
        return False

    try:
        # ── 0. Get audio duration ────────────────────────────────────────────
        r = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", "voiceover.mp3"
        ], capture_output=True, text=True, timeout=10)
        duration = float(r.stdout.strip())
        video_duration = duration + 1.0  # minimal padding

        MAX_CLIP_DURATION = 2.5  # seconds per clip — rapid visual change for 23-26s video

        # ── 1. Scale/crop each clip + trim to 2.5 seconds + color grade ────────
        scaled_clips = []
        color_grade = (
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            "setsar=1,eq=contrast=1.2:brightness=0.04:saturation=1.3:gamma=0.92"
        )

        if video_clips:
            print(f"🎬 Standardizing {len(video_clips)} clips (max {MAX_CLIP_DURATION}s each)...")
            for i, clip in enumerate(video_clips):
                if not os.path.exists(clip):
                    continue
                out = f"scaled_{i}.mp4"
                res = subprocess.run([
                    "ffmpeg", "-y",
                    "-i", clip,
                    "-t", str(MAX_CLIP_DURATION),  # trim to 3 seconds
                    "-vf", color_grade,
                    "-pix_fmt", "yuv420p", "-r", "30",
                    "-c:v", "libx264", "-an", "-preset", "ultrafast", out
                ], capture_output=True, text=True)
                if res.returncode == 0 and os.path.exists(out):
                    scaled_clips.append(out)
                else:
                    # Retry without color grade
                    res2 = subprocess.run([
                        "ffmpeg", "-y", "-i", clip,
                        "-t", str(MAX_CLIP_DURATION),
                        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
                        "-pix_fmt", "yuv420p", "-r", "30",
                        "-c:v", "libx264", "-an", "-preset", "ultrafast", out
                    ], capture_output=True, text=True)
                    if res2.returncode == 0 and os.path.exists(out):
                        scaled_clips.append(out)

        # ── 2. Concatenate background (loop to fill duration) ────────────────
        bg = ""
        if scaled_clips:
            try:
                with open("clips.txt", "w") as f:
                    # Each clip is ~3s. Need ceil(duration/3) + buffer clips.
                    repeats = int(video_duration / (len(scaled_clips) * MAX_CLIP_DURATION)) + 3
                    for _ in range(repeats):
                        for c in scaled_clips:
                            abs_path = os.path.abspath(c).replace('\\', '/')
                            f.write(f"file '{abs_path}'\n")

                print("🎬 Concatenating rapid-cut background...")
                res = subprocess.run([
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", "clips.txt", "-c", "copy", "bg_looped.mp4"
                ], capture_output=True, text=True)

                if res.returncode == 0 and os.path.exists("bg_looped.mp4"):
                    bg = "bg_looped.mp4"
                else:
                    print(f"⚠️ Concat failed: {res.stderr[:200]}")
            except Exception as e:
                print(f"⚠️ Concat setup failed: {e}")

        # ── 3. Fallback: solid dark background ───────────────────────────────
        if not bg:
            print("🎬 Using dark fallback background...")
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", f"color=c=0x06091A:s=1080x1920:d={int(video_duration) + 2}",
                "-pix_fmt", "yuv420p", "-r", "30", "bg_looped.mp4"
            ], capture_output=True)
            bg = "bg_looped.mp4"

        # ── 4. Convert VTT → word-level SRT → styled ASS ────────────────────
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
                    print(f"✅ Subtitle ASS ready")
            except Exception as sub_err:
                print(f"⚠️ Subtitle conversion failed: {sub_err}")

        # ── 5. Build video filter chain ──────────────────────────────────────
        import platform
        vf_parts = []

        # 5a. Title text overlay on first 3 seconds (bright yellow, bold)
        safe_title = title[:35].replace("'", "").replace('"', '').replace(':', ' ').replace('\\', '')
        if safe_title:
            # Use drawtext — available on all ffmpeg builds
            title_overlay = (
                f"drawtext=text='{safe_title}':"
                f"fontsize=65:"
                f"fontcolor=yellow:bordercolor=black:borderw=4:"
                f"x=(w-text_w)/2:y=250:"
                f"enable='between(t,0,3)'"
            )
            vf_parts.append(title_overlay)
            print("   🎨 Title overlay: first 3 seconds")

        # 5b. Subtitle burn-in
        if ass_file and os.path.exists(ass_file):
            esc = ass_file.replace("\\", "/")
            if platform.system() == "Windows" and len(esc) > 1 and esc[1] == ":":
                esc = esc[0] + "\\:" + esc[2:]
            vf_parts.append(f"ass='{esc}'")
            print("   📝 Subtitle burn-in: word-level, bottom-third")

        vf_filter = ",".join(vf_parts) if vf_parts else None

        # ── 5c. Subscribe Card (Stitch API or Pillow fallback) ───────────────
        subscribe_card = "subscribe_card.png"
        
        # Try Stitch first
        stitch_success = False
        try:
            from src.generators.stitch_client import generate_ui_image
            result = generate_ui_image(
                "A sleek, dark-mode glassmorphism UI card asking the viewer to Like, Share, and Subscribe to Tech 8ytees",
                subscribe_card
            )
            if result:
                stitch_success = True
                print("   ✅ Stitch subscribe card generated")
        except Exception as e:
            print(f"   ⚠️ Stitch subscribe card failed: {e}")
        
        # Fallback: Create simple Pillow subscribe card
        if not stitch_success:
            try:
                from PIL import Image, ImageDraw, ImageFont
                
                # Create 1080x800 card
                card = Image.new("RGBA", (1080, 800), (0, 0, 0, 0))
                draw = ImageDraw.Draw(card)
                
                # Dark background with transparency
                bg_box = Image.new("RGBA", (1000, 700), (15, 15, 35, 230))
                card.paste(bg_box, (40, 50), bg_box)
                
                # Add glow border
                border_color = (255, 200, 0, 255)  # Gold
                draw.rounded_rectangle([45, 55, 1035, 745], radius=20, outline=border_color, width=5)
                
                # Load fonts
                font_paths = [
                    "C:/Windows/Fonts/arialbd.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                ]
                
                def load_font_fallback(size: int):
                    for path in font_paths:
                        if os.path.exists(path):
                            try:
                                return ImageFont.truetype(path, size)
                            except:
                                continue
                    return ImageFont.load_default()
                
                font_large = load_font_fallback(80)
                font_medium = load_font_fallback(50)
                font_small = load_font_fallback(40)
                
                # Text content
                y_pos = 150
                
                # "LIKE" icon + text
                draw.text((540, y_pos), "👍", font=font_large, anchor="mm")
                draw.text((540, y_pos + 100), "LIKE", font=font_medium, fill=(255, 255, 255), anchor="mm")
                
                # "SHARE" icon + text
                draw.text((540, y_pos + 200), "📤", font=font_large, anchor="mm")
                draw.text((540, y_pos + 300), "SHARE", font=font_medium, fill=(255, 255, 255), anchor="mm")
                
                # "SUBSCRIBE" - emphasized
                draw.rounded_rectangle([200, y_pos + 380, 880, y_pos + 480], radius=15, fill=(255, 0, 0))
                draw.text((540, y_pos + 430), "SUBSCRIBE", font=font_medium, fill=(255, 255, 255), anchor="mm")
                
                # Channel name
                draw.text((540, y_pos + 540), "Tech 8ytees", font=font_small, fill=(255, 200, 0), anchor="mm")
                
                # Save
                card.save(subscribe_card, "PNG")
                print("   ✅ Fallback subscribe card created with Pillow")
            except Exception as e:
                print(f"   ⚠️ Could not create subscribe card: {e}")

        # ── 6. Build ffmpeg command and filters ──────────────────────────────
        main_cmd = ["ffmpeg", "-y", "-i", bg, "-i", "voiceover.mp3"]
        
        sub_card_idx = -1
        if os.path.exists(subscribe_card):
            main_cmd.extend(["-i", subscribe_card])
            sub_card_idx = 2

        audio_input_idx = 3 if sub_card_idx != -1 else 2
        audio_inputs = []

        impact_file = None
        for candidate in ["assets/impact_sound.mp3", "assets/whoosh.mp3", "assets/impact.mp3", "impact_sound.mp3", "whoosh.mp3"]:
            if os.path.exists(candidate):
                impact_file = candidate
                break

        bgm_file = None
        for candidate in ["bgm.mp3", "bgm.wav", "bgm.m4a"]:
            if os.path.exists(candidate):
                bgm_file = candidate
                break

        if impact_file:
            main_cmd.extend(["-i", impact_file])
            print(f"   🔊 Impact sound: {impact_file}")
            audio_inputs.append(("impact", audio_input_idx, 0.35))
            audio_input_idx += 1

        if bgm_file:
            main_cmd.extend(["-stream_loop", "-1", "-i", bgm_file])
            print(f"   🎵 Background music: {bgm_file}")
            audio_inputs.append(("bgm", audio_input_idx, 0.10))
            audio_input_idx += 1

        fc_parts = []
        final_v = "0:v"
        final_a = "1:a"

        # Video filters
        if sub_card_idx != -1:
            t_start = max(0, video_duration - 4)
            if vf_filter:
                fc_parts.append(f"[0:v]{vf_filter}[vbase]")
                in_v = "[vbase]"
            else:
                in_v = "0:v"
            fc_parts.append(f"[{sub_card_idx}:v]scale='min(iw,800)':-1[sub]")
            fc_parts.append(f"{in_v}[sub]overlay=(W-w)/2:(H-h)/2+250:enable='between(t,{t_start},999)'[vout]")
            final_v = "[vout]"
            print("   🪄 Subscribe Card will overlay in the last 4 seconds")
        elif vf_filter:
            fc_parts.append(f"[0:v]{vf_filter}[vout]")
            final_v = "[vout]"

        # Audio filters
        if audio_inputs:
            fc_parts.append(f"[1:a]volume=1.0[vo]")
            mix_inputs = ["[vo]"]
            for name, idx, vol in audio_inputs:
                fc_parts.append(f"[{idx}:a]volume={vol}[{name}]")
                mix_inputs.append(f"[{name}]")
            mix_count = len(mix_inputs)
            fc_parts.append(f"{''.join(mix_inputs)}amix=inputs={mix_count}:duration=first[aout]")
            final_a = "[aout]"

        if fc_parts:
            main_cmd.extend(["-filter_complex", ";".join(fc_parts)])

        main_cmd.extend(["-map", final_v, "-map", final_a])

        main_cmd.extend([
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac",
            "-t", str(video_duration),
            "-shortest",
            "output.mp4"
        ])

        print(f"🎬 Rendering final video ({video_duration:.1f}s target)...")
        res = subprocess.run(main_cmd, capture_output=True, text=True, timeout=600)
        if res.returncode != 0:
            print(f"❌ Render failed: {res.stderr[-800:]}")
            return False
        print(f"✅ Final video ready: output.mp4 ({video_duration:.1f}s)")

        # ── 7. Cleanup ───────────────────────────────────────────────────────
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


# ── Styled ASS subtitles (viral style) ───────────────────────────────────────
def _style_ass(src: str, dst: str):
    """
    Viral subtitle style:
    - Canvas: 1080x1920 (9:16)
    - Font: Impact Bold, size 65 (big, readable)
    - White text with thick black outline
    - Bottom third, above UI elements (MarginV=280)
    - Max 3 words at a time
    """
    with open(src, "r", encoding="utf-8") as f:
        content = f.read()

    # Force PlayRes to match 1080x1920
    if "PlayResX" in content:
        content = re.sub(r"PlayResX:\s*\d+", "PlayResX: 1080", content)
    else:
        content = content.replace("[Script Info]", "[Script Info]\nPlayResX: 1080", 1)

    if "PlayResY" in content:
        content = re.sub(r"PlayResY:\s*\d+", "PlayResY: 1920", content)
    else:
        content = content.replace("PlayResX: 1080", "PlayResX: 1080\nPlayResY: 1920", 1)

    # ASS style: Impact 65, white, thick black outline, bottom-third above UI
    new_style = (
        "Style: Default,"
        "Impact,"                # Bold, punchy font
        "65,"                    # Fontsize (large for mobile)
        "&H00FFFFFF,"            # PrimaryColour: White
        "&H000000FF,"            # SecondaryColour: Red (unused)
        "&H00000000,"            # OutlineColour: Black
        "&H80000000,"            # BackColour: 50% transparent shadow
        "-1,0,0,0,"              # Bold=Yes
        "100,100,"               # ScaleX, ScaleY
        "0,"                     # Spacing
        "0,"                     # Angle
        "1,"                     # BorderStyle: Outline + shadow
        "4,"                     # Outline thickness
        "2,"                     # Shadow distance
        "2,"                     # Alignment: Bottom-Centre
        "20,20,280,0"            # MarginL, MarginR, MarginV=280 (above UI), Encoding
    )

    if "Style: Default," in content:
        content = re.sub(r"Style: Default,.*", new_style, content)
    else:
        content += "\n" + new_style

    with open(dst, "w", encoding="utf-8") as f:
        f.write(content)


# ── VTT word-splitter ────────────────────────────────────────────────────────
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
                end = _parse_time(end_str)
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

        print(f"✅ Subtitles split: {cue_index - 1} word-level cues.")
    except Exception as e:
        print(f"⚠️ VTT split failed ({e}) — using original.")
        shutil.copy(src, dst)


def _rm(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
