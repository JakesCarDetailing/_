import base64, io, os, re, sys
from PIL import Image

root = "/home/user/_"
SCRATCH = "/tmp/claude-0/-home-user--/073a4458-482e-5422-8127-385fb17c2419/scratchpad"
out = os.path.join(SCRATCH, "jakes-bundle.html")
MAXDIM, Q = 1500, 80

html = open(os.path.join(root, "index.html"), encoding="utf-8").read()
css  = open(os.path.join(root, "css/styles.css"), encoding="utf-8").read()
js   = open(os.path.join(root, "js/script.js"), encoding="utf-8").read()

# The lightbox reads the anchor's href, forcing every gallery photo to be embedded
# twice. Read it off the thumbnail instead so each photo is inlined once.
js_patched = js.replace(
    "lightboxImg.src = item.getAttribute('href');",
    "lightboxImg.src = item.querySelector('img').src;")
assert js_patched != js, "lightbox src line not found"
js = js_patched

html, n = re.subn(r'(<a class="gallery-item[^"]*")\s+href="images/[^"]+"',
                  r'\1 href="#gallery"', html)
print(f"de-duplicated {n} gallery lightbox links")

html = html.replace('<link rel="stylesheet" href="css/styles.css">',
                    "<style>\n" + css + "\n</style>")
html = html.replace('<script src="js/script.js"></script>',
                    "<script>\n" + js + "\n</script>")

def datauri(rel):
    im = Image.open(os.path.join(root, rel))
    im.thumbnail((MAXDIM, MAXDIM), Image.LANCZOS)
    buf = io.BytesIO()
    if rel.lower().endswith(".png"):
        im.save(buf, "PNG", optimize=True); mime = "image/png"
    else:
        im.convert("RGB").save(buf, "JPEG", quality=Q, optimize=True, progressive=True)
        mime = "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(buf.getvalue()).decode()}", buf.tell()

refs = sorted(set(re.findall(r'(?:src|href)="(images/[^"]+)"', html)))
total = 0
for rel in refs:
    uri, size = datauri(rel)
    total += size
    html = html.replace(f'"{rel}"', f'"{uri}"')

leftover = re.findall(r'(?:src|href)="(?!data:|https?:|tel:|sms:|mailto:|#)([^"]+)"', html)
if leftover:
    print("WARNING unresolved local refs:", set(leftover), file=sys.stderr)

head_end = html.index('<a class="skip-link"')
doc = ('<!doctype html>\n<html lang="en">\n<head>\n' + html[:head_end].strip()
       + "\n</head>\n<body>\n" + html[head_end:].strip() + "\n</body>\n</html>\n")
open(out, "w", encoding="utf-8").write(doc)
print(f"inlined {len(refs)} images ({total/1e6:.2f} MB compressed) -> {os.path.getsize(out)/1e6:.2f} MB bundle")
