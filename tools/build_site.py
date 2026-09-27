"""Собирает сайт для Netlify в папку site/ (и site.zip в export/)."""
import os, shutil, zipfile

URL = "https://antonisonya.netlify.app"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")

page = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
head = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Антон и Соня приглашают на роспись 14 ноября 2026 года в 15:00, Ростов-на-Дону.">
<meta name="theme-color" content="#EDE6DA">
<meta property="og:type" content="website">
<meta property="og:url" content="{URL}/">
<meta property="og:title" content="Антон и Соня · 14.11.2026">
<meta property="og:description" content="Приглашение на роспись. Суббота, 14 ноября, 15:00, Ростов-на-Дону.">
<meta property="og:image" content="{URL}/img/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="img/favicon.svg" type="image/svg+xml">
"""
cut = page.index('<div class="loader"')
html = head + page[:cut] + "</head>\n<body>\n" + page[cut:] + "\n</body>\n</html>\n"

shutil.rmtree(SITE, ignore_errors=True)
os.makedirs(os.path.join(SITE, "img"))
os.makedirs(os.path.join(SITE, "audio"))
open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(html)
for f in ["img/anton-sonya.jpg", "img/vine.svg", "img/rings.png", "img/og.png", "img/favicon.svg", "audio/giorno-lofi.mp3"]:
    shutil.copy(os.path.join(ROOT, f), os.path.join(SITE, f))

os.makedirs(os.path.join(ROOT, "export"), exist_ok=True)
with zipfile.ZipFile(os.path.join(ROOT, "export", "antonisonya-site.zip"), "w", zipfile.ZIP_DEFLATED) as z:
    for dp, _, fs in os.walk(SITE):
        for f in fs:
            p = os.path.join(dp, f)
            z.write(p, os.path.join("antonisonya", os.path.relpath(p, SITE)))
print("ok")
