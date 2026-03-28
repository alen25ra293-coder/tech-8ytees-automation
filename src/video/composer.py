import random
import os
import re
import shutil
import subprocess


def create_video(title, video_clips, hook_line=""):
    """
    BUGS FIXED vs previous version:
    1. Subtitle alignment=5 (center) collided with CTA (also center).
       Fixed: alignment=2 (bottom-center), MarginV=200.
    2. fontfile='C:/Windows/Fonts/impact.ttf' broke on Linux/GitHub Actions.
       Fixed: fontfile removed entirely.
    3. pop_expr commas inside FFmpeg filter string broke parsing.
       Fixed: removed animation, clean fontsize=52.
    4. CTA was boring ("SUBSCRIBE FOR MORE").
       Fixed: rotated between 3 action CTAs.
    5. Title y=h/3 covered product area.
       Fixed: y=60 (very top edge).
    """
    print("🎞️ Assembling final video with FFmpeg...")

    if not os.path.exists("voiceover.mp3"):
        print("❌ Voiceover file not found.")
        return False

    try:
        # ── 0. Audio duration ────────────────────────────────────────────────
        r = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", "voiceover.mp3"
        ], capture_output=True, text=True, timeout=10)
        duration = float(r.stdout.strip())
        video_duration = duration + 0.8

        if duration <= 20:
            MAX_CLIP_DURATION = 2.0
        elif duration <= 25:
            MAX_CLIP_DURATION = 2.5
        else:
            MAX_CLIP_DURATION = 3.0

        print(f"⏱️  {duration:.1f}s audio → {video_duration:.1f}s | Clips: {MAX_CLIP_DURATION}s")

        # ── 1. Scale/crop clips ──────────────────────────────────────────────
        scaled_clips = []
        color_grade = (
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            "setsar=1,eq=contrast=1.15:brightness=0.02:saturation=1.2:gamma=0.95"
        )

        if video_clips:
            print(f"🎬 Processing {len(video_clips)} clips...")
            for i, clip in enumerate(video_clips):
                if not os.path.exists(clip):
                    continue
                out = f"scaled_{i}.mp4"
                res = subprocess.run([
                    "ffmpeg", "-y", "-i", clip,
                    "-t", str(MAX_CLIP_DURATION),
                    "-vf", color_grade,
                    "-pix_fmt", "yuv420p", "-r", "30",
                    "-c:v", "libx264", "-an", "-preset", "ultrafast", out
                ], capture_output=True, text=True)
                if res.returncode == 0 and os.path.exists(out):
                    scaled_clips.append(out)
                else:
                    res2 = subprocess.run([
                        "ffmpeg", "-y", "-i", clip,
                        "-t", str(MAX_CLIP_DURATION),
                        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
                        "-pix_fmt", "yuv420p", "-r", "30",
                        "-c:v", "libx264", "-an", "-preset", "ultrafast", out
                    ], capture_output=True, text=True)
                    if res2.returncode == 0 and os.path.exists(out):
                        scaled_clips.append(out)

        # ── 2. Concatenate background ────────────────────────────────────────
        bg = ""
        if scaled_clips:
            try:
                with open("clips.txt", "w") as f:
                    repeats = int(video_duration / (len(scaled_clips) * MAX_CLIP_DURATION)) + 3
                    for _ in range(repeats):
                        for c in scaled_clips:
                            abs_path = os.path.abspath(c).replace('\\', '/')
                            f.write(f"file '{abs_path}'\n")

                res = subprocess.run([
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", "clips.txt", "-c", "copy", "bg_looped.mp4"
                ], capture_output=True, text=True)

                if res.returncode == 0 and os.path.exists("bg_looped.mp4"):
                    bg = "bg_looped.mp4"
                else:
                    print(f"⚠️  Concat failed: {res.stderr[:200]}")
            except Exception as e:
                print(f"⚠️  Concat setup failed: {e}")

        # ── 3. Fallback background ───────────────────────────────────────────
        if not bg:
            print("🎬 Using dark fallback background...")
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", f"color=c=0x06091A:s=1080x1920:d={int(video_duration) + 2}",
                "-pix_fmt", "yuv420p", "-r", "30", "bg_looped.mp4"
            ], capture_output=True)
            bg = "bg_looped.mp4"

        # ── 4. Subtitles ─────────────────────────────────────────────────────
        ass_file = None
        if os.path.exists("subtitles.vtt"):
            try:
                _split_vtt_to_words("subtitles.vtt", "subtitles_words.vtt", max_words=2)
                _vtt_to_srt("subtitles_words.vtt", "subtitles.srt")
                ass_result = subprocess.run([
                    "ffmpeg", "-y", "-i", "subtitles.srt", "subtitles_raw.ass"
                ], capture_output=True, text=True, timeout=30)
                if ass_result.returncode == 0 and os.path.exists("subtitles_raw.ass"):
                    _style_ass("subtitles_raw.ass", "subtitles.ass")
                    ass_file = os.path.abspath("subtitles.ass")
                    print("✅ Subtitles ready")
            except Exception as sub_err:
                print(f"⚠️  Subtitle conversion failed: {sub_err}")

        # ── 5. Filter chain ──────────────────────────────────────────────────
        import platform
        import re as _re
        vf_parts = []

        def _fmt_nums(s: str) -> str:
            return _re.sub(r'\b(\d{1,3})(\d{3})\b', lambda m: m.group(1) + ',' + m.group(2), s)

        # 5a. Title — very top of screen, 3s, yellow with black border
        # FIX: no fontfile (was Windows path, broke on GitHub Actions Linux runner)
        # FIX: y=60 not y=h/3 — title was covering the product reveal
        # Strip emojis — FFmpeg drawtext cannot render them on Ubuntu (shows as □)
        raw_title = _fmt_nums(title).upper().replace("'", "").replace('"', '').replace(':', '-').replace('\\', '')
        raw_title = _re.sub(r'[^\x00-\x7F₹]', '', raw_title).strip()
        if len(raw_title) > 28:
            words = raw_title.split()
            truncated = ""
            for w in words:
                candidate = (truncated + " " + w).strip()
                if len(candidate) <= 28:
                    truncated = candidate
                else:
                    break
            safe_title = truncated or raw_title[:28]
        else:
            safe_title = raw_title

        if safe_title:
            title_overlay = (
                f"drawtext=text='{safe_title}':"
                f"fontsize=52:"
                f"fontcolor=yellow:"
                f"borderw=6:bordercolor=black:"
                f"box=1:boxcolor=black@0.8:boxborderw=14:"
                f"x=(w-text_w)/2:"
                f"y=60:"
                f"enable='between(t,0,3)'"
            )
            vf_parts.append(title_overlay)
            print(f"   🎨 Title: '{safe_title}' (0-3s, y=60)")

        # 5b. CTA — upper-third of screen, last 3s
        # FIX: moved from y=h/2 (center) to y=h*0.2 (upper-third)
        # Reason: center position collided with subtitles
        # FIX: better CTA text options (not just "subscribe")
        cta_text = random.choice(["SAVE THIS", "SUBSCRIBE FOR MORE ", "TAP SUBSCRIBE "])
        cta_start = max(duration - 3.0, duration * 0.75)
        cta_overlay = (
            f"drawtext=text='{cta_text}':"
            f"fontsize=68:"
            f"fontcolor=white:"
            f"borderw=8:bordercolor=black:"
            f"box=1:boxcolor=black@0.75:boxborderw=16:"
            f"x=(w-text_w)/2:"
            f"y=h*0.2:"
            f"enable='between(t,{cta_start:.2f},{duration:.2f})'"
        )
        vf_parts.append(cta_overlay)
        print(f"   🎨 CTA: '{cta_text}' (last 3s, upper-third)")

        # 5c. Subtitles — bottom-center
        # FIX: alignment=2 in ASS style means bottom-center
        # Zero collision with CTA which is now at upper-third
        if ass_file and os.path.exists(ass_file):
            esc = ass_file.replace("\\", "/")
            if platform.system() == "Windows" and len(esc) > 1 and esc[1] == ":":
                esc = esc[0] + "\\:" + esc[2:]
            vf_parts.append(f"ass='{esc}'")
            print("   📝 Subtitles: bottom-center (no collision)")

        vf_filter = ",".join(vf_parts) if vf_parts else None

        # ── 6. Audio ─────────────────────────────────────────────────────────
        main_cmd = ["ffmpeg", "-y", "-i", bg, "-i", "voiceover.mp3"]
        audio_inputs = []
        audio_input_idx = 2

        for candidate in ["assets/impact_sound.mp3", "assets/whoosh.mp3", "impact_sound.mp3"]:
            if os.path.exists(candidate):
                main_cmd.extend(["-i", candidate])
                audio_inputs.append(("impact", audio_input_idx, 0.35))
                audio_input_idx += 1
                print(f"   🔊 Impact: {candidate}")
                break

        for candidate in ["assets/bgm.mp3", "bgm.mp3", "bgm.wav", "bgm.m4a"]:
            if os.path.exists(candidate):
                main_cmd.extend(["-stream_loop", "-1", "-i", candidate])
                # BGM starts 0.5s after voiceover (adds energy kick)
                audio_inputs.append(("bgm", audio_input_idx, 0.15, 0.5))
                audio_input_idx += 1
                print(f"   🎵 BGM: {candidate} (starts at 0.5s)")
                break

        if audio_inputs:
            filter_parts = ["[1:a]volume=1.0[vo]"]
            mix_inputs = ["[vo]"]
            for item in audio_inputs:
                if len(item) == 4:
                    name, idx, vol, delay = item
                    # Add delay to BGM using adelay filter
                    delay_ms = int(delay * 1000)
                    filter_parts.append(f"[{idx}:a]volume={vol},adelay={delay_ms}|{delay_ms}[{name}]")
                else:
                    name, idx, vol = item
                    filter_parts.append(f"[{idx}:a]volume={vol}[{name}]")
                mix_inputs.append(f"[{name}]")
            mix_count = len(mix_inputs)
            filter_parts.append(
                f"{''.join(mix_inputs)}amix=inputs={mix_count}:duration=first[aout]"
            )
            af_filter = ";".join(filter_parts)
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

        print(f"🎬 Rendering ({video_duration:.1f}s)...")
        res = subprocess.run(main_cmd, capture_output=True, text=True, timeout=600)
        if res.returncode != 0:
            print(f"❌ Render failed:\n{res.stderr[-1000:]}")
            return False
        print("✅ output.mp4 ready")

        for f in scaled_clips + (video_clips or []):
            _rm(f)
        for f in ["clips.txt", "bg_looped.mp4", "subtitles_words.vtt",
                  "subtitles.srt", "subtitles_raw.ass", "subtitles.ass"]:
            _rm(f)

        return True

    except Exception as e:
        print(f"❌ Video assembly failed: {e}")
        import traceback
        traceback.print_exc()
        return False


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
                import re as _re
                line = _re.sub(r'([.,?!])([^\s])', r'\1 \2', line)
                line = line.replace(' ,', ',').replace(' .', '.')
                line = _re.sub(r'^[,.]\s*', '', line)
                text_lines.append(line.upper())

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
    print(f"   SRT: {idx - 1} cues")


def _style_ass(src: str, dst: str):
    """
    FIX: alignment=2 (bottom-center) instead of 5 (center).
    This is the key fix for subtitle/CTA collision.
    MarginV=200 keeps text above bottom UI chrome.
    """
    with open(src, "r", encoding="utf-8") as f:
        content = f.read()

    if "PlayResX" in content:
        content = re.sub(r"PlayResX:\s*\d+", "PlayResX: 1080", content)
    else:
        content = content.replace("[Script Info]", "[Script Info]\nPlayResX: 1080", 1)

    if "PlayResY" in content:
        content = re.sub(r"PlayResY:\s*\d+", "PlayResY: 1920", content)
    else:
        content = content.replace("PlayResX: 1080", "PlayResX: 1080\nPlayResY: 1920", 1)

    new_style = (
        "Style: Default,"
        "Impact,"
        "82,"               # Increased from 76 for better readability
        "&H0000FFFF,"       # Yellow text (BGR: 00 FF FF 00)
        "&H000000FF,"
        "&H00000000,"       # Black outline
        "&H90000000,"
        "-1,0,0,0,"         # Bold=-1 (enabled), Italic=0, Underline=0, StrikeOut=0
        "100,100,"
        "0,"
        "0,"
        "1,"
        "8,"                # Increased outline from 7 to 8 (thicker black border)
        "3,"
        "2,"                # alignment=2 = bottom-center (KEY FIX)
        "20,20,200,0"       # MarginV=200
    )

    if "Style: Default," in content:
        content = re.sub(r"Style: Default,.*", new_style, content)
    else:
        content += "\n" + new_style

    with open(dst, "w", encoding="utf-8") as f:
        f.write(content)


def _split_vtt_to_words(src: str, dst: str, max_words: int = 2):
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
        print(f"✅ Subtitles: {cue_index - 1} cues")
    except Exception as e:
        print(f"⚠️  VTT split failed ({e}) — using original.")
        shutil.copy(src, dst)


def _rm(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
