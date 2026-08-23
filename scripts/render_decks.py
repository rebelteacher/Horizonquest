"""Render each starter .pptx deck into per-slide PNGs + a manifest.json.
Output: /app/frontend/public/decks/img/<deck>/slide-<n>.png
Manifest maps deck key -> ordered list of image paths (served statically).
"""
import glob, json, os, subprocess, tempfile

DECKS_DIR = "/app/frontend/public/decks"
IMG_DIR = os.path.join(DECKS_DIR, "img")
os.makedirs(IMG_DIR, exist_ok=True)

manifest = {}
for pptx in sorted(glob.glob(os.path.join(DECKS_DIR, "*.pptx"))):
    key = os.path.splitext(os.path.basename(pptx))[0]  # e.g. horizonquest_email_block1
    out = os.path.join(IMG_DIR, key)
    os.makedirs(out, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmp, pptx],
                       check=True, timeout=180, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pdf = os.path.join(tmp, key + ".pdf")
        subprocess.run(["pdftoppm", "-png", "-r", "110", pdf, os.path.join(out, "slide")],
                       check=True, timeout=180)
    pngs = sorted(glob.glob(os.path.join(out, "slide*.png")))
    manifest[key] = [f"/decks/img/{key}/{os.path.basename(p)}" for p in pngs]
    print(f"{key}: {len(pngs)} slides")

with open(os.path.join(IMG_DIR, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)
print("Wrote manifest.json")
