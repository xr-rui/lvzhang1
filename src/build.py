"""Build the installable web app (PWA) into dist/ from src/app.html."""
import pathlib, shutil
from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).parent.parent
DIST = ROOT
DIST.mkdir(exist_ok=True)
VERSION = "1.0.0"

body = (ROOT / "src/app.html").read_text(encoding="utf-8")
body = body.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")

head = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#17675f">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="旅账">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icon-192.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>
"""
tail = """
<script>
if ('serviceWorker' in navigator && location.protocol === 'https:') {
  navigator.serviceWorker.register('sw.js').catch(function(){});
}
</script>
</body>
</html>
"""
# split <title>/<style> (head) from markup (body)
idx = body.index("</style>") + len("</style>")
html = head + body[:idx] + "\n</head>\n<body>\n" + body[idx:] + tail
(DIST / "index.html").write_text(html, encoding="utf-8")

(DIST / "manifest.webmanifest").write_text("""{
  "name": "旅账 · 多币种记账",
  "short_name": "旅账",
  "start_url": "./",
  "scope": "./",
  "display": "standalone",
  "background_color": "#f3f5f4",
  "theme_color": "#17675f",
  "lang": "zh-CN",
  "icons": [
    {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
    {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}
  ]
}
""", encoding="utf-8")

(DIST / "sw.js").write_text(f"""const CACHE = 'lvzhang-{VERSION}';
const SHELL = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png', './apple-touch-icon.png'];
self.addEventListener('install', e => {{ e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); }});
self.addEventListener('activate', e => {{ e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); }});
self.addEventListener('fetch', e => {{
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin) return; // exchange-rate APIs go straight to network
  // network first so updates arrive, cache as offline fallback
  e.respondWith(fetch(e.request).then(r => {{ const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return r; }})
    .catch(() => caches.match(e.request).then(r => r || caches.match('./index.html'))));
}});
""", encoding="utf-8")

def icon(size, path, pad=0.0):
    s = size * 4
    im = Image.new("RGB", (s, s), "#17675f")
    d = ImageDraw.Draw(im)
    # three stacked coins
    r = int(s * 0.17 * (1 - pad))
    cx, cy = s // 2, s // 2
    for dx, dy, col in [(-0.13, 0.06, "#8fd3c8"), (0.13, 0.06, "#d5ebe7"), (0, -0.1, "#ffffff")]:
        x, y = cx + int(dx * s * (1 - pad)), cy + int(dy * s * (1 - pad))
        d.ellipse([x - r - s//60, y - r - s//60, x + r + s//60, y + r + s//60], fill="#17675f")
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    im.resize((size, size), Image.LANCZOS).save(path)

icon(192, DIST / "icon-192.png", 0.15)
icon(512, DIST / "icon-512.png", 0.15)
icon(180, DIST / "apple-touch-icon.png", 0.1)
print("built", sorted(p.name for p in DIST.iterdir()))
