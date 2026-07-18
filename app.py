import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime, date, timedelta
import io

from utils.instagram import fetch_ig_metadata, download_ig_video
from utils.dropbox_client import upload_and_get_link, upload_csv
from utils.model import detect_credits, generate_content, SECTORS, BOARD_TITLE_SUFFIX
from utils.scheduler import generate_schedule
from utils.thumbnail import extract_frames, format_timestamp
from utils.media import download_direct, convert_to_mp4, get_duration

st.set_page_config(page_title="SVGI Pinterest Tool", page_icon="🎬", layout="wide")

# ── Secrets ───────────────────────────────────────────────────────────────────
try:
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
    DROPBOX_TOKEN = st.secrets.get("DROPBOX_TOKEN", "")
    DROPBOX_APP_KEY = st.secrets.get("DROPBOX_APP_KEY", "")
    DROPBOX_APP_SECRET = st.secrets.get("DROPBOX_APP_SECRET", "")
    DROPBOX_REFRESH_TOKEN = st.secrets.get("DROPBOX_REFRESH_TOKEN", "")
    DROPBOX_FOLDER = st.secrets.get("DROPBOX_FOLDER", "/")
    AFFILIATE_LINK = st.secrets.get("AFFILIATE_LINK", "")
except Exception:
    st.error("⚠️ Secrets not configured. Edit .streamlit/secrets.toml")
    st.stop()

def _clear_ig_fields():
    """Hapus semua widget keys tab Instagram dari session_state."""
    for k in [
        "ig_url_input", "ig_brand", "ig_client", "ig_anim", "ig_logo",
        "ig_pin_name", "ig_board", "ig_sector",
        "ig_title", "ig_desc", "ig_kw",
    ]:
        if k in st.session_state:
            del st.session_state[k]


def _clear_direct_fields():
    """Hapus semua widget keys tab Direct URL dari session_state."""
    for k in [
        "direct_url_input", "dt_pin_name", "dt_board", "dt_sector",
        "dt_credit", "dt_link",
        "dt_title", "dt_desc", "dt_kw",
    ]:
        if k in st.session_state:
            del st.session_state[k]


BOARDS = [
    "Logo Animations",
    "E Sports Gaming Logo Animations",
    "Famous Brand Logo Animations",
    "Brand Identity in Motion",
]

CSV_COLUMNS = ["Title", "Video URL", "Pinterest board", "Thumbnail",
               "Description", "Link", "Publish date", "Keywords"]

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in {
    "pins": [],
    "cta_counter": 0,
    "stage": "input",
    "current": {},
    "stage_direct": "input",
    "current_direct": {},
    "session_folder": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🎬 SVGI Pinterest Pipeline")

col_hdr, col_new = st.columns([4, 1])
with col_hdr:
    if st.session_state.session_folder:
        st.caption(f"📁 Session folder: `{st.session_state.session_folder}`")
    else:
        st.caption("No active session. Click **New Session** to start.")
with col_new:
    if st.button("🆕 New Session", type="primary"):
        today_str = date.today().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H%M")
        st.session_state.session_folder = f"/{today_str}_{time_str}"
        st.session_state.pins = []
        st.session_state.cta_counter = 0
        st.session_state.stage = "input"
        st.session_state.current = {}
        st.session_state.stage_direct = "input"
        st.session_state.current_direct = {}
        if "csv_uploaded_path" in st.session_state:
            del st.session_state["csv_uploaded_path"]
        st.rerun()

if not st.session_state.session_folder:
    st.info("👆 Click **New Session** to create a dated folder in Dropbox and start adding pins.")
    st.stop()

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_ig, tab_direct = st.tabs(["📱 Instagram Source", "🌐 Direct URL Source"])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — INSTAGRAM PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════
with tab_ig:
    st.subheader("① Instagram URL")
    ig_url = st.text_input("Paste Instagram post / reel URL",
                            placeholder="https://www.instagram.com/reel/xxx",
                            key="ig_url_input")

    if ig_url and st.button("🔽 Fetch & Upload to Dropbox", type="primary", key="ig_fetch_btn"):
        st.session_state.current = {}
        st.session_state.stage = "input"

        with st.spinner("Fetching metadata from Instagram..."):
            try:
                meta = fetch_ig_metadata(ig_url)
            except Exception as e:
                st.error(f"❌ Fetch failed: {e}")
                st.stop()

        with st.spinner("Downloading video..."):
            try:
                tmpdir = tempfile.mkdtemp()
                video_path = download_ig_video(ig_url, tmpdir)
            except Exception as e:
                st.error(f"❌ Download failed: {e}")
                st.stop()

        with st.spinner("Uploading to Dropbox..."):
            try:
                video_url = upload_and_get_link(
                    video_path, st.session_state.session_folder,
                    token=DROPBOX_TOKEN,
                    app_key=DROPBOX_APP_KEY,
                    app_secret=DROPBOX_APP_SECRET,
                    refresh_token=DROPBOX_REFRESH_TOKEN,
                )
            except Exception as e:
                st.error(f"❌ Dropbox upload failed: {e}")
                st.stop()

        with st.spinner("Detecting credits from caption..."):
            credits = detect_credits(
                caption=meta.get("description", ""),
                uploader_id=meta.get("uploader_id", ""),
                api_key=GROQ_KEY,
            )

        duration = int(meta.get("duration") or 15)
        max_sec = min(duration, 30)
        thumb_secs = list(range(2, max_sec + 1))

        with st.spinner("Extracting thumbnail previews..."):
            frames = extract_frames(video_path, thumb_secs)

        st.session_state.current = {
            "ig_url": ig_url,
            "video_url": video_url,
            "caption": meta.get("description", ""),
            "uploader_id": meta.get("uploader_id", ""),
            "duration": duration,
            "frames": frames,
            "thumb_secs": thumb_secs,
            **credits,
        }
        st.session_state.stage = "uploaded"
        st.rerun()

    if st.session_state.stage in ("uploaded", "generated"):
        cur = st.session_state.current

        st.divider()
        st.subheader("② Preview")
        st.markdown("<style>video { max-height: 280px; }</style>", unsafe_allow_html=True)
        col_v, _ = st.columns([1, 2])
        with col_v:
            st.video(cur["video_url"])
            st.link_button("🎬 Open in browser (Safari)", url=cur["video_url"])

        st.divider()
        st.subheader("Thumbnail timestamp")
        frames = cur.get("frames", {})
        thumb_secs = cur.get("thumb_secs", [])
        selected_ts = cur.get("thumbnail", format_timestamp(thumb_secs[2]) if len(thumb_secs) > 2 else "0:04")

        if frames and len(frames) > 0:
            st.caption("Click a frame to select thumbnail:")
            COLS_PER_ROW = 4
            secs_list = [s for s in thumb_secs if s in frames]
            for row_start in range(0, len(secs_list), COLS_PER_ROW):
                row_secs = secs_list[row_start:row_start + COLS_PER_ROW]
                cols = st.columns(COLS_PER_ROW)
                for i, sec in enumerate(row_secs):
                    ts = format_timestamp(sec)
                    is_selected = (ts == selected_ts)
                    border_color = "#E03C31" if is_selected else "#cccccc"
                    with cols[i]:
                        st.markdown(
                            f'<div style="text-align:center">' +
                            f'<img src="data:image/jpeg;base64,{frames[sec]}" ' +
                            f'style="width:100%;border-radius:4px;border:3px solid {border_color}"/>' +
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        if st.button(ts, key=f"ig_tb_{sec}", use_container_width=True):
                            cur["thumbnail"] = ts
                            st.rerun()
            st.caption(f"✅ Selected: **{selected_ts}**")
        else:
            opts = [format_timestamp(s) for s in range(2, min(cur.get("duration", 15) + 1, 31))] or ["0:02","0:03","0:04","0:05"]
            prev = cur.get("thumbnail", opts[min(2, len(opts)-1)])
            thumbnail = st.radio("Select second", opts, index=opts.index(prev) if prev in opts else 0, horizontal=True, key="ig_thumb_radio")
            cur["thumbnail"] = thumbnail

        st.divider()
        st.subheader("③ Raw Caption")
        st.text_area("Caption from Instagram", value=cur["caption"], height=100, disabled=True)

        st.divider()
        st.subheader("④ Credits (auto-detected, editable)")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            cur["brand_name"] = st.text_input("Brand Name", value=cur.get("brand_name", ""), key="ig_brand")
        with col2:
            cur["client"] = st.text_input("Client @", value=cur.get("client") or "", key="ig_client")
        with col3:
            cur["animator"] = st.text_input("Animator @", value=cur.get("animator") or "", key="ig_anim")
        with col4:
            cur["logo_maker"] = st.text_input("Logo Maker @", value=cur.get("logo_maker") or "", key="ig_logo")

        st.divider()
        st.subheader("⑤ Pin Details")
        col_a, col_b, col_c = st.columns([2, 2, 2])
        with col_a:
            custom_name = st.text_input("Pin name (optional)", value=cur.get("custom_name", cur.get("brand_name", "")), key="ig_pin_name")
            pin_title = f"{custom_name or cur.get('brand_name', 'Logo')} Logo Animation"
            st.caption(f"→ **{pin_title}**")
            cur["custom_name"] = custom_name
        with col_b:
            board = st.selectbox("Pinterest Board", BOARDS,
                                  index=BOARDS.index(cur.get("board", BOARDS[0])) if cur.get("board") in BOARDS else 0,
                                  key="ig_board")
            cur["board"] = board
        with col_c:
            sector = st.selectbox("Sector (optional)", SECTORS,
                                   index=SECTORS.index(cur.get("sector", "")) if cur.get("sector", "") in SECTORS else 0,
                                   key="ig_sector")
            cur["sector"] = sector

        gen_label = "🔄 Regenerate" if st.session_state.stage == "generated" else "✨ Generate Description & Keywords"
        if st.button(gen_label, type="primary", key="ig_gen_btn"):
            with st.spinner("Generating SEO content..."):
                try:
                    result = generate_content(
                        pin_title=pin_title,
                        brand_name=cur.get("brand_name", ""),
                        client=cur.get("client") or "",
                        animator=cur.get("animator") or "",
                        logo_maker=cur.get("logo_maker") or "",
                        board=board,
                        caption=cur["caption"],
                        api_key=GROQ_KEY,
                        cta_index=st.session_state.cta_counter,
                        sector=cur.get("sector", ""),
                    )
                    cur.update(result)
                    st.session_state.stage = "generated"
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")

        if st.session_state.stage == "generated" and cur.get("description"):
            st.divider()
            st.subheader("⑥ Generated Content (editable)")
            cur["title"] = st.text_input("Title", value=cur.get("title", ""), max_chars=100, key="ig_title")
            cur["description"] = st.text_area("Description", value=cur.get("description", ""), height=160, key="ig_desc")
            cur["keywords"] = st.text_input("Keywords", value=cur.get("keywords", ""), key="ig_kw")

            link_field = AFFILIATE_LINK if AFFILIATE_LINK else cur["ig_url"]

            st.divider()
            if st.button("➕ Add to Queue", type="primary", key="ig_add_btn"):
                st.session_state.pins.append({
                    "Title": cur["title"],
                    "Video URL": cur["video_url"],
                    "Pinterest board": cur["board"],
                    "Thumbnail": cur.get("thumbnail", "0:04"),
                    "Description": cur["description"],
                    "Link": link_field,
                    "Publish date": "",
                    "Keywords": cur["keywords"],
                })
                st.session_state.cta_counter += 1
                st.session_state.stage = "input"
                st.session_state.current = {"frames": {}, "thumb_secs": []}
                _clear_ig_fields()
                st.success(f"✅ Pin added! Total: {len(st.session_state.pins)}")
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DIRECT URL PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════
with tab_direct:
    st.subheader("① Media URL")
    direct_url = st.text_input(
        "Paste direct media URL",
        placeholder="https://example.com/video.mp4",
        key="direct_url_input"
    )

    if direct_url and st.button("🔽 Fetch Preview", type="primary", key="direct_fetch_btn"):
        st.session_state.current_direct = {}
        st.session_state.stage_direct = "input"

        tmpdir = tempfile.mkdtemp()
        is_gif = direct_url.split("?")[0].lower().endswith(".gif")

        if is_gif:
            with st.spinner("Downloading GIF..."):
                try:
                    raw_path = download_direct(direct_url, tmpdir)
                except Exception as e:
                    st.error(f"❌ Download failed: {e}")
                    st.stop()

            with st.spinner("Converting GIF → MP4..."):
                try:
                    # Unique filename per URL to prevent stacking
                    import hashlib
                    url_hash = hashlib.md5(direct_url.encode()).hexdigest()[:8]
                    gif_mp4_name = f"gif_{url_hash}.mp4"
                    video_path = convert_to_mp4(raw_path, tmpdir, output_name=gif_mp4_name)
                    st.info("✅ GIF converted to MP4")
                except Exception as e:
                    st.error(f"❌ GIF conversion failed: {e}")
                    st.stop()

            with st.spinner("Uploading to Dropbox..."):
                try:
                    video_url = upload_and_get_link(
                        video_path, st.session_state.session_folder,
                        token=DROPBOX_TOKEN,
                        app_key=DROPBOX_APP_KEY,
                        app_secret=DROPBOX_APP_SECRET,
                        refresh_token=DROPBOX_REFRESH_TOKEN,
                    )
                except Exception as e:
                    st.error(f"❌ Dropbox upload failed: {e}")
                    st.stop()
        else:
            # MP4 — use direct URL, no Dropbox upload needed
            video_path_for_thumb = None
            with st.spinner("Downloading MP4 for preview..."):
                try:
                    video_path_for_thumb = download_direct(direct_url, tmpdir)
                except Exception as e:
                    st.error(f"❌ Download failed: {e}")
                    st.stop()
            video_path = video_path_for_thumb
            video_url = direct_url  # Pinterest fetches directly from source URL

        with st.spinner("Extracting thumbnail previews..."):
            duration = get_duration(video_path)
            max_sec = min(duration, 30)
            thumb_secs = list(range(2, max_sec + 1))
            frames = extract_frames(video_path, thumb_secs)

        st.session_state.current_direct = {
            "media_url": direct_url,
            "video_url": video_url,
            "duration": duration,
            "frames": frames,
            "thumb_secs": thumb_secs,
            "is_gif": is_gif,
        }
        st.session_state.stage_direct = "fetched"
        st.rerun()

    if st.session_state.stage_direct in ("fetched", "generated"):
        cur = st.session_state.current_direct

        st.divider()
        st.subheader("② Preview")
        st.markdown("<style>video { max-height: 280px; }</style>", unsafe_allow_html=True)
        col_v, _ = st.columns([1, 2])
        with col_v:
            st.video(cur.get("video_url", cur.get("media_url", "")))
            st.link_button("🎬 Open in browser (Safari)", url=cur.get("video_url", cur.get("media_url", "")))

        st.divider()
        st.subheader("Thumbnail timestamp")
        frames = cur.get("frames", {})
        thumb_secs = cur.get("thumb_secs", [])
        selected_ts = cur.get("thumbnail", format_timestamp(thumb_secs[2]) if len(thumb_secs) > 2 else "0:04")

        if frames and len(frames) > 0:
            st.caption("Click a frame to select thumbnail:")
            COLS_PER_ROW = 4
            secs_list = [s for s in thumb_secs if s in frames]
            for row_start in range(0, len(secs_list), COLS_PER_ROW):
                row_secs = secs_list[row_start:row_start + COLS_PER_ROW]
                cols = st.columns(COLS_PER_ROW)
                for i, sec in enumerate(row_secs):
                    ts = format_timestamp(sec)
                    is_selected = (ts == selected_ts)
                    border_color = "#E03C31" if is_selected else "#cccccc"
                    with cols[i]:
                        st.markdown(
                            f'<div style="text-align:center">' +
                            f'<img src="data:image/jpeg;base64,{frames[sec]}" ' +
                            f'style="width:100%;border-radius:4px;border:3px solid {border_color}"/>' +
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        if st.button(ts, key=f"dt_tb_{sec}", use_container_width=True):
                            cur["thumbnail"] = ts
                            st.rerun()
            st.caption(f"✅ Selected: **{selected_ts}**")
        else:
            opts = [format_timestamp(s) for s in range(2, min(cur.get("duration", 15) + 1, 31))] or ["0:02","0:03","0:04","0:05"]
            prev = cur.get("thumbnail", opts[min(2, len(opts)-1)])
            thumbnail = st.radio("Select second", opts, index=opts.index(prev) if prev in opts else 0, horizontal=True, key="dt_thumb_radio")
            cur["thumbnail"] = thumbnail

        st.divider()
        st.subheader("③ Pin Details")
        col_a, col_b, col_c = st.columns([2, 2, 2])
        with col_a:
            pin_name = st.text_input("Pin name", placeholder="e.g. Nike", key="dt_pin_name",
                                      value=cur.get("pin_name", ""))
            suffix = BOARD_TITLE_SUFFIX.get(cur.get("board", "Logo Animations"), "Logo Animation")
            pin_title = f"{pin_name} {suffix}" if pin_name else suffix
            st.caption(f"→ **{pin_title}**")
            cur["pin_name"] = pin_name
        with col_b:
            board = st.selectbox("Pinterest Board", BOARDS,
                                  index=BOARDS.index(cur.get("board", BOARDS[0])) if cur.get("board") in BOARDS else 0,
                                  key="dt_board")
            cur["board"] = board
        with col_c:
            sector = st.selectbox("Sector (optional)", SECTORS,
                                   index=SECTORS.index(cur.get("sector", "")) if cur.get("sector", "") in SECTORS else 0,
                                   key="dt_sector")
            cur["sector"] = sector

        st.divider()
        st.subheader("④ Credit & Link")
        col_cr, col_lk = st.columns(2)
        with col_cr:
            credit = st.text_input("Credit", placeholder="e.g. Motion by @username | Logo by @designer",
                                    value=cur.get("credit", ""), key="dt_credit")
            cur["credit"] = credit
        with col_lk:
            source_link = st.text_input("Link to original content", placeholder="https://...",
                                         value=cur.get("source_link", ""), key="dt_link")
            cur["source_link"] = source_link

        gen_label = "🔄 Regenerate" if st.session_state.stage_direct == "generated" else "✨ Generate Description & Keywords"
        if st.button(gen_label, type="primary", key="dt_gen_btn"):
            with st.spinner("Generating SEO content..."):
                try:
                    result = generate_content(
                        pin_title=pin_title,
                        brand_name=pin_name,
                        client="",
                        animator=credit,
                        logo_maker="",
                        board=board,
                        caption=credit,
                        api_key=GROQ_KEY,
                        cta_index=st.session_state.cta_counter,
                        sector=cur.get("sector", ""),
                    )
                    # Override description credit line with user's manual credit
                    desc = result.get("description", "")
                    if credit:
                        lines = desc.split("\n")
                        credit_stripped = credit.strip()
                        # Tambah prefix "Credit: " kalau belum ada
                        if not credit_stripped.lower().startswith("credit:"):
                            lines[0] = f"Credit: {credit_stripped}"
                        else:
                            lines[0] = credit_stripped
                        desc = "\n".join(lines)
                    result["description"] = desc
                    cur.update(result)
                    st.session_state.stage_direct = "generated"
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")

        if st.session_state.stage_direct == "generated" and cur.get("description"):
            st.divider()
            st.subheader("⑤ Generated Content (editable)")
            cur["title"] = st.text_input("Title", value=cur.get("title", ""), max_chars=100, key="dt_title")
            cur["description"] = st.text_area("Description", value=cur.get("description", ""), height=160, key="dt_desc")
            cur["keywords"] = st.text_input("Keywords", value=cur.get("keywords", ""), key="dt_kw")

            st.divider()
            if st.button("➕ Add to Queue", type="primary", key="dt_add_btn"):
                st.session_state.pins.append({
                    "Title": cur["title"],
                    "Video URL": cur.get("video_url", cur.get("media_url", "")),
                    "Pinterest board": cur["board"],
                    "Thumbnail": cur.get("thumbnail", "0:04"),
                    "Description": cur["description"],
                    "Link": cur.get("source_link", ""),
                    "Publish date": "",
                    "Keywords": cur["keywords"],
                })
                st.session_state.cta_counter += 1
                st.session_state.stage_direct = "input"
                st.session_state.current_direct = {"frames": {}, "thumb_secs": []}
                _clear_direct_fields()
                st.success(f"✅ Pin added! Total: {len(st.session_state.pins)}")
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# QUEUE & EXPORT (shared)
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.pins:
    st.divider()
    st.subheader(f"📋 Queue — {len(st.session_state.pins)} pin(s)")

    df = pd.DataFrame(st.session_state.pins, columns=CSV_COLUMNS)
    st.dataframe(df, width=1400, column_config={
        "Description": st.column_config.TextColumn(width="large"),
        "Keywords": st.column_config.TextColumn(width="large"),
    })

    st.divider()
    st.subheader("📅 Export CSV")

    use_schedule = st.toggle("Enable scheduling", value=False,
                              help="OFF = Publish date kosong. ON = randomize dalam rentang tanggal.")
    if use_schedule:
        col1, col2 = st.columns(2)
        with col1:
            sched_start = st.date_input("Start date", value=date.today() + timedelta(days=1))
        with col2:
            sched_end = st.date_input("End date", value=date.today() + timedelta(days=14))
    else:
        sched_start = date.today() + timedelta(days=1)
        sched_end = date.today() + timedelta(days=14)

    # Detect if queue has NON-IG pins for naming
    has_direct = any(not p.get("Link", "").startswith("https://www.instagram.com") for p in st.session_state.pins)
    has_ig = any(p.get("Link", "").startswith("https://www.instagram.com") for p in st.session_state.pins)
    if has_direct and has_ig:
        csv_prefix = "bulk_logo_mixed"
    elif has_direct:
        csv_prefix = "bulk_logo_NON-IG"
    else:
        csv_prefix = "bulk_logo"

    col_exp, col_clr = st.columns([3, 1])
    with col_exp:
        if st.button("📥 Export CSV", type="primary", key="export_btn"):
            try:
                pins_now = st.session_state.pins
                if not pins_now:
                    st.warning("Queue is empty.")
                else:
                    export = []
                    if use_schedule:
                        start_dt = datetime.combine(sched_start, datetime.min.time())
                        end_dt = datetime.combine(sched_end, datetime.min.time())
                        schedules = generate_schedule(start_dt, end_dt, len(pins_now))
                        for i, pin in enumerate(pins_now):
                            p = {c: pin.get(c, "") for c in CSV_COLUMNS}
                            p["Publish date"] = schedules[i]
                            export.append(p)
                    else:
                        for pin in pins_now:
                            p = {c: pin.get(c, "") for c in CSV_COLUMNS}
                            p["Publish date"] = ""
                            export.append(p)

                    df_export = pd.DataFrame(export, columns=CSV_COLUMNS)
                    buf = io.StringIO()
                    df_export.to_csv(buf, index=False)
                    csv_bytes = buf.getvalue().encode("utf-8")

                    folder_name = st.session_state.session_folder.strip("/")
                    fname = f"{csv_prefix}_{folder_name}.csv"

                    dropbox_path = upload_csv(
                        csv_bytes, fname, st.session_state.session_folder,
                        token=DROPBOX_TOKEN,
                        app_key=DROPBOX_APP_KEY,
                        app_secret=DROPBOX_APP_SECRET,
                        refresh_token=DROPBOX_REFRESH_TOKEN,
                    )

                    st.session_state["csv_uploaded_path"] = dropbox_path
                    st.session_state["csv_fname"] = fname
                    st.session_state.pins = export
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Export error: {e}")

        if "csv_uploaded_path" in st.session_state:
            st.success(f"✅ CSV saved to Dropbox: `{st.session_state['csv_uploaded_path']}`")
            col_dl, col_pin = st.columns([1, 1])
            with col_dl:
                st.info(f"📁 File: **{st.session_state['csv_fname']}**")
            with col_pin:
                st.link_button("📌 Upload to Pinterest",
                                url="https://www.pinterest.com/settings/bulk-create-pins/")
    with col_clr:
        if st.button("🗑️ Clear Queue", key="clr_btn"):
            st.session_state.pins = []
            if "csv_uploaded_path" in st.session_state:
                del st.session_state["csv_uploaded_path"]
            st.rerun()
