"""
Auto Thumbnail Generator — Tech 8ytees (2026 Optimized)

Generates a 1280x720 YouTube thumbnail with:
- Split-screen comparison layout (cheap vs expensive)
- UI safe zone awareness (avoids button dead zones)
- Visual stress elements (arrows, X/checkmark)
- "First Frame" optimized — product result visible instantly
- Bold contrast for cheap mobile screens
"""
import os
import random
import textwrap
import re
import math
import subprocess


# Palette: high-contrast accent pairs for split-screen comparison
_COLOR_PALETTES = [
    {"left": (220, 40, 50), "right": (0, 180, 80), "bg": (10, 10, 20), "text": (255, 255, 255)},    # Red vs Green
    {"left": (200, 50, 50), "right": (30, 160, 255), "bg": (12, 12, 25), "text": (255, 255, 255)},   # Red vs Blue
    {"left": (255, 60, 60), "right": (0, 200, 100), "bg": (8, 8, 18), "text": (255, 255, 0)},        # Red vs Green, yellow text
    {"left": (220, 50, 50), "right": (50, 200, 50), "bg": (15, 10, 25), "text": (255, 230, 0)},      # Classic comparison
    {"left": (180, 30, 30), "right": (30, 200, 150), "bg": (5, 10, 20), "text": (255, 255, 255)},    # Dark red vs teal
    {"left": (200, 60, 80), "right": (40, 180, 220), "bg": (10, 10, 30), "text": (255, 200, 0)},     # Pink vs cyan
]


def generate_thumbnail(thumbnail_text: str, title: str, output_path: str = "output_thumbnail.jpg", video_path: str = "output.mp4") -> str | None:
    """
    Generate a split-screen comparison YouTube thumbnail.
    Returns the path to the saved thumbnail, or None on failure.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("⚠️  Pillow not installed — skipping thumbnail generation.")
        return None

    print("🖼️  Generating split-screen comparison thumbnail...")

    try:
        W, H = 1280, 720
        palette = random.choice(_COLOR_PALETTES)

        # ── Background: Extract Frame from Video (Proof of Human) ──────────
        extracted = False
        if os.path.exists(video_path):
            frame_path = "temp_frame.jpg"
            # Extract frame at 0.5s mark to ensure product/hands are visible
            cmd = ["ffmpeg", "-y", "-ss", "00:00:00.500", "-i", video_path, "-vframes", "1", "-q:v", "2", frame_path]
            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                if os.path.exists(frame_path):
                    img = Image.open(frame_path).convert("RGB")
                    # Video is 9:16 (1080x1920), thumbnail is 16:9 (1280x720)
                    # We crop the vertical center to fill 1280x720
                    vid_w, vid_h = img.size
                    target_ratio = W / H
                    vid_ratio = vid_w / vid_h
                    if vid_ratio < target_ratio:
                        new_w = W
                        new_h = int(W / vid_ratio)
                    else:
                        new_h = H
                        new_w = int(H * vid_ratio)
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    left = (img.width - W) // 2
                    top = (img.height - H) // 2
                    img = img.crop((left, top, left + W, top + H))
                    extracted = True
                    os.remove(frame_path)
            except Exception as e:
                print(f"⚠️  Failed to extract video frame: {e}")

        if not extracted:
            print("⚠️  Fallback to solid dark background since frame extraction failed.")
            img = Image.new("RGB", (W, H), color=palette["bg"])
            draw = ImageDraw.Draw(img)
            bg = palette["bg"]
            for y in range(H):
                ratio = y / H
                r = int(bg[0] + ratio * 15)
                g = int(bg[1] + ratio * 10)
                b = int(bg[2] + ratio * 20)
                draw.line([(0, y), (W, y)], fill=(min(r, 255), min(g, 255), min(b, 255)))

        # ── Split-screen divider (Safe Zone right shift) ──────────────────
        split_x = W // 2 + 40

        # Fast overlay using alpha composite for tints (so the photo shows through)
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # Left overlay (Expensive = Red zone, 50% opacity)
        left_color = palette["left"] + (130,)
        overlay_draw.rectangle([40, 80, split_x - 10, H - 80], fill=left_color)

        # Right overlay (Budget = Green zone, 50% opacity)
        right_color = palette["right"] + (130,)
        overlay_draw.rectangle([split_x + 10, 80, W - 40, H - 80], fill=right_color)

        # Composite and prepare drawing context
        img = img.convert("RGBA")
        img = Image.alpha_composite(img, overlay).convert("RGB")
        draw = ImageDraw.Draw(img)

        # Divider line (bright)
        draw.rectangle([split_x - 3, 60, split_x + 3, H - 60], fill=(255, 255, 255))

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

        font_big = load_font(120)
        font_mid = load_font(52)
        font_label = load_font(38)
        font_badge = load_font(32)

        # ── Extract price from title/text for comparison labels ─────────
        prices = re.findall(r'[₹$]\s?[\d,]+', f"{title} {thumbnail_text}")
        if len(prices) >= 2:
            expensive_price = max(prices, key=lambda p: int(re.sub(r'[^\d]', '', p)))
            budget_price = min(prices, key=lambda p: int(re.sub(r'[^\d]', '', p)))
        elif len(prices) == 1:
            budget_price = prices[0]
            expensive_price = "₹15,000+"
        else:
            budget_price = "BUDGET"
            expensive_price = "₹15,000+"

        # ── Left side: "Expensive" with ❌ ────────────────────────────────
        left_center_x = (40 + split_x) // 2
        draw.text((left_center_x, 120), "❌", font=load_font(80), fill=palette["left"], anchor="mm")
        
        # Red Price Badge
        bbox_l = draw.textbbox((left_center_x, 200), expensive_price, font=font_mid, anchor="mm")
        pad = 20
        draw.rounded_rectangle([bbox_l[0]-pad, bbox_l[1]-pad, bbox_l[2]+pad, bbox_l[3]+pad], radius=15, fill=(220, 40, 50))
        draw.text((left_center_x, 200), expensive_price, font=font_mid, fill=(255, 255, 255), anchor="mm")
        
        draw.text((left_center_x, 270), "OVERPRICED", font=font_label, fill=palette["left"], anchor="mm")

        # ── Right side: "Budget" with ✅ ──────────────────────────────────
        right_center_x = (split_x + W - 40) // 2
        draw.text((right_center_x, 120), "✅", font=load_font(80), fill=palette["right"], anchor="mm")
        
        # High-Contrast Yellow Price Badge
        bbox_r = draw.textbbox((right_center_x, 200), budget_price, font=font_mid, anchor="mm")
        draw.rounded_rectangle([bbox_r[0]-pad, bbox_r[1]-pad, bbox_r[2]+pad, bbox_r[3]+pad], radius=15, fill=(255, 230, 0))
        draw.text((right_center_x, 200), budget_price, font=font_mid, fill=(10, 10, 10), anchor="mm")
        
        draw.text((right_center_x, 270), "SAME RESULTS", font=font_label, fill=palette["right"], anchor="mm")

        # ── Main text (center, large, with outline) ───────────────────────
        # SAFE ZONE: Place text center or center-left (right side has YT buttons)
        clean_main = thumbnail_text.upper().strip()
        lines = textwrap.wrap(clean_main, width=14)

        text_block_height = len(lines) * 130
        start_y = max(300, (H * 0.45 + 150 - text_block_height / 2))

        text_x = W // 2 - 30  # Shift slightly left (safe zone)

        for i, line in enumerate(lines):
            y = int(start_y + i * 130)
            # Thick dark outline
            for dx in [-4, 0, 4]:
                for dy in [-4, 0, 4]:
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((text_x + dx, y + dy), line, font=font_big,
                              fill=(0, 0, 0), anchor="mm")
            draw.text((text_x, y), line, font=font_big,
                      fill=palette["text"], anchor="mm")

        # ── Channel badge (bottom-left — safe zone) ──────────────────────
        badge_text = "Tech 8ytees"
        draw.rounded_rectangle([20, H - 70, 250, H - 20], radius=12, fill=(255, 200, 0))
        draw.text((135, H - 45), badge_text, font=font_badge, fill=(10, 10, 25), anchor="mm")

        # ── Visual Stress: Red Arrow ─────────────────────────────────────
        # Arrow pointing down-left towards the center of the right side (where the budget product is)
        arrow_color = (255, 20, 20)
        start_pt = (W//2 + 250, H//2 - 180)
        end_pt = (W//2 + 70, H//2 - 20)
        
        # Helper function to draw arrow
        dx = end_pt[0] - start_pt[0]
        dy = end_pt[1] - start_pt[1]
        angle = math.atan2(dy, dx)
        head_size = 50
        p1 = (end_pt[0] - head_size * math.cos(angle - math.pi/6),
              end_pt[1] - head_size * math.sin(angle - math.pi/6))
        p2 = (end_pt[0] - head_size * math.cos(angle + math.pi/6),
              end_pt[1] - head_size * math.sin(angle + math.pi/6))
              
        # Drop shadow for arrow to stand out against background
        shadow_offset = 6
        draw.line([(start_pt[0]+shadow_offset, start_pt[1]+shadow_offset), (end_pt[0]+shadow_offset, end_pt[1]+shadow_offset)], fill=(0, 0, 0), width=30)
        draw.polygon([(end_pt[0]+shadow_offset, end_pt[1]+shadow_offset), (p1[0]+shadow_offset, p1[1]+shadow_offset), (p2[0]+shadow_offset, p2[1]+shadow_offset)], fill=(0, 0, 0))
        
        # Main Arrow
        draw.line([start_pt, end_pt], fill=arrow_color, width=30)
        draw.polygon([end_pt, p1, p2], fill=arrow_color)

        # ── "VS" circle in center ────────────────────────────────────────
        vs_y = H // 2 - 20
        draw.ellipse([split_x - 35, vs_y - 35, split_x + 35, vs_y + 35], fill=(255, 200, 0))
        draw.text((split_x, vs_y), "VS", font=load_font(36), fill=(10, 10, 25), anchor="mm")

        # ── Save ───────────────────────────────────────────────────────────
        img.save(output_path, "JPEG", quality=95)
        size_kb = os.path.getsize(output_path) // 1024
        print(f"✅ Thumbnail saved: {output_path} ({size_kb} KB)")
        return output_path

    except Exception as e:
        print(f"❌ Thumbnail generation failed: {e}")
        return None
