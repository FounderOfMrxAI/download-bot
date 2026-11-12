import collections
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from functools import partial
from pathlib import Path
from tkinter import filedialog, messagebox

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

try:
    import customtkinter as ctk
except ImportError:
    _root = tk.Tk()
    _root.withdraw()
    messagebox.showerror(
        "Missing package / Eksik paket",
        "customtkinter is not installed.\ncustomtkinter kurulu değil.\n\npip install -r requirements.txt",
    )
    sys.exit(1)

try:
    from yt_dlp import YoutubeDL
    from yt_dlp.utils import DownloadError
except ImportError:
    _root = tk.Tk()
    _root.withdraw()
    messagebox.showerror(
        "Missing package / Eksik paket",
        "yt-dlp is not installed.\nyt-dlp kurulu değil.\n\npip install -r requirements.txt",
    )
    sys.exit(1)

try:
    from yt_dlp.utils import DownloadCancelled
except ImportError:
    class DownloadCancelled(Exception):
        pass

try:
    from yt_dlp.version import __version__ as YTDLP_VERSION
except Exception:
    YTDLP_VERSION = "?"

from diller import LANGUAGES
from yardimci import (
    glow_color,
    gradient_button_image,
    fetch_image,
    human_speed,
    human_time,
    is_youtube_playlist,
    placeholder_thumb,
    round_cover,
    set_window_border,
    short_error,
    site_label,
    split_links,
    style_window,
    youtube_id,
)
from yasal import LICENSE_TEXT, NOTICES_TEXT

APP_VERSION = "2.0.0"
GITHUB_URL = "https://github.com/FounderOfMrxAI"
CONFIG_PATH = Path.home() / ".indirme_botu.json"
DEFAULT_DIR = str(Path.home() / "Downloads" / "DownloadBot")

THUMB_W, THUMB_H = 128, 72
MAX_PARALLEL = 5

FORMAT_SPECS = [
    ("bestvideo*+bestaudio/best", None),
    ("bestvideo[height<=1080]+bestaudio/best[height<=1080]", None),
    ("bestvideo[height<=720]+bestaudio/best[height<=720]", None),
    ("bestvideo[height<=480]+bestaudio/best[height<=480]", None),
    ("bestvideo[height<=360]+bestaudio/best[height<=360]", None),
    ("bestaudio/best", "mp3"),
    ("bestaudio/best", "m4a"),
]

APPEARANCES = ["dark", "light", "system"]

PP_KEYS = {
    "FFmpegMerger": "stat_merge",
    "FFmpegExtractAudio": "stat_audio",
    "FFmpegVideoConvertor": "stat_convert",
}

# (açık tema, koyu tema)
ACCENT = ("#4f46e5", "#6366f1")
ACCENT_HOVER = ("#4338ca", "#4f46e5")
DANGER = ("#dc2626", "#ef4444")
DANGER_HOVER = ("#b91c1c", "#dc2626")
OK = ("#16a34a", "#4ade80")
BG = ("#eef2f9", "#0a0e1a")
SIDEBAR = ("#e2e8f3", "#0d1322")
CARD = ("#fbfcff", "#131a2d")
FIELD = ("#eef2f9", "#0c1121")
BORDER = ("#cdd6e8", "#27324f")
SHEEN = ("#ffffff", "#34416a")
HOVER = ("#d7dfef", "#1b2540")
TEXT = ("#0f172a", "#e6eaf5")
MUTED = ("#64748b", "#8a94ad")
DISABLED_TEXT = ("#9ca3af", "#6b7280")
NEUTRAL = ("#e2e8f0", "#222c47")
SEG_SELECTED = ("#c7d2fe", "#4f46e5")
SEG_SELECTED_HOVER = ("#a5b4fc", "#4338ca")

BTN_GRAD = ("#4f6bff", "#a855f7")

SECONDARY = {
    "fg_color": "transparent",
    "border_width": 1,
    "border_color": BORDER,
    "text_color": TEXT,
    "hover_color": HOVER,
    "height": 32,
    "corner_radius": 8,
}

MENU = {
    "fg_color": FIELD,
    "button_color": ACCENT,
    "button_hover_color": ACCENT_HOVER,
    "text_color": TEXT,
    "dropdown_fg_color": CARD,
    "dropdown_text_color": TEXT,
    "dropdown_hover_color": HOVER,
    "height": 34,
    "corner_radius": 8,
    "dynamic_resizing": False,
}

ENTRY = {
    "fg_color": FIELD,
    "border_color": BORDER,
    "text_color": TEXT,
    "height": 34,
    "corner_radius": 8,
}

SEGMENT = {
    "fg_color": FIELD,
    "selected_color": SEG_SELECTED,
    "selected_hover_color": SEG_SELECTED_HOVER,
    "unselected_color": FIELD,
    "unselected_hover_color": HOVER,
    "text_color": TEXT,
    "height": 34,
    "corner_radius": 8,
}


def pick(colors):
    """(açık, koyu) renk çiftinden geçerli temaya uyanı seçer."""
    return colors[1] if ctk.get_appearance_mode() == "Dark" else colors[0]


def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_config(data):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def resource_dir():
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def find_bundled_ffmpeg():
    """exe içine gömülü (veya yanındaki) ffmpeg'i bulur; yoksa None."""
    names = ["ffmpeg.exe", "ffmpeg"]
    bases = [resource_dir()]
    if getattr(sys, "frozen", False):
        bases.append(os.path.dirname(sys.executable))
    for base in bases:
        for name in names:
            candidate = os.path.join(base, name)
            if os.path.isfile(candidate):
                return candidate
    return None


def open_folder(path):
    if sys.platform.startswith("win"):
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def reveal_file(path):
    """Dosyayı klasöründe seçili göstermeyi dener; olmazsa klasörü açar."""
    if sys.platform.startswith("win") and os.path.isfile(path):
        subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
    else:
        open_folder(os.path.dirname(path) if os.path.isfile(path) else path)


class Task:
    _counter = 0

    def __init__(self, url, site, fmt_index, outdir, playlist, items):
        Task._counter += 1
        self.id = Task._counter
        self.url = url
        self.site = site
        self.fmt_index = fmt_index
        self.outdir = outdir
        self.playlist = playlist
        self.items = items
        self.state = "queued"  # queued | running | done | error | cancelled
        self.cancel = threading.Event()
        self.thumb_url = None
        self.last_emit = 0.0
        self.path = None
        self.msg = ""


class TextDialog(ctk.CTkToplevel):
    def __init__(self, app, title, text):
        super().__init__(app)
        self.title(title)
        self.geometry("660x540")
        self.minsize(480, 360)
        self.configure(fg_color=BG)
        self.transient(app)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        box = ctk.CTkTextbox(
            self,
            fg_color=CARD,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            corner_radius=12,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=12),
        )
        box.grid(row=0, column=0, sticky="nsew", padx=18, pady=(18, 10))
        box.insert("1.0", text)
        box.configure(state="disabled")

        ctk.CTkButton(
            self,
            text=app.t("close"),
            command=self.destroy,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="white",
            height=34,
            width=110,
            corner_radius=8,
        ).grid(row=1, column=0, sticky="e", padx=18, pady=(0, 18))

        self.after(120, self._focus)
        self.after(300, lambda: style_window(self, app.is_dark(), app.bg_hex(), "#6366f1"))

    def _focus(self):
        try:
            self.lift()
            self.focus_force()
        except tk.TclError:
            pass


class TaskRow(ctk.CTkFrame):
    """Kuyruktaki tek bir indirme: thumbnail, başlık, ilerleme ve durum."""

    def __init__(self, app, task):
        super().__init__(
            app.queue_list, fg_color=CARD, corner_radius=12, border_width=1, border_color=BORDER
        )
        self.app = app
        self.task = task
        self.run_text = ""
        self.image = None
        self.grid_columnconfigure(1, weight=1)

        self.thumb = ctk.CTkLabel(
            self, text="", image=app.placeholder, width=THUMB_W, height=THUMB_H, fg_color="transparent"
        )
        self.thumb.grid(row=0, column=0, rowspan=3, padx=12, pady=12)

        self.title_label = ctk.CTkLabel(
            self,
            text=task.url,
            font=app.f_head,
            anchor="w",
            justify="left",
            text_color=TEXT,
            wraplength=420,
        )
        self.title_label.grid(row=0, column=1, sticky="ew", pady=(12, 0))

        self.meta = ctk.CTkLabel(
            self, text="", font=app.f_small, text_color=MUTED, anchor="w", justify="left", wraplength=420
        )
        self.meta.grid(row=1, column=1, sticky="ew", pady=(2, 0))

        self.bar = ctk.CTkProgressBar(
            self, height=8, corner_radius=4, progress_color=ACCENT, fg_color=NEUTRAL
        )
        self.bar.set(0)
        self.bar.grid(row=2, column=1, sticky="ew", pady=(8, 12))

        side = ctk.CTkFrame(self, fg_color="transparent")
        side.grid(row=0, column=2, rowspan=3, padx=12)
        self.cancel_btn = ctk.CTkButton(
            side, text="✕", width=32, command=lambda: app.cancel_task(task), **{**SECONDARY, "height": 32}
        )
        self.open_btn = ctk.CTkButton(side, text="", width=84, command=self.open_location, **SECONDARY)

        self.bind("<Configure>", self.on_resize)
        self.render()

    def on_resize(self, event):
        wrap = max(event.width - THUMB_W - 130, 160)
        self.title_label.configure(wraplength=wrap)
        self.meta.configure(wraplength=wrap)

    def set_title(self, text):
        self.title_label.configure(text=text)

    def set_thumb(self, ctk_image):
        self.image = ctk_image
        self.thumb.configure(image=ctk_image)

    def set_progress(self, fraction, text):
        self.bar.set(min(max(fraction, 0.0), 1.0))
        self.run_text = text
        self.render()

    def open_location(self):
        target = self.task.path or self.task.outdir
        try:
            reveal_file(target)
        except Exception as e:
            messagebox.showerror(self.app.t("dlg_error_title"), self.app.t("dlg_open_error", err=e))

    def render(self):
        t = self.app.t
        task = self.task
        color = MUTED
        if task.state == "queued":
            text = t("task_queued")
        elif task.state == "running":
            text = self.run_text or t("task_starting")
        elif task.state == "done":
            text, color = t("task_done"), OK
        elif task.state == "error":
            text = t("task_invalid") if task.msg == "invalid" else t("task_error") + (f": {task.msg}" if task.msg else "")
            color = DANGER
        else:
            text = t("task_cancelled")
        self.meta.configure(text=f"{task.site or '?'}  ·  {text}", text_color=color)
        self.open_btn.configure(text=t("task_open"))

        if task.state in ("queued", "running"):
            self.open_btn.pack_forget()
            self.cancel_btn.pack()
        elif task.state == "done":
            self.cancel_btn.pack_forget()
            self.open_btn.pack()
        else:
            self.cancel_btn.pack_forget()
            self.open_btn.pack_forget()

    def finish(self):
        if self.task.state == "done":
            self.bar.set(1)
        self.run_text = ""
        self.render()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.settings = load_config()
        for old_key in ("cookie_mode", "cookie_file"):
            self.settings.pop(old_key, None)

        lang = self.settings.get("language")
        self.lang = lang if lang in LANGUAGES else "en"

        appearance = self.settings.get("appearance", "dark")
        self.appearance = appearance if appearance in APPEARANCES else "dark"
        ctk.set_appearance_mode(self.appearance)

        try:
            self.format_index = int(self.settings.get("format", 0))
        except (TypeError, ValueError):
            self.format_index = 0
        if not 0 <= self.format_index < len(FORMAT_SPECS):
            self.format_index = 0

        try:
            self.parallel = int(self.settings.get("parallel", 3))
        except (TypeError, ValueError):
            self.parallel = 3
        self.parallel = min(max(self.parallel, 1), MAX_PARALLEL)

        self.effects = bool(self.settings.get("effects", True))
        self.playlist_var = tk.BooleanVar(value=bool(self.settings.get("playlist", True)))
        self.effects_var = tk.BooleanVar(value=self.effects)

        self.events = queue.Queue()
        self.tasks = {}
        self.rows = {}
        self.pending = collections.deque()
        self.active = 0
        self.i18n = []
        self.pages = {}
        self.nav_buttons = {}
        self.glow_widgets = []
        self.phase = 0.0
        self.tick_count = 0

        self.ffmpeg_path = find_bundled_ffmpeg()
        self.has_ffmpeg = bool(self.ffmpeg_path or shutil.which("ffmpeg"))

        self.f_title = ctk.CTkFont(size=26, weight="bold")
        self.f_head = ctk.CTkFont(size=14, weight="bold")
        self.f_body = ctk.CTkFont(size=13)
        self.f_small = ctk.CTkFont(size=12)
        self.f_brand = ctk.CTkFont(size=20, weight="bold")

        self.make_images()

        self.title(self.t("app_title"))
        self.geometry("1120x820")
        self.minsize(980, 700)
        self.configure(fg_color=BG)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        try:
            self.attributes("-alpha", 0.0 if self.effects else 1.0)
        except tk.TclError:
            pass

        outdir = self.settings.get("outdir", DEFAULT_DIR)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=26, pady=22)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.build_download()
        self.build_settings()

        self.set_outdir(outdir)
        self.refresh_menus()
        self.update_summary()
        self.show_page("download")
        self.after(60, self.poll)
        self.after(50, self.tick)
        self.after(120, self.fade_in)
        self.after(300, self.style_titlebar)
        self.after(300, self.set_icon)

    # ------------------------------------------------------------------ yardımcılar

    def t(self, key, **kw):
        text = LANGUAGES[self.lang].get(key)
        if text is None:
            text = LANGUAGES["en"].get(key, key)
        if kw and isinstance(text, str):
            return text.format(**kw)
        return text

    def is_dark(self):
        return ctk.get_appearance_mode() == "Dark"

    def bg_hex(self):
        return pick(BG)

    def label(self, master, key, **kw):
        widget = ctk.CTkLabel(master, text=self.t(key), **kw)
        self.i18n.append((widget, "text", key))
        return widget

    def button(self, master, key, command, **kw):
        widget = ctk.CTkButton(master, text=self.t(key), command=command, **kw)
        self.i18n.append((widget, "text", key))
        return widget

    def make_images(self):
        ph = placeholder_thumb(THUMB_W, THUMB_H, dark=True)
        ph_light = placeholder_thumb(THUMB_W, THUMB_H, dark=False)
        self.placeholder = ctk.CTkImage(light_image=ph_light, dark_image=ph, size=(THUMB_W, THUMB_H))
        self.primary_w, self.primary_h = 156, 38
        normal = gradient_button_image(self.primary_w, self.primary_h, *BTN_GRAD, radius=10)
        bright = gradient_button_image(self.primary_w, self.primary_h, *BTN_GRAD, radius=10, bright=0.14)
        size = (self.primary_w, self.primary_h)
        self.primary_img = ctk.CTkImage(light_image=normal, dark_image=normal, size=size)
        self.primary_img_hover = ctk.CTkImage(light_image=bright, dark_image=bright, size=size)

    def card(self, master):
        frame = ctk.CTkFrame(master, fg_color=CARD, corner_radius=14, border_width=1, border_color=BORDER)
        # cam parlaması: üst kenarda ince, açık bir çizgi
        ctk.CTkFrame(frame, height=1, fg_color=SHEEN, corner_radius=0).place(
            relx=0.03, y=1, relwidth=0.94
        )
        return frame

    def header(self, page, title_key, sub_key):
        box = ctk.CTkFrame(page, fg_color="transparent")
        box.grid(row=0, column=0, sticky="ew")
        self.label(box, title_key, font=self.f_title, anchor="w", text_color=TEXT).pack(anchor="w")
        self.label(box, sub_key, font=self.f_body, anchor="w", text_color=MUTED).pack(anchor="w", pady=(2, 0))

    def make_page(self, name):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        self.pages[name] = page
        return page

    # ------------------------------------------------------------------ efektler

    def add_glow(self, widget):
        if widget not in self.glow_widgets:
            self.glow_widgets.append(widget)
        if not self.effects:
            widget.configure(border_color=BORDER)

    def remove_glow(self, widget):
        if widget in self.glow_widgets:
            self.glow_widgets.remove(widget)
        try:
            widget.configure(border_color=BORDER)
        except tk.TclError:
            pass

    def tick(self):
        try:
            if self.effects and self.state() != "iconic":
                self.phase = (self.phase + 0.004) % 1.0
                color = glow_color(self.phase)
                for widget in list(self.glow_widgets):
                    try:
                        widget.configure(border_color=color)
                    except tk.TclError:
                        self.glow_widgets.remove(widget)
                self.tick_count += 1
                if self.tick_count % 3 == 0:
                    set_window_border(self, color)
        except tk.TclError:
            pass
        self.after(50, self.tick)

    def fade_in(self, step=0):
        if not self.effects:
            return
        try:
            self.attributes("-alpha", min(1.0, step / 10))
            if step < 10:
                self.after(18, lambda: self.fade_in(step + 1))
        except tk.TclError:
            pass

    def style_titlebar(self):
        style_window(self, self.is_dark(), self.bg_hex(), "#6366f1")

    def set_icon(self):
        icon = os.path.join(resource_dir(), "icon.ico")
        if sys.platform.startswith("win") and os.path.isfile(icon):
            try:
                self.iconbitmap(icon)
            except tk.TclError:
                pass

    def hover_image(self, button, image):
        button.configure(image=image)

    # ------------------------------------------------------------------ kenar çubuğu

    def build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=214, corner_radius=0, fg_color=SIDEBAR)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(10, weight=1)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=20, pady=(26, 22))
        self.label(brand, "app_title", font=self.f_brand, text_color=TEXT, anchor="w").pack(anchor="w")
        self.label(brand, "app_tagline", font=self.f_small, text_color=MUTED, anchor="w").pack(anchor="w", pady=(2, 0))

        items = [("download", "nav_download"), ("settings", "nav_settings")]
        for row, (page, key) in enumerate(items, start=1):
            btn = self.button(
                sidebar,
                key,
                lambda p=page: self.show_page(p),
                fg_color="transparent",
                text_color=TEXT,
                hover_color=HOVER,
                anchor="w",
                height=40,
                corner_radius=10,
                font=self.f_body,
            )
            btn.grid(row=row, column=0, sticky="ew", padx=14, pady=3)
            self.nav_buttons[page] = btn

        ctk.CTkLabel(sidebar, text=f"v{APP_VERSION}", font=self.f_small, text_color=MUTED).grid(
            row=11, column=0, sticky="w", padx=20, pady=18
        )

    def show_page(self, name):
        for key, page in self.pages.items():
            if key == name:
                page.grid(row=0, column=0, sticky="nsew")
            else:
                page.grid_remove()
        for key, btn in self.nav_buttons.items():
            if key == name:
                btn.configure(fg_color=ACCENT, text_color="white", hover_color=ACCENT_HOVER)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT, hover_color=HOVER)

    # ------------------------------------------------------------------ indirme sayfası

    def build_download(self):
        page = self.make_page("download")
        page.grid_rowconfigure(4, weight=1)
        self.header(page, "dl_title", "dl_subtitle")

        links = self.card(page)
        links.configure(border_width=2)
        links.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        links.grid_columnconfigure(0, weight=1)
        self.add_glow(links)

        top = ctk.CTkFrame(links, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        self.label(top, "links_label", font=self.f_head, text_color=TEXT).pack(side="left")
        self.label(top, "links_hint", font=self.f_small, text_color=MUTED).pack(side="left", padx=10)

        self.links_box = ctk.CTkTextbox(
            links,
            height=76,
            fg_color=FIELD,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            corner_radius=10,
            wrap="word",
            font=self.f_body,
        )
        self.links_box.grid(row=1, column=0, sticky="ew", padx=16)

        tools = ctk.CTkFrame(links, fg_color="transparent")
        tools.grid(row=2, column=0, sticky="ew", padx=16, pady=(10, 14))
        tools.grid_columnconfigure(0, weight=1)
        left = ctk.CTkFrame(tools, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")
        self.button(left, "paste", self.paste, **SECONDARY).pack(side="left")
        self.button(left, "load_file", self.load_file, **SECONDARY).pack(side="left", padx=8)
        self.button(left, "clear", lambda: self.links_box.delete("1.0", "end"), **SECONDARY).pack(side="left")

        right = ctk.CTkFrame(tools, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e")
        self.start_btn = ctk.CTkButton(
            right,
            text=self.t("btn_download"),
            command=self.start,
            image=self.primary_img,
            compound="center",
            fg_color="transparent",
            hover_color=CARD,
            border_width=0,
            text_color="white",
            width=self.primary_w,
            height=self.primary_h,
            corner_radius=10,
            font=self.f_head,
        )
        self.i18n.append((self.start_btn, "text", "btn_download"))
        self.start_btn.bind("<Enter>", lambda e: self.hover_image(self.start_btn, self.primary_img_hover))
        self.start_btn.bind("<Leave>", lambda e: self.hover_image(self.start_btn, self.primary_img))
        self.start_btn.pack(side="left")
        self.stop_btn = self.button(
            right,
            "btn_stop",
            self.stop_all,
            fg_color=NEUTRAL,
            hover_color=NEUTRAL,
            text_color="white",
            text_color_disabled=DISABLED_TEXT,
            height=self.primary_h,
            width=130,
            corner_radius=10,
            font=self.f_head,
            state="disabled",
        )
        self.stop_btn.pack(side="left", padx=(8, 0))

        opts = self.card(page)
        opts.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        opts.grid_columnconfigure(1, weight=1)
        opts.grid_columnconfigure(3, weight=1)

        self.label(opts, "type_label", font=self.f_body, text_color=TEXT, anchor="w").grid(
            row=0, column=0, sticky="w", padx=(16, 10), pady=(14, 6)
        )
        self.format_menu = ctk.CTkOptionMenu(opts, values=self.t("formats"), command=self.on_format, **MENU)
        self.format_menu.grid(row=0, column=1, sticky="ew", padx=(0, 20), pady=(14, 6))

        self.label(opts, "range_label", font=self.f_body, text_color=TEXT, anchor="w").grid(
            row=0, column=2, sticky="w", padx=(0, 10), pady=(14, 6)
        )
        self.range_entry = ctk.CTkEntry(opts, placeholder_text=self.t("range_hint"), **ENTRY)
        self.range_entry.grid(row=0, column=3, sticky="ew", padx=(0, 16), pady=(14, 6))

        switch = ctk.CTkSwitch(
            opts,
            text=self.t("playlist_switch"),
            variable=self.playlist_var,
            onvalue=True,
            offvalue=False,
            progress_color=ACCENT,
            text_color=TEXT,
            font=self.f_body,
        )
        self.i18n.append((switch, "text", "playlist_switch"))
        switch.grid(row=1, column=0, columnspan=4, sticky="w", padx=16, pady=6)

        self.label(opts, "save_label", font=self.f_body, text_color=TEXT, anchor="w").grid(
            row=2, column=0, sticky="w", padx=(16, 10), pady=(6, 14)
        )
        folder = ctk.CTkFrame(opts, fg_color="transparent")
        folder.grid(row=2, column=1, columnspan=3, sticky="ew", padx=(0, 16), pady=(6, 14))
        folder.grid_columnconfigure(0, weight=1)
        self.outdir_entry = ctk.CTkEntry(folder, **ENTRY)
        self.outdir_entry.grid(row=0, column=0, sticky="ew")
        self.button(folder, "browse", self.choose_dir, width=90, **SECONDARY).grid(row=0, column=1, padx=(8, 0))
        self.button(folder, "open_folder", self.open_dir, width=110, **SECONDARY).grid(row=0, column=2, padx=(8, 0))

        if not self.has_ffmpeg:
            self.label(page, "ffmpeg_warn", font=self.f_small, text_color=DANGER, anchor="w").grid(
                row=3, column=0, sticky="w", pady=(8, 0)
            )

        qcard = self.card(page)
        qcard.grid(row=4, column=0, sticky="nsew", pady=(12, 0))
        qcard.grid_columnconfigure(0, weight=1)
        qcard.grid_rowconfigure(1, weight=1)

        qhead = ctk.CTkFrame(qcard, fg_color="transparent")
        qhead.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        qhead.grid_columnconfigure(1, weight=1)
        self.label(qhead, "queue_title", font=self.f_small, text_color=MUTED, anchor="w").grid(row=0, column=0)
        self.summary_label = ctk.CTkLabel(qhead, text="", font=self.f_small, text_color=MUTED, anchor="e")
        self.summary_label.grid(row=0, column=1, sticky="e", padx=10)
        self.button(qhead, "queue_clear", self.clear_finished, **SECONDARY).grid(row=0, column=2)

        self.queue_list = ctk.CTkScrollableFrame(
            qcard,
            fg_color="transparent",
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=HOVER,
        )
        self.queue_list.grid(row=1, column=0, sticky="nsew", padx=(10, 6), pady=(0, 10))
        self.queue_list.grid_columnconfigure(0, weight=1)
        self.empty_label = ctk.CTkLabel(
            self.queue_list, text=self.t("queue_empty"), font=self.f_body, text_color=MUTED, justify="center"
        )
        self.i18n.append((self.empty_label, "text", "queue_empty"))
        self.empty_label.pack(pady=40)

    # ------------------------------------------------------------------ ayarlar sayfası

    def section(self, parent, key, row):
        self.label(parent, key, font=self.f_small, text_color=MUTED, anchor="w").grid(
            row=row * 2, column=0, sticky="w", padx=4, pady=(14 if row else 0, 6)
        )
        card = self.card(parent)
        card.grid(row=row * 2 + 1, column=0, sticky="ew")
        card.grid_columnconfigure(1, weight=1)
        return card

    def setting_row(self, card, row, key, last=False, hint_key=None):
        box = ctk.CTkFrame(card, fg_color="transparent")
        box.grid(row=row, column=0, sticky="w", padx=(18, 16), pady=(14 if row == 0 else 8, 14 if last else 8))
        self.label(box, key, font=self.f_body, text_color=TEXT, anchor="w").pack(anchor="w")
        if hint_key:
            self.label(box, hint_key, font=self.f_small, text_color=MUTED, anchor="w").pack(anchor="w")

    def build_settings(self):
        page = self.make_page("settings")
        page.grid_rowconfigure(1, weight=1)
        self.header(page, "settings_title", "settings_subtitle")

        scroll = ctk.CTkScrollableFrame(
            page,
            fg_color="transparent",
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=HOVER,
        )
        scroll.grid(row=1, column=0, sticky="nsew", pady=(14, 0))
        scroll.grid_columnconfigure(0, weight=1)

        general = self.section(scroll, "sec_general", 0)
        self.setting_row(general, 0, "lang_label")
        self.lang_menu = ctk.CTkOptionMenu(
            general, values=[d["language_name"] for d in LANGUAGES.values()], command=self.on_language, width=220, **MENU
        )
        self.lang_menu.grid(row=0, column=1, sticky="e", padx=18, pady=(14, 8))

        self.setting_row(general, 1, "appearance_label")
        self.appearance_seg = ctk.CTkSegmentedButton(
            general, values=self.t("appearance_modes"), command=self.on_appearance, width=220, **SEGMENT
        )
        self.appearance_seg.grid(row=1, column=1, sticky="e", padx=18, pady=8)

        self.setting_row(general, 2, "effects_label", last=True, hint_key="effects_hint")
        ctk.CTkSwitch(
            general,
            text="",
            width=46,
            variable=self.effects_var,
            command=self.on_effects,
            progress_color=ACCENT,
        ).grid(row=2, column=1, sticky="e", padx=18, pady=(8, 14))

        downloads = self.section(scroll, "sec_downloads", 1)
        self.setting_row(downloads, 0, "parallel_label", last=True, hint_key="parallel_hint")
        self.parallel_seg = ctk.CTkSegmentedButton(
            downloads,
            values=[str(i) for i in range(1, MAX_PARALLEL + 1)],
            command=self.on_parallel,
            width=220,
            **SEGMENT,
        )
        self.parallel_seg.set(str(self.parallel))
        self.parallel_seg.grid(row=0, column=1, sticky="e", padx=18, pady=14)

        about = self.section(scroll, "sec_about", 2)
        self.setting_row(about, 0, "about_dev")
        dev = ctk.CTkFrame(about, fg_color="transparent")
        dev.grid(row=0, column=1, sticky="e", padx=18, pady=(14, 8))
        ctk.CTkLabel(dev, text="FounderOfMrxAI", font=self.f_body, text_color=TEXT).pack(side="left")
        self.button(dev, "about_open", lambda: webbrowser.open(GITHUB_URL), width=84, **SECONDARY).pack(
            side="left", padx=(12, 0)
        )

        self.setting_row(about, 1, "about_engine")
        ctk.CTkLabel(about, text=f"yt-dlp {YTDLP_VERSION}", font=self.f_body, text_color=TEXT).grid(
            row=1, column=1, sticky="e", padx=18, pady=8
        )

        self.setting_row(about, 2, "about_version")
        ctk.CTkLabel(about, text=APP_VERSION, font=self.f_body, text_color=TEXT).grid(
            row=2, column=1, sticky="e", padx=18, pady=8
        )

        self.setting_row(about, 3, "license_label")
        lic = ctk.CTkFrame(about, fg_color="transparent")
        lic.grid(row=3, column=1, sticky="e", padx=18, pady=8)
        self.label(lic, "license_value", font=self.f_body, text_color=TEXT).pack(side="left", padx=(0, 12))
        self.button(
            lic, "license_view", lambda: TextDialog(self, self.t("license_title"), LICENSE_TEXT), **SECONDARY
        ).pack(side="left")
        self.button(
            lic, "notices_view", lambda: TextDialog(self, self.t("notices_title"), NOTICES_TEXT), **SECONDARY
        ).pack(side="left", padx=(8, 0))

        self.label(
            about, "about_legal", font=self.f_small, text_color=MUTED, anchor="w", justify="left", wraplength=640
        ).grid(row=4, column=0, columnspan=2, sticky="w", padx=18, pady=(6, 16))

    # ------------------------------------------------------------------ ayar olayları

    def refresh_menus(self):
        formats = self.t("formats")
        self.format_menu.configure(values=formats)
        self.format_menu.set(formats[self.format_index])

        modes = self.t("appearance_modes")
        self.appearance_seg.configure(values=modes)
        self.appearance_seg.set(modes[APPEARANCES.index(self.appearance)])

        self.lang_menu.set(LANGUAGES[self.lang]["language_name"])

    def apply_language(self):
        self.title(self.t("app_title"))
        for widget, option, key in self.i18n:
            widget.configure(**{option: self.t(key)})
        try:
            self.range_entry.configure(placeholder_text=self.t("range_hint"))
        except Exception:
            pass
        self.refresh_menus()
        for row in self.rows.values():
            row.render()
        self.update_summary()

    def on_language(self, choice):
        for code, data in LANGUAGES.items():
            if data["language_name"] == choice:
                self.lang = code
        self.save_settings()
        self.apply_language()

    def on_appearance(self, choice):
        modes = self.t("appearance_modes")
        if choice in modes:
            self.appearance = APPEARANCES[modes.index(choice)]
            ctk.set_appearance_mode(self.appearance)
            self.save_settings()
            self.after(150, self.style_titlebar)

    def on_effects(self):
        self.effects = bool(self.effects_var.get())
        if not self.effects:
            for widget in self.glow_widgets:
                try:
                    widget.configure(border_color=BORDER)
                except tk.TclError:
                    pass
            set_window_border(self, "#6366f1")
            try:
                self.attributes("-alpha", 1.0)
            except tk.TclError:
                pass
        self.save_settings()

    def on_parallel(self, choice):
        try:
            self.parallel = min(max(int(choice), 1), MAX_PARALLEL)
        except ValueError:
            return
        self.save_settings()
        self.pump()

    def on_format(self, choice):
        formats = self.t("formats")
        if choice in formats:
            self.format_index = formats.index(choice)

    def get_outdir(self):
        return self.outdir_entry.get().strip()

    def set_outdir(self, path):
        self.outdir_entry.delete(0, "end")
        self.outdir_entry.insert(0, path)

    def save_settings(self):
        self.settings["language"] = self.lang
        self.settings["appearance"] = self.appearance
        self.settings["outdir"] = self.get_outdir() or DEFAULT_DIR
        self.settings["format"] = self.format_index
        self.settings["playlist"] = self.playlist_var.get()
        self.settings["parallel"] = self.parallel
        self.settings["effects"] = self.effects
        save_config(self.settings)

    # ------------------------------------------------------------------ giriş araçları

    def paste(self):
        try:
            content = self.clipboard_get()
        except tk.TclError:
            return
        if self.links_box.get("1.0", "end").strip():
            self.links_box.insert("end", "\n")
        self.links_box.insert("end", content.strip())

    def load_file(self):
        path = filedialog.askopenfilename(
            title=self.t("pick_list"),
            filetypes=[(self.t("ft_text"), "*.txt"), (self.t("ft_all"), "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]
        except OSError as e:
            messagebox.showerror(self.t("dlg_error_title"), self.t("dlg_file_error", err=e))
            return
        if self.links_box.get("1.0", "end").strip():
            self.links_box.insert("end", "\n")
        self.links_box.insert("end", "\n".join(lines))

    def choose_dir(self):
        path = filedialog.askdirectory(title=self.t("pick_dir"), initialdir=self.get_outdir() or None)
        if path:
            self.set_outdir(path)
            self.save_settings()

    def open_dir(self):
        path = self.get_outdir() or DEFAULT_DIR
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            open_folder(path)
        except Exception as e:
            messagebox.showerror(self.t("dlg_error_title"), self.t("dlg_open_error", err=e))

    # ------------------------------------------------------------------ kuyruk yönetimi

    def start(self):
        urls = split_links(self.links_box.get("1.0", "end"))
        if not urls:
            messagebox.showinfo(self.t("dlg_no_links_title"), self.t("dlg_no_links"))
            return

        outdir = self.get_outdir()
        if not outdir:
            outdir = DEFAULT_DIR
            self.set_outdir(outdir)
        try:
            Path(outdir).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            messagebox.showerror(self.t("dlg_error_title"), self.t("dlg_folder_error", err=e))
            return

        items = self.range_entry.get().replace(" ", "")
        if items and not re.fullmatch(r"[\d,\-:]+", items):
            messagebox.showerror(self.t("dlg_range_title"), self.t("dlg_range_invalid"))
            return

        self.save_settings()
        want_playlist = self.playlist_var.get()

        for url in urls:
            site = site_label(url)
            playlist = bool(site) and want_playlist and is_youtube_playlist(url)
            task = Task(url, site, self.format_index, outdir, playlist, items if playlist else None)
            row = TaskRow(self, task)
            self.tasks[task.id] = task
            self.rows[task.id] = row
            self.empty_label.pack_forget()
            row.pack(fill="x", padx=(0, 6), pady=(0, 8))
            if site is None:
                task.state, task.msg = "error", "invalid"
                row.finish()
                continue
            self.pending.append(task)
            vid = youtube_id(url)
            if vid:
                self.load_thumb_async(task, f"https://i.ytimg.com/vi/{vid}/mqdefault.jpg")

        self.links_box.delete("1.0", "end")
        self.pump()

    def pump(self):
        """Boş indirme yuvası varsa sıradaki linkleri başlatır."""
        while self.pending and self.active < self.parallel:
            task = self.pending.popleft()
            if task.cancel.is_set() or task.state != "queued":
                continue
            self.active += 1
            task.state = "running"
            row = self.rows.get(task.id)
            if row:
                row.render()
                row.bar.configure(progress_color=ACCENT)
                self.add_glow(row)
            threading.Thread(target=self.run_task, args=(task,), daemon=True).start()
        self.update_summary()

    def cancel_task(self, task):
        task.cancel.set()
        if task.state == "queued":
            try:
                self.pending.remove(task)
            except ValueError:
                pass
            task.state = "cancelled"
            row = self.rows.get(task.id)
            if row:
                row.finish()
            self.update_summary()

    def stop_all(self):
        for task in list(self.tasks.values()):
            if task.state in ("queued", "running"):
                self.cancel_task(task)

    def clear_finished(self):
        for tid, task in list(self.tasks.items()):
            if task.state in ("done", "error", "cancelled"):
                row = self.rows.pop(tid, None)
                del self.tasks[tid]
                if row:
                    self.remove_glow(row)
                    row.destroy()
        if not self.tasks:
            self.empty_label.pack(pady=40)
        self.update_summary()

    def update_summary(self):
        total = len(self.tasks)
        done = sum(1 for t in self.tasks.values() if t.state == "done")
        running = sum(1 for t in self.tasks.values() if t.state == "running")
        queued = sum(1 for t in self.tasks.values() if t.state == "queued")
        text = self.t("queue_summary", done=done, total=total, running=running, queued=queued) if total else ""
        self.summary_label.configure(text=text)
        if running or queued:
            self.stop_btn.configure(state="normal", fg_color=DANGER, hover_color=DANGER_HOVER)
        else:
            self.stop_btn.configure(state="disabled", fg_color=NEUTRAL, hover_color=NEUTRAL)

    # ------------------------------------------------------------------ indirme (arka plan)

    def load_thumb_async(self, task, url):
        threading.Thread(target=self.load_thumb, args=(task, url), daemon=True).start()

    def load_thumb(self, task, url):
        img = fetch_image(url)
        if img is None:
            return
        try:
            self.events.put(("thumb", task.id, round_cover(img, THUMB_W, THUMB_H, radius=10)))
        except Exception:
            pass

    def make_options(self, task):
        fmt, audio = FORMAT_SPECS[task.fmt_index]
        base = Path(task.outdir)
        if task.playlist:
            template = str(base / "%(playlist_title)s" / "%(playlist_index)03d - %(title).150B.%(ext)s")
        else:
            template = str(base / "%(title).150B [%(id)s].%(ext)s")

        opts = {
            "format": fmt,
            "outtmpl": template,
            "noplaylist": not task.playlist,
            "progress_hooks": [partial(self.progress_hook, task)],
            "postprocessor_hooks": [partial(self.pp_hook, task)],
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "retries": 5,
            "fragment_retries": 5,
            "socket_timeout": 25,
            "concurrent_fragment_downloads": 4,
            "windowsfilenames": True,
            "merge_output_format": "mp4",
            "ignoreerrors": task.playlist,
        }
        if self.ffmpeg_path:
            opts["ffmpeg_location"] = self.ffmpeg_path
        if task.items:
            opts["playlist_items"] = task.items
        if audio:
            opts["postprocessors"] = [
                {"key": "FFmpegExtractAudio", "preferredcodec": audio, "preferredquality": "192"}
            ]
        return opts

    @staticmethod
    def title_text(info):
        title = info.get("title") or "?"
        index = info.get("playlist_index")
        total = info.get("n_entries") or info.get("playlist_count")
        if index and total:
            return f"[{index}/{total}] {title}"
        return title

    def progress_hook(self, task, d):
        if task.cancel.is_set():
            raise DownloadCancelled()
        info = d.get("info_dict") or {}
        if d.get("status") == "downloading":
            now = time.monotonic()
            if now - task.last_emit < 0.15:
                return
            task.last_emit = now
            self.events.put(("title", task.id, self.title_text(info)))
            thumb = info.get("thumbnail")
            if thumb and thumb != task.thumb_url and (task.site != "YouTube" or task.playlist):
                task.thumb_url = thumb
                self.load_thumb_async(task, thumb)
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes", 0)
            fraction = (done / total) if total else 0
            size = f"{total / 1048576:.1f} MB" if total else "?"
            self.events.put(("prog", task.id, fraction, d.get("speed"), d.get("eta"), size))
        elif d.get("status") == "finished":
            self.events.put(("stat", task.id, "stat_processing"))

    def pp_hook(self, task, d):
        info = d.get("info_dict") or {}
        name = d.get("postprocessor")
        if d.get("status") == "started" and name in PP_KEYS:
            self.events.put(("stat", task.id, PP_KEYS[name]))
        elif d.get("status") == "finished" and name == "MoveFiles":
            path = info.get("filepath")
            if path:
                self.events.put(("saved", task.id, path))

    def run_task(self, task):
        result, msg = "done", ""
        try:
            with YoutubeDL(self.make_options(task)) as ydl:
                ydl.download([task.url])
        except DownloadCancelled:
            result = "cancelled"
        except DownloadError as e:
            result, msg = "error", short_error(e)
        except Exception as e:
            result, msg = "error", short_error(e)
        if task.cancel.is_set() and result != "done":
            result, msg = "cancelled", ""
        self.events.put(("end", task.id, result, msg))

    # ------------------------------------------------------------------ olay döngüsü (arayüz iş parçacığı)

    def poll(self):
        try:
            while True:
                event = self.events.get_nowait()
                try:
                    self.handle_event(event)
                except Exception:
                    pass
        except queue.Empty:
            pass
        self.after(60, self.poll)

    def handle_event(self, event):
        kind, tid = event[0], event[1]
        row = self.rows.get(tid)
        task = self.tasks.get(tid)
        if row is None or task is None:
            return
        if kind == "title":
            row.set_title(event[2])
        elif kind == "prog":
            _, _, fraction, speed, eta, size = event
            text = self.t(
                "stat_fmt",
                percent=f"{fraction * 100:.1f}%",
                speed=human_speed(speed),
                eta=human_time(eta),
                size=size,
            )
            row.set_progress(fraction, text)
        elif kind == "stat":
            row.run_text = self.t(event[2])
            row.render()
        elif kind == "thumb":
            row.set_thumb(ctk.CTkImage(light_image=event[2], dark_image=event[2], size=(THUMB_W, THUMB_H)))
        elif kind == "saved":
            task.path = event[2]
        elif kind == "end":
            _, _, result, msg = event
            self.active = max(0, self.active - 1)
            task.state, task.msg = result, msg
            self.remove_glow(row)
            row.finish()
            self.pump()

    # ------------------------------------------------------------------ çıkış

    def on_close(self):
        busy = self.active or self.pending
        if busy:
            if not messagebox.askyesno(self.t("dlg_exit_title"), self.t("dlg_exit")):
                return
            self.stop_all()
        self.save_settings()
        self.destroy()


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
