"""
Auto Thumbnail Generator
Generates a 1280x720 YouTube thumbnail with bold text overlay using Pillow.
Randomizes accent color & background gradient each run for visual variety.
"""
import os
import random
import textwrap


# Palette of vibrant accent color schemes (accent, text, background start, end)
_COLOR_PALETTES = [
    {"accent": (255, 200,   0), "text": (255, 230,   0), "bg1": ( 10,  10,  25), "bg2": ( 25,  20,  50)},  # Gold (default)
    {"accent": (255,  50,  80), "text": (255,  80, 100), "bg1": ( 15,   5,  10), "bg2": ( 40,  10,  20)},  # Red/Pink
    {"accent": (  0, 200, 255), "text": (  0, 230, 255), "bg1": (  5,  10,  25), "bg2": ( 10,  25,  50)},  # Cyan
    {"accent": (  0, 255, 120), "text": ( 80, 255, 160), "bg1": (  5,  15,  10), "bg2": ( 10,  35,  20)},  # Green
    {"accent": (255, 120,   0), "text": (255, 160,  30), "bg1": ( 20,  10,   5), "bg2": ( 40,  20,   5)},  # Orange
    {"accent": (180,   0, 255), "text": (210,  60, 255), "bg1": ( 15,   5,  25), "bg2": ( 30,   5,  50)},  # Purple
    {"accent": (255, 255, 255), "text": (240, 240, 240), "bg1": (  0,  10,  30), "bg2": ( 10,  20,  60)},  # White/Deep Blue
    {"accent": (255, 230,   0), "text": (255, 255,   0), "bg1": ( 30,  20,   0), "bg2": ( 60,  40,   0)},  # Amber/Black
    {"accent": (  0, 255, 255), "text": (200, 255, 255), "bg1": (  0,  40,  40), "bg2": (  0,  15,  15)},  # Teal/Dark
    {"accent": (255,  80,  80), "text": (255, 120, 120), "bg1": ( 35,  10,  10), "bg2": ( 15,   5,   5)},  # Crimson
    {"accent": (200, 255,   0), "text": (220, 255,  50), "bg1": ( 15,  20,   0), "bg2": (  5,  10,   5)},  # Lime/Dark
    {"accent": ( 80, 150, 255), "text": (130, 180, 255), "bg1": (  5,  10,  30), "bg2": (  0,   5,  15)},  # Electric Blue
]


def generate_thumbnail(thumbnail_text: str, title: str, output_path: str = "output_thumbnail.jpg") -> str | None:
    """
    Generate a YouTube thumbnail.
    Returns the path to the saved thumbnail, or None on failure.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("⚠️  Pillow not installed — skipping thumbnail generation.")
        return None

    print("🖼️  Generating YouTube thumbnail...")

    try:
        W, H = 1280, 720

        # Pick a random color palette each run for variety
        palette = random.choice(_COLOR_PALETTES)
        accent  = palette["accent"]
        text_color = palette["text"]
        bg1     = palette["bg1"]
        bg2     = palette["bg2"]

        # ── Background: dark gradient ──────────────────────────────────────
        img = Image.new("RGB", (W, H), color=bg1)
        draw = ImageDraw.Draw(img)

        for y in range(H):
            ratio = y / H
            r = int(bg1[0] + ratio * (bg2[0] - bg1[0]))
            g = int(bg1[1] + ratio * (bg2[1] - bg1[1]))
            b = int(bg1[2] + ratio * (bg2[2] - bg1[2]))
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        # Accent bars at top and bottom
        bar_h = 12
        draw.rectangle([0, 0, W, bar_h], fill=accent)
        draw.rectangle([0, H - bar_h, W, H], fill=accent)

        # ── Load fonts ──────────────────────────────────────────────────────
        font_paths = [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
            "C:/Windows/Fonts/Impact.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ]

        def load_font(size: int):
            for path in font_paths:
                if os.path.exists(path):
                    try:
                        return ImageFont.truetype(path, size)
                    except Exception:
                        continue
            return ImageFont.load_default()

        font_main  = load_font(140)
        font_sub   = load_font(44)
        font_badge = load_font(36)

        # ── Thumbnail text (main big text) ─────────────────────────────────
        clean_main = thumbnail_text.upper().strip()
        lines = textwrap.wrap(clean_main, width=12)

        text_block_height = len(lines) * 160
        start_y = max(80, (H * 0.55 - text_block_height) // 2)

        for i, line in enumerate(lines):
            y = int(start_y + i * 160)
            # Thick dark outline (draw text 8 times offset for stroke effect)
            for dx in [-3, 0, 3]:
                for dy in [-3, 0, 3]:
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((W // 2 + dx, y + dy), line, font=font_main,
                              fill=(0, 0, 0), anchor="mm")
            # Main colored text on top
            draw.text((W // 2, y), line, font=font_main,
                      fill=text_color, anchor="mm")

        # ── Channel badge ──────────────────────────────────────────────────
        badge_text = "Tech 8ytees"
        draw.rounded_rectangle([W - 280, H - 75, W - 20, H - 20],
                                radius=12, fill=accent)
        # Badge text in dark color
        badge_fg = (10, 10, 25) if sum(accent) > 400 else (255, 255, 255)
        draw.text((W - 150, H - 47), badge_text, font=font_badge,
                  fill=badge_fg, anchor="mm")

        # ── Subtitle line (smaller text) ─────────────────────────────────
        sub_text = title[:55] + ("…" if len(title) > 55 else "")
        draw.text((W // 2, H - 100), sub_text, font=font_sub,
                  fill=(210, 210, 210), anchor="mm")

        # ── Save ───────────────────────────────────────────────────────────
        img.save(output_path, "JPEG", quality=95)
        size_kb = os.path.getsize(output_path) // 1024
        print(f"✅ Thumbnail saved: {output_path} ({size_kb} KB)")
        return output_path

    except Exception as e:
        print(f"❌ Thumbnail generation failed: {e}")
        return None
