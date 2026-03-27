import random
import os
import re
import shutil
import subprocess


def create_video(title, video_clips, hook_line=""):
    """
    Composes final video optimized for retention:
    1. Dynamic clip duration based on video length (not fixed 2.5s)
    2. Title overlay: smaller, bottom-third, persists longer (not just 3s)
    3. Progress bar: thin bar at bottom — rewards viewers for watching
    4. CTA overlay: last 2 seconds
    5. Word-level subtitles (Impact font, yellow, bottom-third)
    6. Impact sound on first frame
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
        video_duration = duration + 0.8  # tight padding — don't pad too much

        # ── Dynamic clip duration ────────────────────────────────────────────
        # For shorter videos (under 20s): 2s cuts feel fast
        # For longer videos (25s+): 3s cuts give viewer time to process product
        if duration <= 20:
            MAX_CLIP_DURATION = 2.0
        elif duration <= 25:
            MAX_CLIP_DURATION = 2.5
        else:
            MAX_CLIP_DURATION = 3.0

        print(f"⏱️  Video: {duration:.1f}s audio → {video_duration:.1f}s total | Clip length: {MAX_CLIP_DURATION}s")

        # ── 1. Scale/crop + color grade each clip ────────────────────────────
        scaled_clips = []
        color_grade = (
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            "setsar=1,eq=contrast=1.15:brightness=0.02:saturation=1.2:gamma=0.95"
        )
        # Slightly reduced from original — over-saturated video looks cheap

        if video_clips:
            print(f"🎬 Standardizing {len(video_clips)} clips ({MAX_CLIP_DURATION}s each)...")
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

                print("🎬 Concatenating background...")
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
                    print("✅ Subtitles ready")
            except Exception as sub_err:
                print(f"⚠️  Subtitle conversion failed: {sub_err}")

        # ── 5. Build video filter chain ──────────────────────────────────────
        import platform
        import re as _re
        vf_parts = []

        def _fmt_nums(s: str) -> str:
            return _re.sub(r'\b(\d{1,3})(\d{3})\b', lambda m: m.group(1) + ',' + m.group(2), s)

        # ── 5a. Title overlay ─────────────────────────────────────────────────
        # CHANGED: Smaller font, bottom-third position (not top), stays for first 5s
        # Rationale: Top title blocks the product reveal in first frame.
        # Bottom-third keeps product visible while title still shows.
        raw_title = _fmt_nums(title).upper().replace("'", "").replace('"', '').replace(':', '-').replace('\\', '')
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
                f"fontsize=40:"           # Smaller than before (was 48)
                f"fontcolor=yellow:"      # Yellow for readability
                f"box=1:boxcolor=black@0.75:boxborderw=10:"
                f"x=(w-text_w)/2:"
                f"y=h-text_h-320:"        # Bottom-third (above subtitles area)
                f"enable='between(t,0,5)'"  # Stays 5s instead of 3s
            )
            vf_parts.append(title_overlay)
            print(f"   🎨 Title: '{safe_title}' (0-5s, bottom-third)")

        # ── 5b. Progress bar ──────────────────────────────────────────────────
        # Disabled: FFmpeg drawbox doesn't support dynamic width based on time
        # (would require timeline-based rendering which is complex)
        # Removed to fix render failures

        # ── 5c. CTA overlay: last 2 seconds ──────────────────────────────────
        cta_text = random.choice(["FOLLOW FOR MORE", "SAVE THIS"])
        cta_start = max(duration - 2.5, duration * 0.75)  # at least 75% through
        cta_overlay = (
            f"drawtext=text='{cta_text}':"
            f"fontsize=72:"
            f"fontcolor=yellow:"
            f"box=1:boxcolor=black@0.65:boxborderw=18:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"enable='between(t,{cta_start:.2f},{duration:.2f})'"
        )
        vf_parts.append(cta_overlay)
        print(f"   🎨 CTA: '{cta_text}' (last ~2.5s)")

        # ── 5d. Subtitle burn-in ──────────────────────────────────────────────
        if ass_file and os.path.exists(ass_file):
            esc = ass_file.replace("\\", "/")
            if platform.system() == "Windows" and len(esc) > 1 and esc[1] == ":":
                esc = esc[0] + "\\:" + esc[2:]
            vf_parts.append(f"ass='{esc}'")
            print("   📝 Subtitles: word-level, bottom-third")

        vf_filter = ",".join(vf_parts) if vf_parts else None

        # ── 6. Build audio mix ───────────────────────────────────────────────
        main_cmd = ["ffmpeg", "-y", "-i", bg, "-i", "voiceover.mp3"]
        audio_inputs = []

        impact_file = None
        for candidate in ["assets/impact_sound.mp3", "assets/whoosh.mp3", "assets/impact.mp3",
                          "impact_sound.mp3", "whoosh.mp3"]:
            if os.path.exists(candidate):
                impact_file = candidate
                break

        bgm_file = None
        for candidate in ["bgm.mp3", "bgm.wav", "bgm.m4a"]:
            if os.path.exists(candidate):
                bgm_file = candidate
                break

        audio_input_idx = 2

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

        if audio_inputs:
            filter_parts = ["[1:a]volume=1.0[vo]"]
            mix_inputs = ["[vo]"]
            for name, idx, vol in audio_inputs:
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
            print(f"❌ Render failed: {res.stderr[-800:]}")
            return False
        print(f"✅ output.mp4 ready ({video_duration:.1f}s)")

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


# ── VTT → SRT ────────────────────────────────────────────────────────────────

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


# ── Styled ASS subtitles ──────────────────────────────────────────────────────

def _style_ass(src: str, dst: str):
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
        "65,"
        "&H0000FFFF,"
        "&H000000FF,"
        "&H00000000,"
        "&H80000000,"
        "-1,0,0,0,"
        "100,100,"
        "0,"
        "0,"
        "1,"
        "8,"
        "4,"
        "2,"
        "20,20,320,0"   # MarginV=320 — slightly higher to avoid progress bar
    )

    if "Style: Default," in content:
        content = re.sub(r"Style: Default,.*", new_style, content)
    else:
        content += "\n" + new_style

    with open(dst, "w", encoding="utf-8") as f:
        f.write(content)


# ── VTT word-splitter ─────────────────────────────────────────────────────────

def _split_vtt_to_words(src: str, dst: str, max_words: int = 3):
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
        print(f"⚠️  VTT split failed ({e}) — using original.")
        shutil.copy(src, dst)


def _rm(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
