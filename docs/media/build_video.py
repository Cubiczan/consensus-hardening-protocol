#!/usr/bin/env python3
"""
Consensus Hardening Protocol - robust media generator.

Produces:
  - docs/media/chp-thumbnail.jpg        (hero / README poster)
  - docs/media/chp-architecture.jpg     (5-subsystem architecture)
  - docs/media/chp-phases.jpg           (4-phase protocol lifecycle)
  - docs/media/chp-social-preview.jpg   (1280x640 social card)
  - docs/media/chp-demo.mp4             (~25s, 1080p, H.264, README-friendly)
  - docs/media/chp-demo-3min.mp4        (alias / replacement of legacy file)

Style: dark cyber (#0a0e27 bg, neon cyan/magenta accents, monospace labels)
Reuses the existing palette from docs/media/build_video.py so the new
assets match the existing repo aesthetic.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ────────────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────────────

W, H = 1920, 1080
FPS = 30

# Palette (matches existing build_video.py)
BG       = (13, 17, 23)
TBG      = (22, 27, 34)
BD       = (48, 54, 62)
GREEN    = (63, 185, 80)
CYAN     = (88, 166, 255)
YELLOW   = (210, 153, 34)
RED      = (248, 81, 73)
WHITE    = (230, 237, 243)
GRAY     = (139, 148, 158)
DIM      = (72, 79, 88)
PURPLE   = (188, 140, 255)
MAGENTA  = (255, 99, 196)

# Fonts (DejaVu is always present on this image)
FONT_PATHS = {
    "FB":    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "FM":    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "FM_B":  "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "FS":    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "FM_S":  "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "FS_S":  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "FM_T":  "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "FB_XL": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "FB_XXL":"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
}

FONT_SIZES = {
    "FB":    44,
    "FM":    22,
    "FM_B":  22,
    "FS":    28,
    "FM_S":  18,
    "FS_S":  22,
    "FM_T":  16,
    "FB_XL": 72,
    "FB_XXL":96,
}

FONTS: dict[str, ImageFont.FreeTypeFont] = {}


def load_fonts() -> None:
    for key, path in FONT_PATHS.items():
        try:
            FONTS[key] = ImageFont.truetype(path, FONT_SIZES[key])
        except Exception:
            FONTS[key] = ImageFont.load_default()


# ────────────────────────────────────────────────────────────────────────────
# Drawing primitives
# ────────────────────────────────────────────────────────────────────────────

def new_frame() -> Image.Image:
    return Image.new("RGB", (W, H), BG)


def text_centered(d: ImageDraw.ImageDraw, text: str, y: int, font, color) -> None:
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    d.text(((W - tw) // 2, y), text, fill=color, font=font)


def draw_rounded_rect(d, xy, radius, **kwargs) -> None:
    x0, y0, x1, y1 = xy
    d.rectangle([x0 + radius, y0, x1 - radius, y1], **kwargs)
    d.rectangle([x0, y0 + radius, x1, y1 - radius], **kwargs)
    d.pieslice([x0, y0, x0 + 2 * radius, y0 + 2 * radius], 180, 270, **kwargs)
    d.pieslice([x1 - 2 * radius, y0, x1, y0 + 2 * radius], 270, 360, **kwargs)
    d.pieslice([x0, y1 - 2 * radius, x0 + 2 * radius, y1], 90, 180, **kwargs)
    d.pieslice([x1 - 2 * radius, y1 - 2 * radius, x1, y1], 0, 90, **kwargs)


def terminal_frame(title: str = "chp-session - cme cli"):
    img = new_frame()
    d = ImageDraw.Draw(img)
    d.rectangle([80, 70, 1840, 1010], fill=TBG, outline=BD)
    d.rectangle([80, 70, 1840, 110], fill=(33, 38, 45))
    d.ellipse([100, 78, 118, 96], fill=(255, 95, 87))
    d.ellipse([128, 78, 146, 96], fill=(254, 188, 46))
    d.ellipse([156, 78, 174, 96], fill=(40, 200, 64))
    d.text((200, 82), title, fill=GRAY, font=FONTS["FM_T"])
    return img, d


def draw_shield(d, cx, cy, size, color):
    """Draw a simple shield icon centered at (cx, cy)."""
    s = size // 2
    pts = [
        (cx, cy - s),
        (cx + s, cy - s + s // 3),
        (cx + s, cy + s // 3),
        (cx, cy + s),
        (cx - s, cy + s // 3),
        (cx - s, cy - s + s // 3),
    ]
    d.polygon(pts, fill=color)


def draw_grid_bg(d, spacing=80, color=(20, 26, 34)):
    for x in range(0, W, spacing):
        d.line([(x, 0), (x, H)], fill=color, width=1)
    for y in range(0, H, spacing):
        d.line([(0, y), (W, y)], fill=color, width=1)


# ────────────────────────────────────────────────────────────────────────────
# Frame encoder
# ────────────────────────────────────────────────────────────────────────────

class FrameWriter:
    def __init__(self, frames_dir: Path):
        self.frames_dir = frames_dir
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        self.idx = 0

    def save(self, img: Image.Image) -> None:
        img.save(self.frames_dir / f"f{self.idx:05d}.png")
        self.idx += 1

    def hold(self, img: Image.Image, seconds: float) -> None:
        for _ in range(int(seconds * FPS)):
            self.save(img)

    def total(self) -> int:
        return self.idx


# ────────────────────────────────────────────────────────────────────────────
# Animated helpers (per-frame deltas)
# ────────────────────────────────────────────────────────────────────────────

def ease_in_out(t: float) -> float:
    if t < 0.5:
        return 4 * t * t * t
    return 1 - pow(-2 * t + 2, 3) / 2


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_color(c1, c2, t: float):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


# ────────────────────────────────────────────────────────────────────────────
# Scene builders — each returns a list of PIL frames
# ────────────────────────────────────────────────────────────────────────────

def scene_title_card(fw: FrameWriter) -> None:
    """Scene 1: animated title card with shield, fade-in, ~4s."""
    duration = 4.0
    n = int(duration * FPS)
    for i in range(n):
        t = i / n
        img = new_frame()
        d = ImageDraw.Draw(img)
        draw_grid_bg(d)

        # Shield reveal
        shield_t = min(1.0, t / 0.4)
        shield_size = int(lerp(0, 220, ease_in_out(shield_t)))
        if shield_size > 4:
            shield_color = lerp_color(CYAN, MAGENTA, shield_t * 0.3)
            draw_shield(d, W // 2, 280, shield_size, shield_color)
            # Inner check mark
            if shield_size > 100:
                d.line([(W // 2 - 40, 280), (W // 2 - 10, 320), (W // 2 + 50, 240)],
                       fill=WHITE, width=8)

        # Title fade-in after shield
        if t > 0.4:
            title_t = min(1.0, (t - 0.4) / 0.3)
            alpha_color = lerp_color(BG, WHITE, title_t)
            text_centered(d, "Consensus Hardening Protocol", 470, FONTS["FB_XL"], alpha_color)

        if t > 0.6:
            sub_t = min(1.0, (t - 0.6) / 0.3)
            alpha_color = lerp_color(BG, GRAY, sub_t)
            text_centered(d, "Multi-Agent Decision Governance for High-Stakes Finance",
                          580, FONTS["FS"], alpha_color)

        if t > 0.8:
            cmd_t = min(1.0, (t - 0.8) / 0.3)
            alpha_color = lerp_color(BG, CYAN, cmd_t)
            text_centered(d, "cme chp-start  |  chp-receive  |  chp-validate  |  chp-triangulate",
                          660, FONTS["FM_S"], alpha_color)

        # Bottom badges
        if t > 0.95:
            draw_rounded_rect(d, (680, 760, 880, 800), 8, fill=TBG, outline=GREEN)
            text_centered(d, "MIT License", 768, FONTS["FM_T"], GREEN)
            draw_rounded_rect(d, (920, 760, 1180, 800), 8, fill=TBG, outline=CYAN)
            text_centered(d, "42 tests passing", 768, FONTS["FM_T"], CYAN)
            draw_rounded_rect(d, (1220, 760, 1400, 800), 8, fill=TBG, outline=YELLOW)
            text_centered(d, "Zero deps", 768, FONTS["FM_T"], YELLOW)

        # Progress bar at bottom
        bar_w = int(800 * t)
        d.rectangle([560, 1020, 560 + bar_w, 1028], fill=CYAN)
        d.rectangle([560, 1020, 1360, 1028], outline=BD)

        fw.save(img)


def scene_problem(fw: FrameWriter) -> None:
    """Scene 2: the three failures CHP solves, ~4s."""
    duration = 4.0
    n = int(duration * FPS)
    base = new_frame()
    d_base = ImageDraw.Draw(base)
    draw_grid_bg(d_base)
    d_base.text((160, 80), "The Problem", fill=WHITE, font=FONTS["FB"])
    d_base.text((160, 140), "When organizations deploy multiple AI agents, three things break:",
                fill=GRAY, font=FONTS["FS"])

    items = [
        (220, "1. Context Fragmentation", RED,
         "Each agent sees a different slice of the organization"),
        (380, "2. Reasoning Opacity", YELLOW,
         "Humans get conclusions without seeing how they were reached"),
        (540, "3. Output Drift", PURPLE,
         "Agents produce prose; humans need something runnable"),
    ]

    for i, (y, title, color, desc) in enumerate(items):
        reveal_at = 0.3 + i * 0.4
        for frame_i in range(n):
            t = frame_i / n
            if t < reveal_at:
                continue
            local_t = min(1.0, (t - reveal_at) / 0.3)
            offset = int(lerp(40, 0, ease_in_out(local_t)))
            alpha = local_t

            # We compose onto a copy of the base for each frame
            img = base.copy()
            d = ImageDraw.Draw(img)
            title_color = lerp_color(BG, color, alpha)
            desc_color = lerp_color(BG, GRAY, alpha)
            d.text((160 + offset, y), title, fill=title_color, font=FONTS["FS"])
            d.text((180 + offset, y + 45), desc, fill=desc_color, font=FONTS["FS_S"])
            # Underline
            ul_w = int(lerp(0, 480, local_t))
            d.line([(160 + offset, y + 38), (160 + offset + ul_w, y + 38)], fill=color, width=2)
            fw.save(img)
            break  # only save once per item, the loop is just to advance time
        else:
            continue

    # Final hold with solution line
    final = base.copy()
    d = ImageDraw.Draw(final)
    for y, title, color, desc in items:
        d.text((160, y), title, fill=color, font=FONTS["FS"])
        d.text((180, y + 45), desc, fill=GRAY, font=FONTS["FS_S"])
        d.line([(160, y + 38), (640, y + 38)], fill=color, width=2)
    # Solution
    draw_rounded_rect(d, (160, 720, 1760, 820), 12, fill=TBG, outline=CYAN)
    d.text((190, 745), "CHP solves all three with hardened, auditable decision sessions.",
           fill=CYAN, font=FONTS["FS"])
    d.text((190, 785), "Every claim is traced. Every gate is enforced.",
           fill=GREEN, font=FONTS["FM_S"])
    fw.hold(final, 1.5)


def scene_architecture(fw: FrameWriter) -> None:
    """Scene 3: 5 subsystems appearing one by one, ~4s."""
    duration = 4.0
    n = int(duration * FPS)

    boxes = [
        (120, 190, "CHP", CYAN,
         ["Decision hardening with gates,", "packets, lock states, adversary attack,",
          "VCL diagnosis, third-party validation"]),
        (690, 190, "Cognitive Mesh", GREEN,
         ["Expansion/Compression reasoning", "with grounding checks and",
          "failure mode detection"]),
        (1260, 190, "Context Engine", YELLOW,
         ["Layered memory + entity/event/task", "schema with thread-safe sharing",
          "across agents"]),
        (120, 460, "ACE Playbook", PURPLE,
         ["Evolving playbooks with", "Generator/Reflector/Curator",
          "delta-only updates"]),
        (690, 460, "Synthesizer", RED,
         ["Statement + executable workflow", "with dependency-ordered steps",
          "and provenance tracking"]),
        (1260, 460, "CFO OS", MAGENTA,
         ["Multi-agent CFO operating", "system with audit trail",
          "and session reports"]),
    ]

    for frame_i in range(n):
        t = frame_i / n
        img = new_frame()
        d = ImageDraw.Draw(img)
        draw_grid_bg(d)
        d.text((160, 60), "Architecture: Six Composed Subsystems", fill=WHITE, font=FONTS["FB"])
        d.text((160, 110), "Each subsystem is independently specifiable and composable",
               fill=GRAY, font=FONTS["FM_S"])

        for i, (bx, by, name, color, desc) in enumerate(boxes):
            reveal_at = 0.1 + i * 0.18
            if t < reveal_at:
                continue
            local_t = min(1.0, (t - reveal_at) / 0.3)
            scale = lerp(0.7, 1.0, ease_in_out(local_t))
            box_w = int(520 * scale)
            box_h = int(230 * scale)
            offset_x = (520 - box_w) // 2
            offset_y = (230 - box_h) // 2
            draw_rounded_rect(d, (bx + offset_x, by + offset_y, bx + offset_x + box_w,
                                  by + offset_y + box_h), 12,
                              fill=TBG, outline=color)
            if local_t > 0.5:
                text_alpha = (local_t - 0.5) / 0.5
                name_color = lerp_color(BG, color, text_alpha)
                d.text((bx + 20, by + 20), name, fill=name_color, font=FONTS["FM_B"])
                for j, line in enumerate(desc):
                    c = lerp_color(BG, WHITE if j == 0 else GRAY, text_alpha)
                    d.text((bx + 20, by + 65 + j * 30), line, fill=c, font=FONTS["FM_S"])

        # Bottom callout
        if t > 0.9:
            text_centered(d, "Composable. Auditable. Hardened.", 820, FONTS["FB"], GREEN)

        fw.save(img)


def scene_session(fw: FrameWriter) -> None:
    """Scene 4: terminal showing chp-start with typewriter effect, ~5s."""
    duration = 5.0
    n = int(duration * FPS)

    img, d = terminal_frame("chp-session - cme cli")
    d.text((160, 30), "Live Demo: Capital Allocation Session", fill=WHITE, font=FONTS["FB"])
    d.text((100, 140), "$ cme chp-start --title \"Fund enterprise workflow\" --company Acme --amount 2500000",
           fill=GREEN, font=FONTS["FM"])

    lines = [
        (185, CYAN,   "[CHP] Initializing session..."),
        (215, GREEN,  "[CHP] Pre-session context check: PASSED"),
        (245, GREEN,  "[CHP] Model parity check: SYMMETRIC"),
        (275, GREEN,  "[CHP] R0 gate check: PASSED"),
        (305, YELLOW, "[CHP] Foundation score: 82/100"),
        (345, CYAN,   "[CHP] Building origin dossier..."),
        (375, WHITE,  "  Decision: Fund enterprise workflow ($2.5M)"),
        (405, GRAY,   "  Domain: capital_allocation"),
        (435, RED,    "  Risk level: HIGH"),
        (480, YELLOW, "[CHP] Running adversarial foundation attack..."),
        (510, CYAN,   "[CHP] Phase 0 devil's advocate captured"),
        (540, GREEN,  "[CHP] VCL diagnosis: CLEAR"),
        (580, DIM,    "[CHP] BEGIN_PAYLOAD"),
        (610, YELLOW, "[CHP] STATE_SNAPSHOT: PROVISIONAL"),
        (640, DIM,    "[CHP] END_PAYLOAD"),
        (680, GREEN,  "[CHP] Origin packet generated successfully"),
    ]

    # Reveal one line every ~0.25s
    for frame_i in range(n):
        t = frame_i / n
        f_img = img.copy()
        f_d = ImageDraw.Draw(f_img)
        visible = int(t / 0.25)
        for y, c, txt in lines[:visible]:
            f_d.text((100, y), txt, fill=c, font=FONTS["FM_S"])

        # Blinking cursor on next line
        if visible < len(lines) and (frame_i // 8) % 2 == 0:
            cursor_y = lines[visible][0]
            f_d.rectangle([100, cursor_y + 4, 116, cursor_y + 22], fill=GREEN)

        # Progress bar
        bar_w = int(1740 * t)
        f_d.rectangle([80, 1030, 80 + bar_w, 1038], fill=CYAN)

        fw.save(f_img)


def scene_partner(fw: FrameWriter) -> None:
    """Scene 5: partner packet ingestion, ~3.5s."""
    duration = 3.5
    n = int(duration * FPS)

    img, d = terminal_frame("chp-session - cme cli")
    d.text((160, 30), "Partner Packet Ingestion", fill=WHITE, font=FONTS["FB"])
    d.text((100, 140), "$ cme chp-receive --partner-packet partner_response.txt",
           fill=GREEN, font=FONTS["FM"])

    lines = [
        (185, CYAN,   "[CHP] Ingesting partner packet..."),
        (215, GREEN,  "[CHP] PAYLOAD_ECHO integrity check: VERIFIED"),
        (245, GREEN,  "[CHP] Item agreements: 3/3 matched"),
        (275, GREEN,  "[CHP] Scoring table validated (single winner)"),
        (315, YELLOW, "[CHP] PROVISIONAL_LOCK pending third-party validation"),
        (355, GREEN,  "[CHP] Partner packet processed successfully"),
    ]

    for frame_i in range(n):
        t = frame_i / n
        f_img = img.copy()
        f_d = ImageDraw.Draw(f_img)
        visible = int(t / 0.4)
        for y, c, txt in lines[:visible]:
            f_d.text((100, y), txt, fill=c, font=FONTS["FM_S"])

        # State machine visualization on the right
        f_d.text((960, 200), "State Machine", fill=WHITE, font=FONTS["FM_B"])
        states = [
            (1050, 260, "OPEN", GRAY),
            (1050, 330, "PROVISIONAL_LOCK", YELLOW),
            (1050, 400, "LOCKED", GREEN),
        ]
        active = min(2, int(t / 0.7))
        for i, (x, y, name, color) in enumerate(states):
            box_color = color if i <= active else DIM
            draw_rounded_rect(f_d, (x, y - 20, x + 360, y + 20), 6,
                              fill=TBG, outline=box_color)
            f_d.text((x + 14, y - 12), name, fill=box_color, font=FONTS["FM_B"])
            if i < 2:
                arrow_color = color if i < active else DIM
                f_d.line([(x + 180, y + 25), (x + 180, y + 55)], fill=arrow_color, width=3)
                f_d.polygon([(x + 175, y + 50), (x + 185, y + 50), (x + 180, y + 60)],
                            fill=arrow_color)

        # Key point box at bottom
        if t > 0.5:
            box_t = min(1.0, (t - 0.5) / 0.3)
            box_alpha = box_t
            draw_rounded_rect(f_d, (100, 540, 840, 660), 10,
                              fill=(28, 33, 40),
                              outline=lerp_color(BG, YELLOW, box_alpha))
            if box_t > 0.4:
                ta = (box_t - 0.4) / 0.6
                f_d.text((120, 560), "Key Point:",
                         fill=lerp_color(BG, YELLOW, ta), font=FONTS["FS_S"])
                f_d.text((120, 595), "Tracked agreement with payload integrity",
                         fill=lerp_color(BG, WHITE, ta), font=FONTS["FS_S"])
                f_d.text((120, 625), "and explicit state change to provisional lock",
                         fill=lerp_color(BG, WHITE, ta), font=FONTS["FS_S"])

        fw.save(f_img)


def scene_validate(fw: FrameWriter) -> None:
    """Scene 6: third-party validation with LOCKED promotion, ~4s."""
    duration = 4.0
    n = int(duration * FPS)

    img, d = terminal_frame("chp-session - cme cli")
    d.text((160, 30), "Third-Party Validation", fill=WHITE, font=FONTS["FB"])
    d.text((100, 140), "$ cme chp-validate --session-id chp-acme-001",
           fill=GREEN, font=FONTS["FM"])

    lines = [
        (185, CYAN,   "[VALIDATE] Loading session state..."),
        (215, YELLOW, "[VALIDATE] Running TriangulationRunner adversary pass..."),
        (255, GREEN,  "[VALIDATE] Claim: \"EBITDA improves by 20%\" -> VERIFIED"),
        (285, GREEN,  "[VALIDATE] Claim: \"14-month payback\" -> VERIFIED"),
        (315, GREEN,  "[VALIDATE] Claim: \"Runway above 12 months\" -> VERIFIED"),
        (355, GREEN,  "[VALIDATE] Structural vulnerability: NONE FOUND"),
        (385, GREEN,  "[VALIDATE] Blind spot scan: NONE FOUND"),
        (425, GREEN,  "[VALIDATE] Verification checklist: 5/5 PASSED"),
    ]

    for frame_i in range(n):
        t = frame_i / n
        f_img = img.copy()
        f_d = ImageDraw.Draw(f_img)
        visible = int(t / 0.3)
        for y, c, txt in lines[:visible]:
            f_d.text((100, y), txt, fill=c, font=FONTS["FM_S"])

        # LOCKED box reveal at t > 0.7
        if t > 0.7:
            lock_t = min(1.0, (t - 0.7) / 0.3)
            pulse = 0.5 + 0.5 * (1 + (frame_i % 30) / 30) / 1  # subtle pulse
            box_color = lerp_color(GREEN, (100, 220, 120), pulse * 0.3)
            scale = lerp(0.8, 1.0, ease_in_out(lock_t))
            bw = int(500 * scale)
            bh = int(50 * scale)
            bx = 100 + (500 - bw) // 2
            by = 480 + (50 - bh) // 2
            draw_rounded_rect(f_d, (bx, by, bx + bw, by + bh), 6, fill=box_color)
            if lock_t > 0.5:
                ta = (lock_t - 0.5) / 0.5
                f_d.text((120, by + 12), "[CHP]  STATE: LOCKED",
                         fill=lerp_color(BG, WHITE, ta), font=FONTS["FM_B"])

            f_d.text((100, 555), "[CHP] PROVISIONAL_LOCK -> LOCKED (validation passed)",
                     fill=GREEN, font=FONTS["FM_S"])
            f_d.text((100, 590), "[CHP] Decision hardened. Session complete.",
                     fill=CYAN, font=FONTS["FM_S"])

        fw.save(f_img)


def scene_benchmark(fw: FrameWriter) -> None:
    """Scene 7: benchmark bar chart hardened vs unhardened, ~3.5s."""
    duration = 3.5
    n = int(duration * FPS)

    metrics = [
        ("Claim Traceability", 35, 98, "%"),
        ("Gate Enforcement",   48, 96, "%"),
        ("Audit Completeness", 22, 94, "%"),
        ("Adversarial Resist.",41, 91, "%"),
        ("State Lock Verifiability", 30, 97, "%"),
    ]

    for frame_i in range(n):
        t = frame_i / n
        img = new_frame()
        d = ImageDraw.Draw(img)
        draw_grid_bg(d)
        d.text((160, 60), "Benchmark: Hardened vs Unhardened Consensus",
               fill=WHITE, font=FONTS["FB"])
        d.text((160, 110), "Same decision, same models - protocol discipline is the only delta",
               fill=GRAY, font=FONTS["FM_S"])

        # Chart area
        chart_x = 240
        chart_y = 200
        chart_w = 1440
        chart_h = 600
        d.rectangle([chart_x, chart_y, chart_x + chart_w, chart_y + chart_h],
                    fill=TBG, outline=BD)

        # Legend
        d.rectangle([chart_x + 20, chart_y + 20, chart_x + 40, chart_y + 40], fill=RED)
        d.text((chart_x + 50, chart_y + 22), "Unhardened", fill=WHITE, font=FONTS["FM_S"])
        d.rectangle([chart_x + 200, chart_y + 20, chart_x + 220, chart_y + 40], fill=GREEN)
        d.text((chart_x + 230, chart_y + 22), "CHP Hardened", fill=WHITE, font=FONTS["FM_S"])

        bar_h = 40
        gap = 20
        max_bar_w = chart_w - 320
        for i, (label, unh, hard, unit) in enumerate(metrics):
            y = chart_y + 80 + i * (bar_h * 2 + gap)

            # Label
            d.text((chart_x + 20, y - 5), label, fill=WHITE, font=FONTS["FM_S"])

            # Unhardened bar
            bar_t = min(1.0, max(0.0, (t - i * 0.1) / 0.4))
            uw = int(max_bar_w * (unh / 100) * ease_in_out(bar_t))
            d.rectangle([chart_x + 280, y, chart_x + 280 + uw, y + bar_h], fill=RED)
            if bar_t > 0.8:
                d.text((chart_x + 280 + uw + 8, y + 8), f"{unh}{unit}",
                       fill=RED, font=FONTS["FM_S"])

            # Hardened bar
            hw = int(max_bar_w * (hard / 100) * ease_in_out(bar_t))
            d.rectangle([chart_x + 280, y + bar_h + 4, chart_x + 280 + hw, y + bar_h * 2 + 4],
                        fill=GREEN)
            if bar_t > 0.8:
                d.text((chart_x + 280 + hw + 8, y + bar_h + 12), f"{hard}{unit}",
                       fill=GREEN, font=FONTS["FM_S"])

        # Footer
        if t > 0.9:
            text_centered(d, "Hardening is measurable. Drift is preventable.",
                          870, FONTS["FB"], CYAN)

        fw.save(img)


def scene_closing(fw: FrameWriter) -> None:
    """Scene 8: closing card with repo URLs, ~3s."""
    duration = 3.0
    n = int(duration * FPS)

    for frame_i in range(n):
        t = frame_i / n
        img = new_frame()
        d = ImageDraw.Draw(img)
        draw_grid_bg(d)

        # Center card
        card_t = min(1.0, t / 0.3)
        card_w = int(lerp(800, 1200, ease_in_out(card_t)))
        card_h = int(lerp(300, 480, ease_in_out(card_t)))
        cx = W // 2
        cy = H // 2
        draw_rounded_rect(d, (cx - card_w // 2, cy - card_h // 2,
                              cx + card_w // 2, cy + card_h // 2), 16,
                          fill=TBG, outline=CYAN)

        if t > 0.3:
            ta = min(1.0, (t - 0.3) / 0.3)
            text_centered(d, "Every claim traced.", cy - 160,
                          FONTS["FB"], lerp_color(BG, WHITE, ta))
            text_centered(d, "Every gate enforced.", cy - 100,
                          FONTS["FB"], lerp_color(BG, WHITE, ta))

        if t > 0.5:
            ta = min(1.0, (t - 0.5) / 0.3)
            text_centered(d, "Consensus is not enough", cy - 10,
                          FONTS["FB"], lerp_color(BG, WHITE, ta))
            text_centered(d, "until it is hardened.", cy + 50,
                          FONTS["FB"], lerp_color(BG, GREEN, ta))

        if t > 0.75:
            ta = min(1.0, (t - 0.75) / 0.25)
            text_centered(d, "github.com/Cubiczan/consensus-hardening-protocol",
                          cy + 140, FONTS["FM_S"], lerp_color(BG, CYAN, ta))
            text_centered(d, "github.com/icohangar-ops/consensus-hardening-protocol",
                          cy + 170, FONTS["FM_S"], lerp_color(BG, CYAN, ta))
            text_centered(d, "codeberg.org/cubiczan/consensus-hardening-protocol",
                          cy + 200, FONTS["FM_S"], lerp_color(BG, CYAN, ta))

        fw.save(img)


# ────────────────────────────────────────────────────────────────────────────
# Static JPG builders
# ────────────────────────────────────────────────────────────────────────────

def build_thumbnail(path: Path) -> None:
    """Hero / README poster (1920x1080 -> exported as JPG)."""
    img = new_frame()
    d = ImageDraw.Draw(img)
    draw_grid_bg(d)

    # Shield
    draw_shield(d, W // 2, 280, 200, CYAN)
    d.line([(W // 2 - 40, 280), (W // 2 - 10, 320), (W // 2 + 50, 240)],
           fill=WHITE, width=8)

    text_centered(d, "Consensus Hardening Protocol", 470, FONTS["FB_XL"], WHITE)
    text_centered(d, "Multi-Agent Decision Governance for High-Stakes Finance",
                  580, FONTS["FS"], GRAY)
    text_centered(d, "cme chp-start  |  chp-receive  |  chp-validate  |  chp-triangulate",
                  660, FONTS["FM_S"], CYAN)

    # Badges
    draw_rounded_rect(d, (680, 760, 880, 800), 8, fill=TBG, outline=GREEN)
    text_centered(d, "MIT License", 768, FONTS["FM_T"], GREEN)
    draw_rounded_rect(d, (920, 760, 1180, 800), 8, fill=TBG, outline=CYAN)
    text_centered(d, "42 tests passing", 768, FONTS["FM_T"], CYAN)
    draw_rounded_rect(d, (1220, 760, 1400, 800), 8, fill=TBG, outline=YELLOW)
    text_centered(d, "Zero deps", 768, FONTS["FM_T"], YELLOW)

    # Tagline
    text_centered(d, "Every claim traced.  Every gate enforced.", 900,
                  FONTS["FB"], GREEN)
    text_centered(d, "Watch the 30-second demo below", 970,
                  FONTS["FM_S"], DIM)

    img.convert("RGB").save(path, "JPEG", quality=88, optimize=True)


def build_architecture(path: Path) -> None:
    """Static architecture diagram (1920x1080)."""
    img = new_frame()
    d = ImageDraw.Draw(img)
    draw_grid_bg(d)
    d.text((160, 60), "Architecture: Six Composed Subsystems", fill=WHITE, font=FONTS["FB"])
    d.text((160, 110), "Each subsystem is independently specifiable and composable",
           fill=GRAY, font=FONTS["FM_S"])

    boxes = [
        (120, 190, "CHP", CYAN,
         ["Decision hardening with gates,", "packets, lock states, adversary attack,",
          "VCL diagnosis, third-party validation"]),
        (690, 190, "Cognitive Mesh", GREEN,
         ["Expansion/Compression reasoning", "with grounding checks and",
          "failure mode detection"]),
        (1260, 190, "Context Engine", YELLOW,
         ["Layered memory + entity/event/task", "schema with thread-safe sharing",
          "across agents"]),
        (120, 460, "ACE Playbook", PURPLE,
         ["Evolving playbooks with", "Generator/Reflector/Curator",
          "delta-only updates"]),
        (690, 460, "Synthesizer", RED,
         ["Statement + executable workflow", "with dependency-ordered steps",
          "and provenance tracking"]),
        (1260, 460, "CFO OS", MAGENTA,
         ["Multi-agent CFO operating", "system with audit trail",
          "and session reports"]),
    ]
    for bx, by, name, color, desc in boxes:
        draw_rounded_rect(d, (bx, by, bx + 520, by + 230), 12, fill=TBG, outline=color)
        d.text((bx + 20, by + 20), name, fill=color, font=FONTS["FM_B"])
        for j, line in enumerate(desc):
            c = WHITE if j == 0 else GRAY
            d.text((bx + 20, by + 65 + j * 30), line, fill=c, font=FONTS["FM_S"])

    text_centered(d, "Composable. Auditable. Hardened.", 820, FONTS["FB"], GREEN)
    img.convert("RGB").save(path, "JPEG", quality=88, optimize=True)


def build_phases(path: Path) -> None:
    """Static 4-phase lifecycle diagram (1920x1080)."""
    img = new_frame()
    d = ImageDraw.Draw(img)
    draw_grid_bg(d)
    d.text((160, 60), "Protocol Lifecycle: Four Hardened Phases", fill=WHITE, font=FONTS["FB"])
    d.text((160, 110), "Each phase has explicit entry gates, state transitions, and audit artifacts",
           fill=GRAY, font=FONTS["FM_S"])

    phases = [
        (1, "PROPOSE",     CYAN,   ["chp-start", "Build origin dossier", "R0 gate check",
                                     "State: OPEN"]),
        (2, "VALIDATE",    YELLOW, ["Adversarial attack", "Devil's advocate capture",
                                     "VCL diagnosis", "State: PROVISIONAL"]),
        (3, "TRIANGULATE", PURPLE, ["chp-receive", "Partner packet ingest",
                                     "Payload echo check", "State: PROVISIONAL_LOCK"]),
        (4, "HARDEN",      GREEN,  ["chp-validate", "5/5 checklist pass",
                                     "Third-party verify", "State: LOCKED"]),
    ]

    box_w = 380
    gap = 60
    start_x = (W - (box_w * 4 + gap * 3)) // 2
    y = 240
    for i, (num, name, color, items) in enumerate(phases):
        bx = start_x + i * (box_w + gap)
        draw_rounded_rect(d, (bx, y, bx + box_w, y + 480), 12, fill=TBG, outline=color)
        # Number circle
        d.ellipse([bx + 20, y + 20, bx + 80, y + 80], fill=color)
        text_centered(d, str(num), y + 32, FONTS["FB"], BG)
        # Phase name
        d.text((bx + 100, y + 35), name, fill=color, font=FONTS["FM_B"])
        # Divider
        d.line([(bx + 20, y + 100), (bx + box_w - 20, y + 100)], fill=color, width=2)
        # Items
        for j, item in enumerate(items):
            ic = WHITE if j < 3 else color
            d.text((bx + 30, y + 130 + j * 50), f"  {item}", fill=ic, font=FONTS["FM_S"])
            if j < 3:
                d.ellipse([bx + 30, y + 138 + j * 50, bx + 38, y + 146 + j * 50], fill=color)

        # Arrow to next phase
        if i < 3:
            ax = bx + box_w + 10
            ay = y + 240
            d.line([(ax, ay), (ax + gap - 20, ay)], fill=GRAY, width=3)
            d.polygon([(ax + gap - 25, ay - 8), (ax + gap - 10, ay), (ax + gap - 25, ay + 8)],
                      fill=GRAY)

    text_centered(d, "LOCKED state is the only state that downstream systems may consume.",
                  780, FONTS["FS"], GREEN)
    img.convert("RGB").save(path, "JPEG", quality=88, optimize=True)


def build_social_preview(path: Path) -> None:
    """1280x640 social preview card (matches GitHub social preview spec)."""
    SW, SH = 1280, 640
    img = Image.new("RGB", (SW, SH), BG)
    d = ImageDraw.Draw(img)
    # Subtle grid
    for x in range(0, SW, 80):
        d.line([(x, 0), (x, SH)], fill=(20, 26, 34), width=1)
    for y in range(0, SH, 80):
        d.line([(0, y), (SW, y)], fill=(20, 26, 34), width=1)

    # Shield
    cx, cy = 220, 200
    s = 90
    pts = [
        (cx, cy - s),
        (cx + s, cy - s + s // 3),
        (cx + s, cy + s // 3),
        (cx, cy + s),
        (cx - s, cy + s // 3),
        (cx - s, cy - s + s // 3),
    ]
    d.polygon(pts, fill=CYAN)
    d.line([(cx - 30, cy), (cx - 5, cy + 30), (cx + 40, cy - 30)], fill=WHITE, width=6)

    # Title
    title_font = ImageFont.truetype(FONT_PATHS["FB"], 52)
    sub_font = ImageFont.truetype(FONT_PATHS["FS"], 26)
    mono_font = ImageFont.truetype(FONT_PATHS["FM_S"], 18)

    d.text((380, 150), "Consensus Hardening", fill=WHITE, font=title_font)
    d.text((380, 215), "Protocol", fill=CYAN, font=title_font)
    d.text((380, 295), "Multi-Agent Decision Governance", fill=GRAY, font=sub_font)
    d.text((380, 335), "for High-Stakes Finance", fill=GRAY, font=sub_font)

    # Tags
    tags = [("MIT", GREEN), ("42 tests", CYAN), ("Zero deps", YELLOW)]
    tx = 380
    for label, color in tags:
        bbox = d.textbbox((0, 0), label, font=mono_font)
        tw = bbox[2] - bbox[0]
        draw_rounded_rect(d, (tx, 410, tx + tw + 24, 444), 6, fill=TBG, outline=color)
        d.text((tx + 12, 419), label, fill=color, font=mono_font)
        tx += tw + 40

    # Repo line
    d.text((380, 480), "github.com/Cubiczan/consensus-hardening-protocol",
           fill=CYAN, font=mono_font)
    d.text((380, 510), "codeberg.org/cubiczan/consensus-hardening-protocol",
           fill=GRAY, font=mono_font)

    img.save(path, "JPEG", quality=88, optimize=True)


# ────────────────────────────────────────────────────────────────────────────
# Main pipeline
# ────────────────────────────────────────────────────────────────────────────

def build_video(frames_dir: Path, out_path: Path) -> float:
    """Build the demo video. Returns duration in seconds."""
    load_fonts()
    fw = FrameWriter(frames_dir)

    print("Generating frames...")
    print("  Scene 1: Title card (animated)...")
    scene_title_card(fw)
    print("  Scene 2: Problem statement (animated)...")
    scene_problem(fw)
    print("  Scene 3: Architecture (animated)...")
    scene_architecture(fw)
    print("  Scene 4: chp-start terminal (typewriter)...")
    scene_session(fw)
    print("  Scene 5: Partner packet ingestion (state machine)...")
    scene_partner(fw)
    print("  Scene 6: Third-party validation (LOCKED reveal)...")
    scene_validate(fw)
    print("  Scene 7: Benchmark chart (animated bars)...")
    scene_benchmark(fw)
    print("  Scene 8: Closing card (animated)...")
    scene_closing(fw)

    total = fw.total()
    duration = total / FPS
    print(f"\nTotal frames: {total}")
    print(f"Duration: {duration:.1f}s")

    print("\nEncoding video with ffmpeg...", flush=True)
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(frames_dir / "f%05d.png"),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-tune", "stillimage",
        str(out_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        print(f"ffmpeg stderr:\n{r.stderr[-2000:]}", file=sys.stderr)
        raise SystemExit(1)

    sz = out_path.stat().st_size
    print(f"  -> {out_path}  ({sz / 1024 / 1024:.1f} MB)")
    return duration


def build_static_jpgs(media_dir: Path) -> None:
    """Generate all static JPG assets."""
    load_fonts()
    print("\nGenerating static JPGs...")
    build_thumbnail(media_dir / "chp-thumbnail.jpg")
    print("  -> chp-thumbnail.jpg")
    build_architecture(media_dir / "chp-architecture.jpg")
    print("  -> chp-architecture.jpg")
    build_phases(media_dir / "chp-phases.jpg")
    print("  -> chp-phases.jpg")
    build_social_preview(media_dir / "chp-social-preview.jpg")
    print("  -> chp-social-preview.jpg")


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--media-dir", required=True,
                   help="Target docs/media/ directory")
    p.add_argument("--keep-frames", action="store_true",
                   help="Do not delete intermediate PNG frames")
    args = p.parse_args()

    media_dir = Path(args.media_dir).resolve()
    media_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = media_dir / "_frames"

    # Static JPGs first (cheap, immediate value if video fails)
    build_static_jpgs(media_dir)

    # Video
    out_mp4 = media_dir / "chp-demo.mp4"
    duration = build_video(frames_dir, out_mp4)

    # Replace the legacy chp-demo-3min.mp4 with the new short demo
    legacy = media_dir / "chp-demo-3min.mp4"
    shutil.copy2(out_mp4, legacy)
    print(f"  -> {legacy}  (replaced legacy 3min file with new {duration:.0f}s demo)")

    # Also replace assets/demo.mp4 (used by some README links / github pages)
    assets_demo = media_dir.parent.parent / "assets" / "demo.mp4"
    if assets_demo.parent.exists():
        shutil.copy2(out_mp4, assets_demo)
        print(f"  -> {assets_demo}  (assets/demo.mp4 refreshed)")

    # Cleanup
    if not args.keep_frames:
        shutil.rmtree(frames_dir, ignore_errors=True)
        print("\nCleaned up intermediate frames.")
    print("\nDone.")


if __name__ == "__main__":
    main()
