"""Saf yardımcılar: link işleme, thumbnail görselleri, Windows pencere stili."""
import io
import re
import sys
import urllib.request
from urllib.parse import parse_qs, urlparse

from PIL import Image, ImageDraw

try:
    LANCZOS = Image.Resampling.LANCZOS
except AttributeError:  # eski Pillow
    LANCZOS = Image.LANCZOS

# --------------------------------------------------------------------------- linkler

KNOWN_SITES = {
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "instagram.com": "Instagram",
    "tiktok.com": "TikTok",
    "twitter.com": "X",
    "x.com": "X",
    "facebook.com": "Facebook",
    "fb.watch": "Facebook",
    "reddit.com": "Reddit",
    "vimeo.com": "Vimeo",
    "twitch.tv": "Twitch",
    "dailymotion.com": "Dailymotion",
    "pinterest.com": "Pinterest",
    "soundcloud.com": "SoundCloud",
    "bilibili.com": "Bilibili",
    "vk.com": "VK",
}


def clean_url(raw):
    raw = raw.strip().strip(",;")
    if raw and not raw.lower().startswith(("http://", "https://")):
        raw = "https://" + raw
    return raw


def split_links(text):
    parts = re.split(r"[\s,;]+", text.strip())
    seen, out = set(), []
    for p in parts:
        if not p:
            continue
        url = clean_url(p)
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def site_label(url):
    """Bilinen platformun adını, bilinmeyen geçerli linkte alan adını, geçersizde None döndürür."""
    host = urlparse(url).netloc.lower().split("@")[-1].split(":")[0]
    if not host or "." not in host:
        return None
    for key, name in KNOWN_SITES.items():
        if host == key or host.endswith("." + key):
            return name
    return host[4:] if host.startswith("www.") else host


def is_youtube_playlist(url):
    return site_label(url) == "YouTube" and ("list=" in url or "/playlist" in url)


def youtube_id(url):
    p = urlparse(url)
    host = p.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    vid = ""
    if host == "youtu.be":
        vid = p.path.strip("/").split("/")[0]
    elif host == "youtube.com" or host.endswith(".youtube.com"):
        if p.path == "/watch":
            vid = parse_qs(p.query).get("v", [""])[0]
        else:
            m = re.match(r"^/(?:shorts|embed|live|v)/([\w-]{11})", p.path)
            vid = m.group(1) if m else ""
    return vid if re.fullmatch(r"[\w-]{11}", vid or "") else None


def human_speed(speed):
    return f"{speed / 1048576:.2f} MB/s" if speed else "-"


def human_time(seconds):
    if seconds is None:
        return "-"
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def strip_ansi(text):
    return re.sub(r"\x1b\[[0-9;]*m", "", str(text))


def short_error(text, limit=220):
    text = strip_ansi(text).strip().splitlines()
    line = text[-1] if text else ""
    line = re.sub(r"^ERROR:\s*", "", line)
    return line if len(line) <= limit else line[: limit - 1] + "…"


# --------------------------------------------------------------------------- renkler

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(int(max(0, min(255, round(v)))) for v in rgb)


def lerp_color(a, b, t):
    ra, rb = hex_to_rgb(a), hex_to_rgb(b)
    return rgb_to_hex(tuple(ra[i] + (rb[i] - ra[i]) * t for i in range(3)))


# --------------------------------------------------------------------------- görseller

def _rounded_mask(w, h, radius):
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    return mask


def placeholder_thumb(w, h, radius=10, scale=2, dark=True):
    W, H = w * scale, h * scale
    top, bottom = ("#1b2440", "#0f1527") if dark else ("#dbe3f5", "#c3cfea")
    base = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(base)
    for y in range(H):
        d.line([(0, y), (W, y)], fill=lerp_color(top, bottom, y / max(H - 1, 1)))
    cx, cy, r = W // 2, H // 2, H // 5
    tri = [(cx - r // 2, cy - r), (cx - r // 2, cy + r), (cx + r, cy)]
    d.polygon(tri, fill="#6b7aa8" if dark else "#7d8fc4")
    img = base.convert("RGBA")
    img.putalpha(_rounded_mask(W, H, radius * scale))
    return img


def round_cover(img, w, h, radius=10, scale=2):
    """Görseli w×h alanına 'cover' olarak sığdırır, köşeleri yuvarlar."""
    W, H = w * scale, h * scale
    img = img.convert("RGB")
    ratio = max(W / img.width, H / img.height)
    new = (max(1, round(img.width * ratio)), max(1, round(img.height * ratio)))
    img = img.resize(new, LANCZOS)
    left, top = (new[0] - W) // 2, (new[1] - H) // 2
    img = img.crop((left, top, left + W, top + H)).convert("RGBA")
    img.putalpha(_rounded_mask(W, H, radius * scale))
    return img


def fetch_image(url, timeout=10, max_bytes=6_000_000):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read(max_bytes)
        return Image.open(io.BytesIO(data))
    except Exception:
        return None


# --------------------------------------------------------------------------- Windows pencere kenarlığı

def _dwm_set(widget, attr, value):
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes

        user32 = ctypes.windll.user32
        user32.GetParent.restype = ctypes.c_void_p
        user32.GetParent.argtypes = [ctypes.c_void_p]
        dwm = ctypes.windll.dwmapi
        dwm.DwmSetWindowAttribute.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint]
        hwnd = user32.GetParent(widget.winfo_id())
        val = ctypes.c_int(value)
        dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(val), ctypes.sizeof(val))
    except Exception:
        pass


def _colorref(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    return r | (g << 8) | (b << 16)


def style_window(widget, dark, caption_hex, border_hex):
    """Koyu başlık çubuğu + başlık rengi + pencere kenarlık rengi (Windows 11; Windows 10'da sessizce yok sayılır)."""
    _dwm_set(widget, 20, 1 if dark else 0)
    _dwm_set(widget, 35, _colorref(caption_hex))
    _dwm_set(widget, 34, _colorref(border_hex))

