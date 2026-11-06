"""Build the print files for the business card (services / QR side).

    python3 build.py

Fonts (Jura 400/700, Open Sans 400, all SIL Open Font License) are pulled from
Google Fonts into ./fonts on first run. Outputs land next to this script.
"""
import os
import re
import urllib.request

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.environ.get("CARD_FONT_DIR", os.path.join(HERE, "fonts"))
FONTS = {"Jura": (400, 700), "Open+Sans": (400,)}


def fetch_fonts():
    os.makedirs(FONT_DIR, exist_ok=True)
    for family, weights in FONTS.items():
        for w in weights:
            dest = os.path.join(FONT_DIR, f"{family.replace('+', '')}-{w}.ttf")
            if os.path.exists(dest):
                continue
            css_url = f"https://fonts.googleapis.com/css2?family={family}:wght@{w}"
            # an old user agent makes Google Fonts serve plain TTF
            req = urllib.request.Request(css_url, headers={"User-Agent": "Wget/1.0"})
            css = urllib.request.urlopen(req).read().decode()
            ttf = re.search(r"url\((https://[^)]+\.ttf)\)", css).group(1)
            urllib.request.urlretrieve(ttf, dest)


def main():
    fetch_fonts()
    import cardlib

    title = "Jake's Car Detailing business card (back)"
    pdf_bleed = os.path.join(HERE, "business-card-back_print-bleed.pdf")
    tmp = pdf_bleed + ".tmp"
    cardlib.build_pdf(tmp, cardlib.TEXT, bleed=cardlib.BLEED, title=title)

    # All text is outlined, so drop the unused Helvetica that reportlab declares
    # by default. Print preflight checks flag it as an unembedded font otherwise.
    doc = pymupdf.open(tmp)
    page = doc[0]
    for xref in page.get_contents():
        stream = doc.xref_stream(xref).replace(b"BT /F1 12 Tf 14.4 TL ET", b"")
        doc.update_stream(xref, stream)
    doc.xref_set_key(page.xref, "Resources/Font", "null")
    doc.save(pdf_bleed, garbage=4, deflate=True)
    doc.close()
    os.remove(tmp)

    doc = pymupdf.open(pdf_bleed)
    page = doc[0]
    # 600 dpi PNG with bleed (3.75 x 2.25 in -> 2250 x 1350)
    pix = page.get_pixmap(dpi=600, alpha=False)
    pix.set_dpi(600, 600)
    pix.save(os.path.join(HERE, "business-card-back_600dpi-bleed.png"))
    # 600 dpi PNG at trim size (3.5 x 2 in -> 2100 x 1200), same framing as the original
    pix = page.get_pixmap(dpi=600, alpha=False, clip=page.trimbox)
    pix.set_dpi(600, 600)
    pix.save(os.path.join(HERE, "business-card-back_600dpi.png"))


if __name__ == "__main__":
    main()
