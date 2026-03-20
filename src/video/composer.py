import os
import re
import subprocess


def create_video(title, video_clips):
    """
    Composes the final video:
    1. Scales/crops background clips to 1080x1920
    2. Concatenates into background loop
    3. Burns 1-3 word-at-a-time subtitles (MrBeast style) + voiceover
    4. Appends 4-second irresistible end-card CTA
    """
    print("🎞️ Assembling final video with FFmpeg...")

    if not os.path.exists("voiceover.mp3"):
        print("❌ Voiceover file not found.")
        return False

    try:
        # ── Duration ───────────────────────────────────────────────────────
        r = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            "voiceover.mp3"
        ], capture_output=True, text=True, timeout=10)

        duration = float(r.stdout.strip())
        video_duration = duration + 1.5

        # ── 1. Scale/crop each clip ────────────────────────────────────────
        scaled_clips = []
        if video_clips:
            print(f"🎬 Standardizing {len(video_clips)} background clips...")
            for i, clip in enumerate(video_clips):
                if not os.path.exists(clip):
                    continue
                out = f"scaled_{i}.mp4"
                subprocess.run([
                    "ffmpeg", "-y", "-i", clip,
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                    "-r", "30", "-c:v", "libx264", "-an", "-preset", "ultrafast", out
                ], capture_output=True)
                scaled_clips.append(out)

        # ── 2. Concatenate background ──────────────────────────────────────
        if scaled_clips:
            with open("clips.txt", "w") as f:
                repeats = int(video_duration / (len(scaled_clips) * 5)) + 2
                for _ in range(repeats):
                    for c in scaled_clips:
                        f.write(f"file '{c}'\n")
            print("🎬 Concatenating background...")
            subprocess.run([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", "clips.txt", "-c", "copy", "bg_looped.mp4"
            ], capture_output=True)
            bg = "bg_looped.mp4"
        else:
            print("⚠️ No clips — using dark fallback.")
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi",
                "-i", f"color=c=0x0A0A19:size=1080x1920:duration={video_duration}",
                "-c:v", "libx264", "-preset", "ultrafast", "bg_looped.mp4"
            ], capture_output=True)
            bg = "bg_looped.mp4"

        # ── 3. Post-process VTT: 1-3 words per cue (MrBeast style) ─────────
        if os.path.exists("subtitles.vtt"):
            _split_vtt_to_words("subtitles.vtt", "subtitles_words.vtt", max_words=3)
            sub_file = "subtitles_words.vtt"
        else:
            sub_file = None

        # ── 4. Final render: video + audio + subtitles ─────────────────────
        print("🎬 Rendering main video with word-level subtitles...")

        # Bold centred style — black box for readability
        sub_style = (
            "Fontname=Impact,"
            "Fontsize=115,"
            "PrimaryColour=&H00FFFF,"
            "BackColour=&H99000000,"
            "BorderStyle=3,"
            "Outline=3,"
            "Shadow=2,"
            "Alignment=2,"
            "MarginV=870"
        )

        main_cmd = ["ffmpeg", "-y", "-i", bg, "-i", "voiceover.mp3"]
        if sub_file and os.path.exists(sub_file):
            # ffmpeg subtitles filter REQUIRES absolute path on Linux (GitHub Actions)
            abs_sub = os.path.abspath(sub_file).replace("\\", "/").replace(":", "\\:")
            main_cmd.extend(["-vf", f"subtitles='{abs_sub}':force_style='{sub_style}'"])
        main_cmd.extend([
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac",
            "-t", str(video_duration),
            "-shortest",
            "main_video.mp4"
        ])

        res = subprocess.run(main_cmd, capture_output=True, text=True, timeout=600)
        if res.returncode != 0:
            print(f"❌ Main render failed: {res.stderr[-600:]}")
            return False
        print("✅ Main video rendered.")

        # ── 5. End-card CTA slide (4 sec) ─────────────────────────────────
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
            # Fallback: just rename main video
            os.rename("main_video.mp4", "output.mp4")
            print("⚠️  End-card concat failed — video saved without end-card.")
        else:
            total = video_duration + 4
            print(f"✅ Final video ready: output.mp4 ({total:.1f}s incl. 4s CTA)")

        # ── 7. Cleanup ────────────────────────────────────────────────────
        for f in scaled_clips + (video_clips or []):
            _rm(f)
        for f in ["clips.txt", "bg_looped.mp4", "main_video.mp4",
                  "end_card.mp4", "final_concat.txt",
                  "subtitles_words.vtt"]:
            _rm(f)

        return True

    except Exception as e:
        print(f"❌ Video assembly failed: {e}")
        return False


# ── VTT word-splitter: MrBeast style ─────────────────────────────────────────
def _split_vtt_to_words(src: str, dst: str, max_words: int = 3):
    """
    Re-chunk a VTT subtitle file so each cue contains at most `max_words` words.
    This gives the single-word-at-a-time effect that boosts watch time by 15-40%.
    """
    try:
        with open(src, "r", encoding="utf-8") as f:
            content = f.read()

        cue_blocks = re.split(r"\n{2,}", content.strip())
        new_cues: list[str] = ["WEBVTT\n"]
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
            # Find timestamp line
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

            # Split text into groups of max_words
            total_dur = end - start
            n_groups  = max(1, len(words))
            per_word_dur = total_dur / n_groups

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
        import shutil
        shutil.copy(src, dst)


# ── End-card CTA ─────────────────────────────────────────────────────────────
def _create_end_card(duration: float = 4.0):
    """4-second bold subscribe/follow/like end-card."""
    font = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

    drawtext = (
        "drawbox=x=0:y=0:w=1080:h=1920:color=0x0D0D0D@1.0:t=fill,"
        "drawbox=x=0:y=670:w=1080:h=8:color=yellow@1.0:t=fill,"
        "drawbox=x=0:y=1190:w=1080:h=8:color=yellow@1.0:t=fill,"
        f"drawtext=text='DON'\\''T LEAVE YET':fontfile={font}:fontsize=80:"
        "fontcolor=yellow:x=(w-text_w)/2:y=710:shadowcolor=black:shadowx=3:shadowy=3,"
        f"drawtext=text='HIT SUBSCRIBE on YouTube':fontfile={font}:fontsize=64:"
        "fontcolor=white:x=(w-text_w)/2:y=830:shadowcolor=black:shadowx=2:shadowy=2,"
        f"drawtext=text='Follow @Tech8ytees on Instagram':fontfile={font}:fontsize=54:"
        "fontcolor=0xE1306C:x=(w-text_w)/2:y=940:shadowcolor=black:shadowx=2:shadowy=2,"
        f"drawtext=text='SMASH THAT LIKE RIGHT NOW':fontfile={font}:fontsize=68:"
        "fontcolor=yellow:x=(w-text_w)/2:y=1050:shadowcolor=black:shadowx=3:shadowy=3"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=black:size=1080x1920:rate=30:duration={duration}",
        "-vf", drawtext,
        "-c:v", "libx264", "-preset", "fast",
        "-t", str(duration),
        "end_card.mp4"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if res.returncode != 0 or not os.path.exists("end_card.mp4"):
        # Simple fallback
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=0x111111:size=1080x1920:rate=30:duration={duration}",
            "-vf", (
                "drawtext=text='SUBSCRIBE  •  FOLLOW  •  LIKE':"
                "fontsize=80:fontcolor=yellow:"
                "x=(w-text_w)/2:y=(h-text_h)/2:"
                "shadowcolor=black:shadowx=4:shadowy=4"
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
