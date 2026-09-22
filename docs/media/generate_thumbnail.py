#!/usr/bin/env python3
"""Generate CHP video thumbnail — 1280×720 PNG."""

from PIL import Image, ImageDraw, ImageFont

# ── Canvas ──────────────────────────────────────────────────────────────
W, H = 1280, 720
BG       = (13, 17, 23)        # #0D1117
TERM_BG  = (22, 27, 34)        # #161B22
BORDER   = (48, 54, 61)        # #30363D
GREEN    = (63, 185, 80)       # #3FB950
CYAN     = (88, 166, 255)      # #58A6FF
YELLOW   = (210, 153, 34)      # #D29922
WHITE    = (230, 237, 243)     # #E6EDF3
GRAY     = (139, 148, 158)     # #8B949E
BADGE_BG = (35, 134, 54)       # #238636

img  = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# ── Fonts ───────────────────────────────────────────────────────────────
FONTS = "/usr/share/fonts/truetype/dejavu/"
mono_r     = ImageFont.truetype(FONTS + "DejaVuSansMono.ttf", 18)
mono_b     = ImageFont.truetype(FONTS + "DejaVuSansMono-Bold.ttf", 18)
sans_b     = ImageFont.truetype(FONTS + "DejaVuSans-Bold.ttf", 64)
sans_b2    = ImageFont.truetype(FONTS + "DejaVuSans-Bold.ttf", 56)
sans_r     = ImageFont.truetype(FONTS + "DejaVuSans.ttf", 20)
sans_r_sm  = ImageFont.truetype(FONTS + "DejaVuSans.ttf", 15)
mono_sm    = ImageFont.truetype(FONTS + "DejaVuSansMono.ttf", 14)
mono_sm_b  = ImageFont.truetype(FONTS + "DejaVuSansMono-Bold.ttf", 14)
sans_badge = ImageFont.truetype(FONTS + "DejaVuSans-Bold.ttf", 16)
sans_license = ImageFont.truetype(FONTS + "DejaVuSans.ttf", 13)

def text_size(font, text):
    """Get text dimensions using textbbox."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def draw_gradient_text(draw, img, text, font, x, y, color_start, color_end):
    """Draw text with per-character color gradient, paste onto img."""
    cx = x
    for i, ch in enumerate(text):
        t = i / max(len(text) - 1, 1)
        r = int(color_start[0] * (1 - t) + color_end[0] * t)
        g = int(color_start[1] * (1 - t) + color_end[1] * t)
        b = int(color_start[2] * (1 - t) + color_end[2] * t)
        # Render single char on a small transparent canvas
        cw, ch_h = text_size(font, ch)
        tmp = Image.new("RGBA", (cw + 4, ch_h + 4), (0, 0, 0, 0))
        tmp_draw = ImageDraw.Draw(tmp)
        tmp_draw.text((0, 0), ch, fill=(r, g, b, 255), font=font)
        # Paste onto main image (convert tmp to RGB for paste)
        img.paste(tmp.convert("RGB").point(lambda p: p if p > 0 else BG[0] if p == 0 else p),
                  (cx, y), tmp)
        # Advance by actual glyph width
        bbox = font.getbbox(ch)
        cx += bbox[2] - bbox[0]

# ── Subtle dot-grid background ─────────────────────────────────────────
for gx in range(0, W, 32):
    for gy in range(0, H, 32):
        img.putpixel((gx, gy), (26, 31, 40))

# ── Subtle radial glow behind title area ───────────────────────────────
for r in range(400, 0, -2):
    alpha_ratio = r / 400
    c = int(18 + 6 * (1 - alpha_ratio))
    bx, by = 940, 340
    cx0, cy0 = max(0, bx - r), max(0, by - r)
    cx1, cy1 = min(W, bx + r), min(H, by + r)
    draw.ellipse([cx0, cy0, cx1, cy1], fill=(c, c, c + 4))

# ── Terminal window ────────────────────────────────────────────────────
term_x, term_y = 50, 90
term_w, term_h = 700, 540
title_bar_h = 36

# Terminal shadow
draw.rounded_rectangle(
    [term_x + 4, term_y + 4, term_x + term_w + 4, term_y + term_h + 4],
    radius=12, fill=(4, 6, 9)
)
# Terminal border
draw.rounded_rectangle(
    [term_x - 1, term_y - 1, term_x + term_w + 1, term_y + term_h + 1],
    radius=12, fill=BORDER
)
# Terminal background
draw.rounded_rectangle(
    [term_x, term_y, term_x + term_w, term_y + term_h],
    radius=12, fill=TERM_BG
)

# Title bar
draw.rounded_rectangle(
    [term_x, term_y, term_x + term_w, term_y + title_bar_h],
    radius=12, fill=(20, 24, 31)
)
# Square off bottom of title bar
draw.rectangle(
    [term_x, term_y + title_bar_h - 12, term_x + term_w, term_y + title_bar_h],
    fill=(20, 24, 31)
)

# Traffic-light dots
dot_y = term_y + title_bar_h // 2
for i, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
    cxd = term_x + 22 + i * 22
    draw.ellipse([cxd - 6, dot_y - 6, cxd + 6, dot_y + 6], fill=color)

# "CHP Session" label in title bar
_, lbl_h = text_size(mono_sm_b, "CHP Session")
draw.text((term_x + 96, dot_y - lbl_h // 2), "CHP Session", fill=GRAY, font=mono_sm_b)

# Thin separator line
draw.line(
    [term_x + 10, term_y + title_bar_h, term_x + term_w - 10, term_y + title_bar_h],
    fill=BORDER, width=1
)

# ── Terminal text content ─────────────────────────────────────────────
tx = term_x + 22
ty_start = term_y + title_bar_h + 18
line_h = 30

terminal_lines = [
    ("$ cme chp-start --title \"Fund enterprise workflow\"", GREEN, mono_b, 0),
    ("", None, None, 0),
    ("  CHP v2.4.0  |  consensus-hardening-protocol", GRAY, mono_sm, 0),
    ("", None, None, 0),
    ("  \u2713  Dossier built", GREEN, mono_r, 0),
    ("  \u2713  Foundation score: 82/100", CYAN, mono_r, 0),
    ("  \u2713  Packet generated", GREEN, mono_r, 0),
    ("", None, None, 0),
    ("  \u26A1  Adversarial attack in progress...", YELLOW, mono_r, 0),
    ("  \u26A0  PROVISIONAL_LOCK", YELLOW, mono_b, 0),
    ("", None, None, 0),
    ("  \u2713  LOCKED \u2014 Third-party validation passed", GREEN, mono_b, 0),
    ("", None, None, 0),
    ("  Packet: 0xF7B2...C91A  |  Round: 14", GRAY, mono_sm, 0),
    ("  Consensus: 6/7 agents  |  1 abstained", GRAY, mono_sm, 0),
]

cursor_y = ty_start
for text, color, font, indent in terminal_lines:
    if text == "":
        cursor_y += line_h * 0.5
        continue
    draw.text((tx + indent, cursor_y), text, fill=color, font=font)
    cursor_y += line_h

# Blinking cursor
cursor_x = tx + 8
cursor_y += 4
draw.rectangle([cursor_x, cursor_y, cursor_x + 9, cursor_y + 20], fill=GREEN)

# ── Right-side title area ──────────────────────────────────────────────
rx = 790  # right panel x start

# "Consensus Hardening" — large white
draw.text((rx, 195), "Consensus", fill=WHITE, font=sans_b)
draw.text((rx, 265), "Hardening", fill=WHITE, font=sans_b)

# "Protocol" — gradient cyan→green, character by character
proto_y = 340
draw_gradient_text(draw, img, "Protocol", sans_b2, rx, proto_y, CYAN, GREEN)

# Subtitle
draw.text((rx, 415), "Multi-Agent Decision Governance", fill=GRAY, font=sans_r)

# ── Shield / Lock icon (geometric) ─────────────────────────────────────
shield_x, shield_y = rx + 16, 470
# Shield body
shield_pts = [
    (shield_x, shield_y),
    (shield_x + 40, shield_y),
    (shield_x + 40, shield_y + 28),
    (shield_x + 20, shield_y + 44),
    (shield_x, shield_y + 28),
]
draw.polygon(shield_pts, fill=None, outline=CYAN, width=2)

# Lock body inside shield
lock_cx = shield_x + 20
lock_cy = shield_y + 18
draw.rectangle([lock_cx - 7, lock_cy, lock_cx + 7, lock_cy + 12], fill=CYAN)
# Lock shackle
draw.arc([lock_cx - 5, lock_cy - 10, lock_cx + 5, lock_cy + 2], 180, 0, fill=CYAN, width=2)
# Keyhole
draw.ellipse([lock_cx - 2, lock_cy + 3, lock_cx + 2, lock_cy + 7], fill=TERM_BG)

# Label next to shield
draw.text((shield_x + 52, shield_y + 8), "Multi-agent secure consensus", fill=GRAY, font=sans_r_sm)

# ── "3 min demo" badge (bottom-right) ─────────────────────────────────
badge_text = "\u25B6  3 min demo"
bw, bh = text_size(sans_badge, badge_text)
badge_px, badge_py = 20, 12
bx1 = W - bw - badge_px * 2 - 40
by1 = H - bh - badge_py * 2 - 40
bx2 = W - 40
by2 = H - 40

draw.rounded_rectangle([bx1, by1, bx2, by2], radius=8, fill=BADGE_BG)
draw.text((bx1 + badge_px, by1 + badge_py), badge_text, fill=WHITE, font=sans_badge)

# ── "MIT License" badge (top-right) ───────────────────────────────────
mit_text = "MIT License"
mw, mh = text_size(sans_license, mit_text)
mit_px, mit_py = 14, 6
mx1 = W - mw - mit_px * 2 - 50
my1 = 28
mx2 = W - 50
my2 = 28 + mh + mit_py * 2

draw.rounded_rectangle([mx1, my1, mx2, my2], radius=6, fill=BORDER)
draw.text((mx1 + mit_px, my1 + mit_py), mit_text, fill=GRAY, font=sans_license)

# ── Thin accent line separator between terminal and title ──────────────
draw.line([770, 120, 770, 610], fill=(30, 36, 44), width=1)

# ── Bottom-left: small repo path ──────────────────────────────────────
draw.text((60, H - 45), "~/cme/consensus-hardening-protocol", fill=(48, 54, 61), font=mono_sm)

# ── Save ────────────────────────────────────────────────────────────────
out = "/home/z/my-project/mineral-review/consensus-hardening-protocol/docs/media/chp-thumbnail.png"
img.save(out, "PNG")
print(f"Saved: {out}  ({W}x{H})")
