"""Собирает сайт для Netlify в папку site/ (и site.zip в export/)."""
import os, re, shutil, subprocess, zipfile

URL = "https://sonya-anton.ru"
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
for d in ("img", "audio", "fonts"):
    os.makedirs(os.path.join(SITE, d))

# Шрифты кладём рядом с сайтом, чтобы не зависеть от Google Fonts
link = re.search(r'<link rel="stylesheet" href="(https://fonts.googleapis.com[^"]+)">', html)
ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
css = subprocess.run(["curl", "-sS", "-A", ua, link.group(1).replace("&amp;", "&")], capture_output=True, text=True, check=True).stdout
faces = []
for i, (subset, block) in enumerate(re.findall(r"/\* ([\w-]+) \*/\s*(@font-face \{.*?\})", css, re.S)):
    if subset not in ("cyrillic", "latin"):
        continue
    url = re.search(r"url\((https://[^)]+)\)", block).group(1)
    name = f"f{i}.woff2"
    subprocess.run(["curl", "-sS", "-o", os.path.join(SITE, "fonts", name), url], check=True)
    faces.append(block.replace(url, "fonts/" + name))
html = re.sub(r'<link rel="preconnect"[^>]*>\s*', "", html)
html = html.replace(link.group(0), "<style>\n" + "\n".join(faces) + "\n</style>")
open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(html)
for f in ["img/anton-sonya.jpg", "img/vine.svg", "img/rings.png", "img/og.png", "img/favicon.svg", "audio/giorno-lofi.mp3"]:
    shutil.copy(os.path.join(ROOT, f), os.path.join(SITE, f))

os.makedirs(os.path.join(ROOT, "export"), exist_ok=True)
with zipfile.ZipFile(os.path.join(ROOT, "export", "sonya-anton-site.zip"), "w", zipfile.ZIP_DEFLATED) as z:
    for dp, _, fs in os.walk(SITE):
        for f in fs:
            p = os.path.join(dp, f)
            z.write(p, os.path.join("sonya-anton", os.path.relpath(p, SITE)))
    # Сервер опроса едет в архиве рядом с сайтом, но не попадает в публичную папку
    z.write(os.path.join(ROOT, "tools", "rsvp_server.py"), "sonya-anton-server/rsvp_server.py")
print("ok")
