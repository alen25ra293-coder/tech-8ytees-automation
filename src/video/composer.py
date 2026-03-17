import os
import subprocess

def create_video(title, video_clips):
    """
    Composes the final video:
    1. Scales/crops all background clips to 1080x1920
    2. Concatenates them into one long background
    3. Overlays the voiceover audio
    4. Burns the edge-tts generated VTT subtitles onto the video with a bold, yellow style
    """
    print("🎞️ Assembling final video with FFmpeg...")
    
    if not os.path.exists("voiceover.mp3"):
        print("❌ Voiceover file not found - cannot create video")
        return False
        
    try:
        # Get audio duration
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            "voiceover.mp3"
        ], capture_output=True, text=True, timeout=10)
        
        duration = float(result.stdout.strip())
        video_duration = duration + 2  # slight padding
        
        # 1. Standardize and scale each clip to 1080x1920
        scaled_clips = []
        if video_clips:
            print(f"🎬 Standardizing {len(video_clips)} background clips...")
            for i, clip in enumerate(video_clips):
                if not os.path.exists(clip):
                    continue
                scaled_name = f"scaled_{i}.mp4"
                scale_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
                # Strip audio, scale/crop, standard framerate
                subprocess.run([
                    "ffmpeg", "-y", "-i", clip,
                    "-vf", scale_filter,
                    "-r", "30", "-c:v", "libx264", "-an",
                    "-preset", "ultrafast", scaled_name
                ], capture_output=True)
                scaled_clips.append(scaled_name)
        
        # 2. Concatenate them. We will create a loop if needed.
        if scaled_clips:
            # We need to ensure the background is at least as long as video_duration
            # So we just repeat the list of clips a few times in our concat file
            with open("clips.txt", "w") as f:
                # Assuming each clip is ~10 seconds, repeat list enough times
                repeats = int(video_duration / (len(scaled_clips) * 5)) + 2 
                for _ in range(repeats):
                    for c in scaled_clips:
                        f.write(f"file '{c}'\n")
            
            print("🎬 Concatenating background...")
            subprocess.run([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "clips.txt",
                "-c", "copy", "bg_looped.mp4"
            ], capture_output=True)
            background_input = "bg_looped.mp4"
        else:
            # Fallback to dark background color if no clips downloaded
            print("⚠️ No clips available, using dark fallback background.")
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x0A0A19:size=1080x1920:duration={video_duration}",
                "-c:v", "libx264", "-preset", "ultrafast", "bg_looped.mp4"
            ], capture_output=True)
            background_input = "bg_looped.mp4"
            
        # 3. Final Render: Audio + Subtitles + Trimming
        # Adding a massive 'MrBeast' style yellow drop-shadow style for the subtitles in the center
        print("🎬 Burning viral subtitles & rendering ultimate video...")
        subtitle_style = "Fontname=Impact,Fontsize=110,PrimaryColour=&H00FFFF,OutlineColour=&H000000,BorderStyle=1,Outline=4,Shadow=2,Alignment=2,MarginV=900"
        
        has_subs = os.path.exists("subtitles.vtt")
        
        final_cmd = [
            "ffmpeg", "-y",
            "-i", background_input,
            "-i", "voiceover.mp3"
        ]
        
        if has_subs:
            # Note: Windows path escaping for ffmpeg subtitles filter can be tricky, 
            # so we assume subtitles.vtt is in the current working directory
            final_cmd.extend(["-vf", f"subtitles=subtitles.vtt:force_style='{subtitle_style}'"])
            
        final_cmd.extend([
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac",
            "-t", str(video_duration),
            "-shortest", 
            "output.mp4"
        ])
        
        res = subprocess.run(final_cmd, capture_output=True, text=True, timeout=600)
        
        if res.returncode != 0:
            print(f"❌ Final render failed: {res.stderr[-800:]}")
            return False
            
        print(f"✅ Final video ready: output.mp4 (Length: {video_duration:.1f}s)")
        
        # Cleanup temp clips
        if scaled_clips:
            for c in scaled_clips:
                if os.path.exists(c):
                    os.remove(c)
            for clip in video_clips:
                if os.path.exists(clip):
                    os.remove(clip)
        if os.path.exists("clips.txt"):
            os.remove("clips.txt")
        if os.path.exists("bg_looped.mp4"):
            os.remove("bg_looped.mp4")
            
        return True

    except Exception as e:
        print(f"❌ Video assembly failed: {e}")
        return False
