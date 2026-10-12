# 🎬 SVGI Pinterest Pipeline

Streamlit app untuk mengotomasi pipeline konten logo animation dari Instagram dan direct URL ke Pinterest via CSV bulk upload.

---

## Struktur File

```
svgi-pinterest/
├── app.py                        # Main app — 2 tab pipeline
├── requirements.txt
├── .gitignore
├── svgi_pinterest_memory.txt     # Project memory lintas sesi
├── .streamlit/
│   ├── config.toml               # Light theme, sage green
│   └── secrets.toml              # Tidak di-push ke GitHub
└── utils/
    ├── __init__.py
    ├── instagram.py              # yt-dlp fetch, download, carousel fix
    ├── dropbox_client.py         # Upload video dan CSV ke Dropbox
    ├── dropbox_autosave.py       # Auto-save dan restore queue ke Dropbox
    ├── model.py                  # Gemini: detect credits, generate SEO, CTA title
    ├── scheduler.py              # Distribute publish dates dalam rentang waktu
    ├── thumbnail.py              # ffmpeg extract frames → base64 jpeg
    └── media.py                  # Download direct URL, convert GIF→MP4, get duration
```

---

## Setup

### 1. Clone dan push ke GitHub

```bash
git clone https://github.com/tokohafsa/svgi-pinterest.git
cd svgi-pinterest
```

### 2. Isi Secrets

Buat `.streamlit/secrets.toml` (tidak di-push):

```toml
GEMINI_API_KEY     = "your-gemini-api-key"
DROPBOX_TOKEN      = ""
DROPBOX_APP_KEY    = "l1c50p00605pykv"
DROPBOX_APP_SECRET = "your-app-secret"
DROPBOX_REFRESH_TOKEN = "your-refresh-token"
```

Di Streamlit Cloud: **Settings → Secrets** → paste isi di atas.

### 3. Deploy

- Push ke GitHub → Streamlit Cloud auto-reboot
- Repo: `tokohafsa/svgi-pinterest` (public)
- Main file: `app.py`

---

## Requirements

```
streamlit>=1.35.0
yt-dlp>=2024.1.0
dropbox>=11.36.0
pandas>=2.0.0
requests>=2.31.0
imageio-ffmpeg>=0.4.9
google-genai>=0.8.0
```

---

## Pipeline — Tab 1: Instagram Source

| Step | Aksi |
|------|------|
| 0 | Klik **New Session** → buat folder Dropbox `/SVGI/2026-07-29_1430` |
| 1 | Paste URL Instagram reel/post (support carousel `?img_index=N`) |
| 2 | Fetch metadata + download video via yt-dlp |
| 3 | Upload video ke Dropbox (folder session) |
| 4 | Extract frame thumbnail detik 1–30 via ffmpeg |
| 5 | Preview video + klik thumbnail untuk pilih timestamp |
| 6 | Review raw caption (read-only) |
| 7 | Edit credits: Poster @ + @Mentions (auto-detect dari caption, editable) |
| 8 | Input pin name + pilih Board + pilih Sector |
| 9 | Generate → review/edit Title, Description, Keywords |
| 10 | Add to Queue → auto-save ke Dropbox |
| 11 | Loop ke step 1 untuk pin berikutnya |
| 12 | Generate CSV Preview → Edit → Upload ke Dropbox |

---

## Pipeline — Tab 2: Direct URL Source

| Step | Aksi |
|------|------|
| 1 | Paste direct URL `.mp4` / `.mov` / `.gif` (Dropbox `dl=0` otomatis jadi `dl=1`) |
| 2 | Download + convert GIF→MP4 via ffmpeg (jika GIF) |
| 3 | MP4: pakai URL asli langsung, tidak re-upload ke Dropbox |
| 4 | GIF: upload hasil konversi ke Dropbox dengan nama unik per URL |
| 5 | Extract frame thumbnail + preview |
| 6 | Input: nama pin, credit animator (plain text), link ke konten asli |
| 7 | Pilih Board + Sector |
| 8 | Generate → review/edit → Add to Queue |

---

## Auto-Save & Restore Queue

Queue otomatis tersimpan ke Dropbox (`queue_backup.json` di folder session) setiap kali pin ditambahkan.

Jika Streamlit reset session:
1. Klik expander **"🔄 Restore previous session"**
2. Klik **"Search backups in Dropbox"**
3. Pilih backup → klik **Restore**

---

## Format Konten

### Title
```
{Nama} {Suffix Board}. {CTA Title — Gemini generated}
```

**Suffix per board:**
| Board | Suffix |
|-------|--------|
| Logo Animations | Logo Animation |
| E Sports Gaming Logo Animations | Logo Animation |
| Famous Brand Logo Animations | Logo Animation |
| Brand Identity in Motion | Animated Brand Identity |

CTA title di-generate Gemini per pin (bukan hardcoded) dengan budget karakter dinamis agar total title ≤ 100 karakter.

### Description
```
Line 1: {credit_line}
Line 2-3: seo_body (2 kalimat SEO natural, max 200 chars)
Line 4: {cta_desc — rotasi 14 variasi soft-sell}
```

**Format credit line:**
- Ada @mention: `Credit: @mention1 @mention2 | from @poster on Instagram`
- Tidak ada @mention: `Credit: @poster on Instagram`
- Tab Direct: `Credit: {nama animator} on Fiverr`

**Aturan konten:**
- Title tidak diulang di description
- Tidak menyebut 3D / three-dimensional
- Board "Brand Identity in Motion": seo_body fokus ke brand system dan visual identity, bukan logo reveal

---

## Boards

- Logo Animations
- E Sports Gaming Logo Animations
- Famous Brand Logo Animations
- Brand Identity in Motion

---

## Sectors (49 pilihan)

**General (33):** Automotive, Aviation, Beauty, Construction, Crypto, Education, Entertainment, E-Sports, Fashion, Finance, Food, Government, Health, Hotels, Insurance, Law, Logistics, Luxury, Manufacturing, Music, NFT, Non-Profit, Outdoor, Pets, Photography, Religion, Retail, Software, Sports, Technology, Telecommunications, Travel, YouTube

**Mobile App (10):** Mobile App & Startup, Fintech & Mobile Banking, Food Delivery & Restaurant App, Health & Fitness App, Dating & Social App, Productivity & SaaS App, E-Commerce & Marketplace App, Gaming & Mobile Gaming, Education & Learning App, Travel & Navigation App

**Agency & Creative (15):** Branding & Design Agency, Motion Design Studio, Video Production Studio, Creative Agency, Social Media Agency, Marketing Agency, Advertising Agency, UI/UX Design Studio, 3D & VFX Studio, Illustration & Art Studio, Photography Studio, PR & Communications Agency, Content Creation Agency, Freelance Designer, Independent Animator

---

## Export CSV

3 langkah terpisah:

**Step 1 — Generate CSV Preview**
- Toggle scheduling ON/OFF
- Pilih start date + end date (jika ON)
  - Start = hari ini → mulai dari sekarang + 2 jam
  - Start = besok atau lebih → mulai dari 02:00 pagi
- Pin di-shuffle secara acak sebelum jadwal di-assign
- Klik "Generate CSV Preview" — tidak langsung upload

**Step 2 — Edit CSV**
- Semua kolom editable langsung di tabel

**Step 3 — Upload ke Dropbox**
- Klik "Upload CSV ke Dropbox"
- Tampil path Dropbox + tombol langsung ke Pinterest Bulk Upload

**Penamaan file CSV:**
| Isi Queue | Nama File |
|-----------|-----------|
| Semua IG | `bulk_logo_{session}.csv` |
| Semua Direct | `NON-IG_bulk_logo_{session}.csv` |
| Campuran | `bulk_logo_mixed_{session}.csv` |

**Kolom CSV:**
`Title, Video URL, Pinterest board, Thumbnail, Description, Link, Publish date, Keywords`

---

## Dropbox Config

| Setting | Value |
|---------|-------|
| Permission | Scoped App (App Folder) |
| App Folder | `/Apps/SVGI Pinterest/` |
| Session folder | `/SVGI/{tanggal}_{waktu}` |
| Auth | OAuth2 Refresh Token (permanent) |
| App key | `l1c50p00605pykv` |
| Link format | `dl.dropboxusercontent.com?dl=1` |

---

## AI Model

**Google Gemini (`gemini-3.1-flash-lite`)** untuk:
- `detect_credits()` — deteksi poster, @mentions dari caption IG
- `generate_content()` — seo_body + keywords per board/sector
- `_generate_cta_title()` — CTA title per pin dengan budget karakter dinamis

Groq sudah dihapus sepenuhnya (deprecated Aug 2026).

---

## Carousel Instagram

URL dengan `?img_index=N` di-support:
- `_parse_img_index(url)` — ambil index N (1-based)
- `_strip_img_index(url)` — bersihkan URL sebelum kirim ke yt-dlp
- yt-dlp fetch seluruh carousel dengan `ignoreerrors=True`
- `_pick_entry(info, img_index)` — filter entry yang video, ambil index ke-N

---

## Affiliate

- Fiverr via Awin: approved ✅
- Link shortener: tidd.ly
- Strategi: affiliate di bio Pinterest saja, link pin ke konten original kreator
