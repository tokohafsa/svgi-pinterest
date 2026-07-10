# SVGI Pinterest Pipeline

Instagram → Dropbox → Pinterest CSV automation for logo animation niche.

## Deploy ke Streamlit Cloud

### 1. Push ke GitHub
```bash
git init
git add .
git commit -m "init svgi pinterest tool"
git remote add origin https://github.com/USERNAME/svgi-pinterest.git
git push -u origin main
```

> ⚠️ Pastikan `.streamlit/secrets.toml` masuk ke `.gitignore` — jangan pernah di-push ke GitHub.

### 2. Deploy di Streamlit Cloud
- Buka https://share.streamlit.io
- Klik **New app** → Connect GitHub repo
- Main file path: `app.py`
- Klik **Deploy**

### 3. Isi Secrets
Setelah deploy, buka **Settings → Secrets** dan paste:

```toml
GROQ_API_KEY = "isi-groq-api-key-kamu"
DROPBOX_TOKEN = "isi-dropbox-token-kamu"
DROPBOX_FOLDER = "/"
AFFILIATE_LINK = ""
```

### 4. Done — app online di URL Streamlit kamu

---

## Workflow per sesi

1. Paste URL Instagram reel/post
2. Klik **Fetch & Upload to Dropbox** → video otomatis didownload & diupload
3. Preview video → set thumbnail timestamp
4. Review caption & credits (auto-detect, bisa diedit)
5. Isi pin name (opsional) + pilih board + pilih sektor (opsional)
6. Klik **Generate** → review/edit title, description, keywords
7. Klik **Add to Queue**
8. Ulangi untuk URL berikutnya
9. Export CSV → toggle schedule ON/OFF → Download

---

## Format CSV Output (Pinterest bulk upload)

| Column | Keterangan |
|---|---|
| Title | {Nama} Logo Animation. {CTA} |
| Video URL | Dropbox direct link (dl=1) |
| Pinterest board | Board yang dipilih |
| Thumbnail | Timestamp (e.g. 0:04) |
| Description | SEO text + credits + CTA |
| Link | Affiliate link atau URL IG |
| Publish date | ISO format atau kosong (direct post) |
| Keywords | Comma-separated SEO keywords |

---

## Secrets Reference

| Key | Keterangan |
|---|---|
| GROQ_API_KEY | Dari https://console.groq.com |
| DROPBOX_TOKEN | Dari https://www.dropbox.com/developers/apps |
| DROPBOX_FOLDER | Path folder di App Folder (default `/`) |
| AFFILIATE_LINK | Fiverr affiliate link (kosong = pakai URL IG) |
