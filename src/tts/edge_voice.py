import os
import subprocess

def generate_voiceover(script_text):
    """
    Generates voiceover using Microsoft Edge TTS (100% free).
    Also generates a WebVTT file for subtitles.
    """
    print("🎙️ Generating voiceover with edge-tts (fast & free)...")
    
    # Save script to a temporary file to avoid command line length limits
    with open("temp_script.txt", "w", encoding="utf-8") as f:
        f.write(script_text)
    
    # Select an energetic, male voice and increase the speed by 15% for a faster, engaging pace
    voice = "en-US-ChristopherNeural"
    rate = "+15%"
    
    cmd = [
        "edge-tts",
        "--voice", voice,
        "--rate", rate,
        "-f", "temp_script.txt",
        "--write-media", "voiceover.mp3",
        "--write-subtitles", "subtitles.vtt"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        # Clean up temp script
        if os.path.exists("temp_script.txt"):
            os.remove("temp_script.txt")
            
        if result.returncode == 0:
            print("✅ edge-tts voiceover and VTT subtitles generated successfully!")
            return True
        else:
            print(f"❌ edge-tts failed with error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to run edge-tts: {e}")
        if os.path.exists("temp_script.txt"):
            os.remove("temp_script.txt")
        return False
