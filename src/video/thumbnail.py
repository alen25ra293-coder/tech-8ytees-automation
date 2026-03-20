"""
Auto Thumbnail Generator
Generates a 1280x720 YouTube thumbnail with bold text overlay using Pillow.
"""
import os
import textwrap


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

        # ── Background: dark gradient ──────────────────────────────────────
        img = Image.new("RGB", (W, H), color=(10, 10, 25))
        draw = ImageDraw.Draw(img)

        # Draw gradient bands
        for y in range(H):
            ratio = y / H
            r = int(10 + ratio * 20)
            g = int(10 + ratio * 15)
            b = int(25 + ratio * 40)
            draw.line([(0, y), (W, y)], fill=(r, g, b))

        # Accent bar at top
        draw.rectangle([0, 0, W, 12], fill=(255, 200, 0))
        # Accent bar at bottom
        draw.rectangle([0, H - 12, W, H], fill=(255, 200, 0))

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

        font_main = load_font(130)
        font_sub  = load_font(52)
        font_badge = load_font(38)

        # ── Thumbnail text (main big yellow text) ──────────────────────────
        clean_main = thumbnail_text.upper().strip()
        lines = textwrap.wrap(clean_main, width=14)

        # Shadow + main text centered vertically in upper 55% of image
        text_block_height = len(lines) * 145
        start_y = max(60, (H * 0.55 - text_block_height) // 2)

        for i, line in enumerate(lines):
            y = int(start_y + i * 145)
            # Shadow
            draw.text((W // 2 + 4, y + 4), line, font=font_main,
                      fill=(0, 0, 0), anchor="mm")
            # Main text (yellow)
            draw.text((W // 2, y), line, font=font_main,
                      fill=(255, 220, 0), anchor="mm")

        # ── Channel badge ──────────────────────────────────────────────────
        badge_text = "Tech 8ytees"
        draw.rounded_rectangle([W - 280, H - 75, W - 20, H - 20],
                                radius=12, fill=(255, 200, 0))
        draw.text((W - 150, H - 47), badge_text, font=font_badge,
                  fill=(10, 10, 25), anchor="mm")

        # ── Subtitle line (smaller white text) ────────────────────────────
        sub_text = title[:55] + ("…" if len(title) > 55 else "")
        draw.text((W // 2, H - 100), sub_text, font=font_sub,
                  fill=(220, 220, 220), anchor="mm")

        # ── Save ───────────────────────────────────────────────────────────
        img.save(output_path, "JPEG", quality=95)
        size_kb = os.path.getsize(output_path) // 1024
        print(f"✅ Thumbnail saved: {output_path} ({size_kb} KB)")
        return output_path

    except Exception as e:
        print(f"❌ Thumbnail generation failed: {e}")
        return None
