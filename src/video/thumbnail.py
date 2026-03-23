"""
Auto Thumbnail Generator
Generates a 1280x720 YouTube thumbnail with bold text overlay using Pillow.
Randomizes accent color & background gradient each run for visual variety.
"""
import os
import random
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont


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


def _fetch_thumbnail_bg_image(topic: str, product_name: str = None) -> str | None:
    """Fetches a relevant tech-themed background image from Pexels for the thumbnail."""
    try:
        from src.video.pexels import _build_search_queries
        
        api_key = os.environ.get("PEXELS_API_KEY")
        if not api_key:
            return None
            
        queries = _build_search_queries(topic, product_name or "")
        query = queries[0] if queries else "tech gadget"
        
        print(f"🔍 Searching Pexels for thumbnail background: '{query}'")
        headers = {"Authorization": api_key}
        params = {"query": query, "per_page": 1, "orientation": "landscape", "size": "large"}
        
        r = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            photos = r.json().get("photos", [])
            if photos:
                img_url = photos[0]["src"]["large"]
                data = requests.get(img_url, timeout=10).content
                path = "temp_thumb_bg.jpg"
                with open(path, "wb") as f:
                    f.write(data)
                return path
    except Exception as e:
        print(f"⚠️ Thumbnail BG fetch failed: {e}")
    return None


def generate_thumbnail(thumbnail_text: str, title: str, style: str = None, output_path: str = "output_thumbnail.jpg") -> str | None:
    """
    Generate a YouTube thumbnail.
    Returns the path to the saved thumbnail, or None on failure.
    """
    print("🖼️  Generating YouTube thumbnail...")

    try:
        # ── 0. Optional: Stitch API Thumbnail ──────────────────────────────
        try:
            from src.generators.stitch_client import generate_ui_image
            if style:
                prompt = f"A high-performing YouTube Shorts thumbnail that perfectly matches this specific visual style: '{style}', and features bold text saying '{thumbnail_text}'"
            else:
                prompt = f"A high-contrast YouTube Shorts thumbnail with a glowing price tag, neon border, and bold text saying '{thumbnail_text}'"
            
            stitch_out = generate_ui_image(prompt, output_path)
            if stitch_out:
                return stitch_out
        except Exception as e:
            print(f"⚠️  Stitch API generation failed: {e}")

        W, H = 1280, 720

        # Pick a random color palette each run for variety
        palette = random.choice(_COLOR_PALETTES)
        accent  = palette["accent"]
        text_color = palette["text"]
        bg1     = palette["bg1"]
        bg2     = palette["bg2"]

        # ── Background: stock image or dark gradient ────────────────────────
        bg_img_path = _fetch_thumbnail_bg_image(title, thumbnail_text)
        if bg_img_path and os.path.exists(bg_img_path):
            img = Image.open(bg_img_path).convert("RGB")
            img = img.resize((W, H), Image.Resampling.LANCZOS)
            # Add a dark overlay to make text pop
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 160))
            img.paste(overlay, (0, 0), overlay)
            os.remove(bg_img_path)
        else:
            img = Image.new("RGB", (W, H), color=bg1)
            draw = ImageDraw.Draw(img)
            for y in range(H):
                ratio = y / H
                r = int(bg1[0] + ratio * (bg2[0] - bg1[0]))
                g = int(bg1[1] + ratio * (bg2[1] - bg1[1]))
                b = int(bg1[2] + ratio * (bg2[2] - bg1[2]))
                draw.line([(0, y), (W, y)], fill=(r, g, b))

        draw = ImageDraw.Draw(img)

        # Accent bars at top and bottom (more subtle neon glow)
        bar_h = 15
        draw.rectangle([0, 0, W, bar_h], fill=accent)
        draw.rectangle([0, H - bar_h, W, H], fill=accent)

        # ── Load fonts ──────────────────────────────────────────────────────
        font_paths = [
            "C:/Windows/Fonts/Impact.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]

        def load_font(size: int):
            for path in font_paths:
                if os.path.exists(path):
                    try:
                        return ImageFont.truetype(path, size)
                    except Exception:
                        continue
            return ImageFont.load_default()

        # Larger, bolder fonts
        font_main  = load_font(180)
        font_sub   = load_font(56)
        font_badge = load_font(42)

        # ── Thumbnail text (main big text) ─────────────────────────────────
        clean_main = thumbnail_text.upper().strip()
        lines = textwrap.wrap(clean_main, width=10)

        text_block_height = len(lines) * 190
        start_y = (H - text_block_height) // 2 - 20

        for i, line in enumerate(lines):
            y = int(start_y + i * 190) + 100
            # Thick shadow context
            for dist in range(1, 10):
                draw.text((W // 2 + dist, y + dist), line, font=font_main,
                          fill=(0, 0, 0, 100), anchor="mm")
            # Main colored text
            draw.text((W // 2, y), line, font=font_main,
                      fill=text_color, anchor="mm")

        # ── Channel badge (bottom-right) ──────────────────────────────────
        badge_text = "Tech 8ytees"
        badge_w, badge_h = 320, 80
        draw.rounded_rectangle([W - badge_w - 20, H - badge_h - 20, W - 20, H - 20],
                                radius=15, fill=accent)
        badge_fg = (0, 0, 0) if sum(accent) > 400 else (255, 255, 255)
        draw.text((W - (badge_w // 2) - 20, H - (badge_h // 2) - 20), badge_text, 
                  font=font_badge, fill=badge_fg, anchor="mm")

        # ── Subtitle - PUNCHY top line ─────────────────────────────────
        sub_text = title.upper()[:45]
        # Draw on top with backing box for contrast
        sub_box_h = 80
        draw.rectangle([0, 40, W, 40 + sub_box_h], fill=(0, 0, 0, 180))
        draw.text((W // 2, 40 + (sub_box_h // 2)), sub_text, font=font_sub,
                  fill=accent, anchor="mm")

        # ── Save ───────────────────────────────────────────────────────────
        img.save(output_path, "JPEG", quality=95)
        size_kb = os.path.getsize(output_path) // 1024
        print(f"✅ Enhanced Thumbnail saved: {output_path} ({size_kb} KB)")
        return output_path

    except Exception as e:
        print(f"❌ Thumbnail generation failed: {e}")
        return None
