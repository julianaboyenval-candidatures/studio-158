#!/usr/bin/env python3
"""Retouche naturelle d'une photo pour Instagram (4:5, 1080x1350).

Usage :
  retouche.py entree.jpg sortie.jpg [--centre X Y] [--zoom Z] [--lumiere L] [--rotation R]

  --centre X Y   centre du sujet en fraction de l'image (0..1), défaut 0.5 0.5
  --zoom Z       1.0 = le plus grand cadre 4:5 possible ; 1.3 = 30 % plus serré
  --lumiere L    ajustement de luminosité manuel (ex. 1.08), sinon automatique
  --rotation R   degrés (sens inverse des aiguilles), pour redresser

Principes (cf. voix-marque.md) : couleur du vernis fidèle, fond blanc vraiment blanc,
pas de lissage de la peau. Corrections douces seulement.
"""
import argparse, sys
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageStat

W, H = 1080, 1350


def crop_45(img, cx, cy, zoom):
    w, h = img.size
    ch = min(h, w * 5 / 4) / max(zoom, 1.0)
    cw = ch * 4 / 5
    left = min(max(cx * w - cw / 2, 0), w - cw)
    top = min(max(cy * h - ch / 2, 0), h - ch)
    return img.crop((round(left), round(top), round(left + cw), round(top + ch)))


def balance_blancs(img):
    """Corrige une dominante légère en prenant les pixels clairs (le fond) comme référence de gris."""
    small = img.resize((200, int(200 * img.height / img.width)))
    px = [p for p in small.getdata() if sum(p) > 600]  # zones claires
    if len(px) < 200:
        return img
    r, g, b = (sum(c[i] for c in px) / len(px) for i in range(3))
    m = (r + g + b) / 3
    gains = [m / r, m / g, m / b]
    if max(abs(x - 1) for x in gains) < 0.015:
        return img
    gains = [1 + max(min(x - 1, 0.08), -0.08) for x in gains]  # au plus ±8 %
    chans = [c.point(lambda v, k=k: min(255, round(v * k))) for c, k in zip(img.split(), gains)]
    return Image.merge("RGB", chans)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("src"); a.add_argument("dst")
    a.add_argument("--centre", nargs=2, type=float, default=[0.5, 0.5])
    a.add_argument("--zoom", type=float, default=1.0)
    a.add_argument("--lumiere", type=float)
    a.add_argument("--rotation", type=float, default=0)
    o = a.parse_args()

    img = ImageOps.exif_transpose(Image.open(o.src)).convert("RGB")
    if o.rotation:
        img = img.rotate(o.rotation, resample=Image.BICUBIC, expand=False)
    img = crop_45(img, o.centre[0], o.centre[1], o.zoom).resize((W, H), Image.LANCZOS)

    img = balance_blancs(img)
    img = ImageOps.autocontrast(img, cutoff=(0.3, 0.3), preserve_tone=True)
    lum = ImageStat.Stat(img.convert("L")).mean[0]
    k = o.lumiere or (min(1.15, 128 / lum) if lum < 115 else 1.0)
    if abs(k - 1) > 0.01:
        img = ImageEnhance.Brightness(img).enhance(k)
    img = ImageEnhance.Contrast(img).enhance(1.04)
    img = ImageEnhance.Color(img).enhance(1.03)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.6, percent=55, threshold=3))

    img.save(o.dst, "JPEG", quality=90, optimize=True, progressive=True)
    print(f"ok {o.dst} {W}x{H} luminosite_moyenne={lum:.0f} gain={k:.2f}")


if __name__ == "__main__":
    sys.exit(main())
