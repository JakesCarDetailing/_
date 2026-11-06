"""Vector rebuild of the Jake's Car Detailing business card (services / QR side).

All layout numbers are in "design px": the original 1050 x 600 artwork at
300 dpi (3.5 x 2 in trim). Everything is drawn as vector paths, text included
(outlined from the font files), so the PDF prints sharp at any size and never
depends on the printer having the fonts installed.
"""
import io
import math
import os

import segno
import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas as rl_canvas

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.environ.get("CARD_FONT_DIR", os.path.join(HERE, "fonts"))

DPI = 300
TRIM_W, TRIM_H = 1050, 600          # 3.5 x 2 in
BLEED = 37.5                        # 0.125 in per side
PX_TO_PT = 72 / DPI

BLACK = (0, 0, 0)
WHITE = (1, 1, 1)
BLUE = (5 / 255, 102 / 255, 237 / 255)   # #0566ED, sampled from the original

QR_URL = "https://qrco.de/bh5mP5"


# --------------------------------------------------------------------------- fonts
class _PathPen(BasePen):
    """Draws font-unit outlines into a reportlab path, transformed to design px."""

    def __init__(self, glyphset, path, ox, oy, scale):
        super().__init__(glyphset)
        self.path, self.ox, self.oy, self.s = path, ox, oy, scale

    def _t(self, p):
        return self.ox + p[0] * self.s, self.oy - p[1] * self.s

    def _moveTo(self, p):
        self.path.moveTo(*self._t(p))

    def _lineTo(self, p):
        self.path.lineTo(*self._t(p))

    def _curveToOne(self, p1, p2, p3):
        self.path.curveTo(*self._t(p1), *self._t(p2), *self._t(p3))

    def _qCurveToOne(self, p1, p2):
        # exact quadratic -> cubic elevation
        p0 = self._getCurrentPoint()
        c1 = (p0[0] + 2 / 3 * (p1[0] - p0[0]), p0[1] + 2 / 3 * (p1[1] - p0[1]))
        c2 = (p2[0] + 2 / 3 * (p1[0] - p2[0]), p2[1] + 2 / 3 * (p1[1] - p2[1]))
        self._curveToOne(c1, c2, p2)

    def _closePath(self):
        self.path.close()


class Font:
    _cache = {}

    def __new__(cls, name):
        if name not in cls._cache:
            self = super().__new__(cls)
            path = os.path.join(FONT_DIR, name + ".ttf")
            self.tt = TTFont(path)
            self.gs = self.tt.getGlyphSet()
            self.order = self.tt.getGlyphOrder()
            self.upem = self.tt["head"].unitsPerEm
            self.hb = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
            cls._cache[name] = self
        return cls._cache[name]

    def layout(self, text, size, tracking=0.0):
        """Shaped glyphs (with kerning) as (glyph_name, dx, dy) in design px."""
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"kern": True, "liga": True})
        s = size / self.upem
        x, out = 0.0, []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            out.append((self.order[info.codepoint], x + pos.x_offset * s, -pos.y_offset * s))
            x += pos.x_advance * s + tracking
        return out

    def ink_bbox(self, text, size, tracking=0.0):
        """Ink box relative to the baseline origin, y down: (l, t, r, b)."""
        s = size / self.upem
        l = t = math.inf
        r = b = -math.inf
        for name, dx, dy in self.layout(text, size, tracking):
            bp = BoundsPen(self.gs)
            self.gs[name].draw(bp)
            if bp.bounds is None:
                continue
            x0, y0, x1, y1 = bp.bounds
            l, r = min(l, dx + x0 * s), max(r, dx + x1 * s)
            t, b = min(t, dy - y1 * s), max(b, dy - y0 * s)
        return l, t, r, b

    def add_to_path(self, path, text, x, baseline, size, tracking=0.0):
        s = size / self.upem
        for name, dx, dy in self.layout(text, size, tracking):
            self.gs[name].draw(_PathPen(self.gs, path, x + dx, baseline + dy, s))


# --------------------------------------------------------------------------- layout
# Each line: font file, size (px), tracking (px), left x of the pen origin, baseline y.
# Values come from fit.py, which matches every line against the original artwork.
TEXT = [
    # text, font, size, tracking, x, baseline
    ("Services", "Jura-700", 61.768, -0.774, 83.815, 102.100),
    ("Ceramic Coating", "Jura-400", 35.017, 0.407, 82.456, 157.751),
    ("Paint Correction", "Jura-400", 32.012, -0.298, 83.747, 201.100),
    ("Interior & Exterior", "Jura-400", 33.283, 0.025, 80.088, 243.834),
    ("Detailing", "Jura-400", 33.646, -0.157, 79.841, 288.985),
    ("Contact", "Jura-700", 60.770, -0.341, 80.262, 402.940),
    ("(877) 552-8664", "Jura-400", 36.088, -0.088, 80.291, 462.129),
    ("info@jakescardetailing.ca", "Jura-400", 31.337, -0.014, 80.241, 504.873),
    ("_jakescardetailing", "Jura-400", 31.337, -0.017, 79.973, 541.873),
    ("Scan Me", "OpenSans-400", 60.917, 0.395, 633.456, 503.201),
]

UNDERLINES = [  # x0, y0, x1, y1
    (84.02, 104.96, 350.63, 108.09),   # Services
    (80.15, 406.23, 321.59, 409.35),   # Contact
]

QR_BOX = (573.14, 60.28, 360.7)  # x, y, size (square)
QR_BOX_RADIUS = 10.0
QR_QUIET_MODULES = 3             # blue margin around the code, in modules

IG_CENTER = (369.1, 531.7)
IG_OUTER = 26.0
IG_STROKE = 2.35
IG_CORNER = 6.5                 # corner radius of the stroke centerline
IG_RING_R = 5.5                 # ring radius (stroke centerline)
IG_DOT = (6.95, -6.85, 1.4)     # offset from center, radius


# --------------------------------------------------------------------------- drawing
def qr_matrix():
    # Same settings as the original code (version 2-L, mask 3, UTF-8 ECI), which
    # reproduces it module for module.
    q = segno.make_qr(QR_URL, error="l", version=2, mask=3, eci=True,
                      encoding="utf-8", boost_error=False)
    return [list(row) for row in q.matrix]


def _fill(c, rgb):
    c.setFillColor(Color(*rgb))


def draw_card(c, text_lines, bleed=BLEED, only=None):
    """Draw onto a reportlab canvas whose page is (TRIM + 2*bleed) design px."""
    page_h = (TRIM_H + 2 * bleed) * PX_TO_PT
    c.saveState()
    # design px, origin at trim top-left, y down
    c.translate(bleed * PX_TO_PT, page_h - bleed * PX_TO_PT)
    c.scale(PX_TO_PT, -PX_TO_PT)

    # background runs past the trim into the bleed
    _fill(c, BLACK)
    c.rect(-bleed, -bleed, TRIM_W + 2 * bleed, TRIM_H + 2 * bleed, stroke=0, fill=1)

    want = (lambda k: True) if only is None else (lambda k: k in only)

    if want("qr"):
        bx, by, bs = QR_BOX
        _fill(c, BLUE)
        c.roundRect(bx, by, bs, bs, QR_BOX_RADIUS, stroke=0, fill=1)
        m = qr_matrix()
        n = len(m)
        mod = bs / (n + 2 * QR_QUIET_MODULES)
        ox = bx + QR_QUIET_MODULES * mod
        oy = by + QR_QUIET_MODULES * mod
        _fill(c, WHITE)
        p = c.beginPath()
        # merge horizontal runs so adjacent modules never show hairline seams
        for r, row in enumerate(m):
            col = 0
            while col < n:
                if row[col]:
                    start = col
                    while col < n and row[col]:
                        col += 1
                    p.rect(ox + start * mod, oy + r * mod, (col - start) * mod, mod)
                else:
                    col += 1
        c.drawPath(p, stroke=0, fill=1, fillMode=1)  # nonzero

    _fill(c, WHITE)
    if want("underlines"):
        for x0, y0, x1, y1 in UNDERLINES:
            c.rect(x0, y0, x1 - x0, y1 - y0, stroke=0, fill=1)

    if want("instagram"):
        cx, cy = IG_CENTER
        c.setStrokeColor(Color(*WHITE))
        c.setLineWidth(IG_STROKE)
        side = IG_OUTER - IG_STROKE
        c.roundRect(cx - side / 2, cy - side / 2, side, side, IG_CORNER, stroke=1, fill=0)
        c.circle(cx, cy, IG_RING_R, stroke=1, fill=0)
        dx, dy, dr = IG_DOT
        c.circle(cx + dx, cy + dy, dr, stroke=0, fill=1)

    for i, (text, font, size, tracking, x, baseline) in enumerate(text_lines):
        if not want(("text", i)) and not want("text"):
            continue
        p = c.beginPath()
        Font(font).add_to_path(p, text, x, baseline, size, tracking)
        c.drawPath(p, stroke=0, fill=1, fillMode=1)  # nonzero winding keeps overlaps solid

    c.restoreState()


def build_pdf(path_or_buf, text_lines, bleed=BLEED, only=None, title=None):
    w = (TRIM_W + 2 * bleed) * PX_TO_PT
    h = (TRIM_H + 2 * bleed) * PX_TO_PT
    c = rl_canvas.Canvas(path_or_buf, pagesize=(w, h), pageCompression=1)
    if title:
        c.setTitle(title)
        c.setAuthor("Jake's Car Detailing")
    if bleed:
        b = bleed * PX_TO_PT
        c.setBleedBox((0, 0, w, h))
        c.setTrimBox((b, b, w - b, h - b))
    draw_card(c, text_lines, bleed=bleed, only=only)
    c.showPage()
    c.save()


def pdf_bytes(text_lines, bleed=BLEED, only=None):
    buf = io.BytesIO()
    build_pdf(buf, text_lines, bleed=bleed, only=only)
    return buf.getvalue()
