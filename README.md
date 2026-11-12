# Download Bot

**English** · [Türkçe](#türkçe)

---

## English

A desktop app that downloads links from YouTube, Instagram, TikTok, X, Facebook, Reddit, Vimeo, Twitch and more — **all at the same time**.

### Features

- **Multi-platform, parallel downloads:** paste links from different sites in one go. They are queued and downloaded 1–5 at a time (configurable).
- **Thumbnails:** every download card shows the video's thumbnail (for YouTube links, even before the download starts).
- Per-download progress, speed, ETA, cancel and "Show" buttons.
- Formats: best quality, 1080p, 720p, 480p, 360p, MP3, M4A.
- YouTube playlists: the whole list or a range (`1-5`, `1,3,7`).
- Batch import from a `.txt` file.
- Clean, minimal interface with dark/light theme.
- Languages: English (default), Türkçe, Deutsch, Español.
- Single `.exe`: no Python required, ffmpeg is bundled.

### Download

Get `DownloadBot.exe` from the [Releases](../../releases) page.

> Unsigned executables may trigger a Windows SmartScreen warning. Choose "More info → Run anyway".

### Build the EXE yourself (Windows)

Double-click `build.bat`. It installs the packages, downloads ffmpeg and creates `dist\DownloadBot.exe`.

On GitHub: **Actions → Build EXE → Run workflow**, or push a tag such as `v2.0.0` to attach the exe to a release.

### Run from source

```bash
pip install -r requirements.txt
python indirme_botu.py
```

When running from source, ffmpeg must be in your PATH (`winget install ffmpeg`).

### Troubleshooting

- **A download fails:** sites change often. Update yt-dlp (`pip install -U yt-dlp`) and rebuild, or download the latest release.
- **Login-required (private) content:** not supported.
- **Reset settings:** delete `%USERPROFILE%\.indirme_botu.json`.

### Disclaimer

For personal use and content you have the right to download only. You are responsible for respecting copyright and each platform's terms of service. The software is provided "as is". This project is not affiliated with or endorsed by any of the platforms mentioned.

### License

[MIT](LICENSE). Third-party components (yt-dlp, CustomTkinter, Pillow, FFmpeg) are covered by their own licenses, listed in the app under **Settings → Third-party notices**. The FFmpeg build bundled in the exe is GPL-licensed; if you redistribute the exe, comply with FFmpeg's license terms too (source: https://ffmpeg.org).

---

## Türkçe

YouTube, Instagram, TikTok, X, Facebook, Reddit, Vimeo, Twitch ve daha fazlasından linkleri **aynı anda** indiren masaüstü programı.

### Özellikler

- **Çoklu platform, paralel indirme:** farklı sitelerden linkleri tek seferde yapıştır. Linkler kuyruğa girer ve aynı anda 1–5 tanesi iner (ayarlanabilir).
- **Küçük resim:** her indirme kartında videonun kapak görseli görünür (YouTube linklerinde indirme başlamadan bile).
- Her indirme için canlı ilerleme, hız, kalan süre, iptal ve "Göster" düğmeleri.
- Formatlar: en iyi kalite, 1080p, 720p, 480p, 360p, MP3, M4A.
- YouTube oynatma listeleri: tüm liste ya da aralık (`1-5`, `1,3,7`).
- `.txt` dosyasından toplu link yükleme.
- Sade ve profesyonel arayüz, koyu/açık tema.
- Diller: English (varsayılan), Türkçe, Deutsch, Español.
- Tek `.exe`: Python gerekmez, ffmpeg içinde gömülüdür.

### İndir

`DownloadBot.exe` dosyasını [Releases](../../releases) sayfasından indir.

> İmzasız exe dosyalarında Windows SmartScreen uyarısı çıkabilir. "Ek bilgi → Yine de çalıştır" seçeneğini kullan.

### EXE'yi kendin oluştur (Windows)

`build.bat` dosyasına çift tıkla. Paketleri kurar, ffmpeg'i indirir ve `dist\DownloadBot.exe` dosyasını oluşturur.

GitHub'da: **Actions → Build EXE → Run workflow** ya da `v2.0.0` gibi bir etiket gönder; exe release'e eklenir.

### Kaynaktan çalıştırma

```bash
pip install -r requirements.txt
python indirme_botu.py
```

Kaynaktan çalıştırırken ffmpeg PATH'te olmalıdır (`winget install ffmpeg`).

### Sorun giderme

- **İndirme hata veriyor:** siteler sık değişir. yt-dlp'yi güncelle (`pip install -U yt-dlp`) ve yeniden build et, ya da en son sürümü indir.
- **Giriş isteyen (özel) içerikler:** desteklenmez.
- **Ayarları sıfırlamak:** `%USERPROFILE%\.indirme_botu.json` dosyasını sil.

### Yasal uyarı

Yalnızca kişisel kullanım ve indirme hakkına sahip olduğun içerikler içindir. Telif haklarına ve platformların kullanım şartlarına uymak senin sorumluluğundadır. Yazılım "olduğu gibi" sunulur. Bu proje, adı geçen platformlarla bağlantılı değildir ve onlar tarafından onaylanmamıştır.

### Lisans

[MIT](LICENSE). Üçüncü taraf bileşenler (yt-dlp, CustomTkinter, Pillow, FFmpeg) kendi lisanslarına tabidir; uygulamada **Settings → Third-party notices** bölümünde listelenir. Exe içine gömülen FFmpeg derlemesi GPL lisanslıdır; exe'yi başkalarına dağıtırsan FFmpeg'in lisans koşullarına da uy (kaynak: https://ffmpeg.org).
