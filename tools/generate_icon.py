"""Generate app icon: oscilloscope waveform on dark rounded background.

Usage: python tools/generate_icon.py
Output: resources/app_icon.ico  (16~256px, 6 resolutions)
"""
import math
import os
from PIL import Image, ImageDraw

SIZES = [16, 32, 48, 64, 128, 256]
OUTPUT = os.path.join(os.path.dirname(__file__), "..", "resources", "app_icon.ico")

BG = (22, 27, 44)
GRID = (38, 43, 60)
WAVE = (0, 229, 180)
DOT = (80, 220, 255)

size = 256
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

r = max(3, size // 6)
d.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=r, fill=BG)

m = max(2, size // 10)
lw = max(1, size // 128)
for i in range(1, 5):
    y = int(m + i * (size - 2 * m) / 5)
    d.line([(m, y), (size - m - 1, y)], fill=GRID, width=lw)

pad = max(3, size // 7)
w = size - 2 * pad
hr = int(size * 0.35)
pts = []
for i in range(w + 1):
    t = i / w
    env = 1 - 0.55 * (2 * t - 1) ** 2
    wave = math.sin(t * 2.5 * math.pi + 0.4)
    pts.append((pad + i, int(size // 2 - wave * env * hr // 2)))

ww = max(2, size // 48)
for i in range(len(pts) - 1):
    d.line([pts[i], pts[i + 1]], fill=WAVE, width=ww)

pi = int(w * 0.35)
if pi < len(pts):
    px, py = pts[pi]
    dr = max(1.5, size / 22)
    d.ellipse([(px - dr, py - dr), (px + dr, py + dr)], fill=DOT)

img.save(OUTPUT, format="ICO", sizes=[(s, s) for s in SIZES])
print(f"Icon saved: {OUTPUT}")
print(f"  Size: {os.path.getsize(OUTPUT)} bytes  |  Resolutions: {SIZES}")
