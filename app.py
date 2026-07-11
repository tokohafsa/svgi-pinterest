import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime, date, timedelta
import io

from utils.instagram import fetch_ig_metadata, download_ig_video
from utils.dropbox_client import upload_and_get_link
from utils.model import detect_credits, generate_content, SECTORS
from utils.scheduler import generate_schedule

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

BOARDS = [
    "Logo Animations",
    "E Sports Gaming Logo Animations",
    "Famous Brand Logo Animations",
]

CSV_COLUMNS = ["Title", "Video URL", "Pinterest board", "Thumbnail",
               "Description", "Link", "Publish date", "Keywords"]

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in {
    "pins": [],
    "cta_counter": 0,
    "stage": "input",       # input | uploaded | generated
    "current": {},          # working data for current pin
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🎬 SVGI Pinterest Pipeline")
st.caption("Instagram → Dropbox → Pinterest CSV")
st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 1 — URL INPUT
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("① Instagram URL")
ig_url = st.text_input("Paste Instagram post / reel URL",
                        placeholder="https://www.instagram.com/reel/xxx",
                        key="ig_url_input")

if ig_url and st.button("🔽 Fetch & Upload to Dropbox", type="primary"):
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
                                video_path, DROPBOX_FOLDER,
                                token=DROPBOX_TOKEN,
                                app_key=DROPBOX_APP_KEY,
                                app_secret=DROPBOX_APP_SECRET,
                                refresh_token=DROPBOX_REFRESH_TOKEN,
                            )
        except Exception as e:
            st.error(f"❌ Dropbox upload failed: {e}")
            st.stop()

    # Detect credits from caption
    with st.spinner("Detecting credits from caption..."):
        credits = detect_credits(
            caption=meta.get("description", ""),
            uploader_id=meta.get("uploader_id", ""),
            api_key=GROQ_KEY,
        )

    st.session_state.current = {
        "ig_url": ig_url,
        "video_url": video_url,
        "caption": meta.get("description", ""),
        "uploader_id": meta.get("uploader_id", ""),
        **credits,
    }
    st.session_state.stage = "uploaded"
    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 2 — PREVIEW + FORM
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.stage in ("uploaded", "generated"):
    cur = st.session_state.current

    st.divider()

    # Preview + Thumbnail
    col_vid, col_thumb = st.columns([1, 1])
    with col_vid:
        st.subheader("② Preview")
        st.markdown("""
            <style>
            video { max-height: 300px; }
            </style>
        """, unsafe_allow_html=True)
        st.video(cur["video_url"])
    with col_thumb:
        st.subheader("Thumbnail timestamp")
        thumbnail = st.text_input("Timestamp (e.g. 0:04)", value=cur.get("thumbnail", "0:04"), key="thumb_input")
        cur["thumbnail"] = thumbnail
        st.caption("Set the frame used as pin thumbnail")

    st.divider()

    # Raw caption
    st.subheader("③ Raw Caption")
    st.text_area("Caption from Instagram", value=cur["caption"], height=100, disabled=True)

    st.divider()

    # Credits (editable)
    st.subheader("④ Credits (auto-detected, editable)")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        cur["brand_name"] = st.text_input("Brand Name", value=cur.get("brand_name", ""))
    with col2:
        cur["client"] = st.text_input("Client @", value=cur.get("client") or "")
    with col3:
        cur["animator"] = st.text_input("Animator @", value=cur.get("animator") or "")
    with col4:
        cur["logo_maker"] = st.text_input("Logo Maker @", value=cur.get("logo_maker") or "")

    st.divider()

    # Title + Board + Sector
    st.subheader("⑤ Pin Details")
    col_a, col_b, col_c = st.columns([2, 2, 2])
    with col_a:
        custom_name = st.text_input(
            "Pin name (optional)",
            value=cur.get("custom_name", cur.get("brand_name", "")),
            help="Leave blank to use Brand Name. Final title = [name] Logo Animation"
        )
        pin_title = f"{custom_name or cur.get('brand_name', 'Logo')} Logo Animation"
        # Format: {Nama} Logo Animation
        st.caption(f"→ **{pin_title}**")
        cur["custom_name"] = custom_name
    with col_b:
        board = st.selectbox("Pinterest Board", BOARDS,
                              index=BOARDS.index(cur.get("board", BOARDS[0])) if cur.get("board") in BOARDS else 0)
        cur["board"] = board
    with col_c:
        sector = st.selectbox("Sector (optional)", SECTORS,
                               index=SECTORS.index(cur.get("sector", "")) if cur.get("sector", "") in SECTORS else 0,
                               help="Enriches SEO keywords only. Not required.")
        cur["sector"] = sector


    # Generate / Regenerate
    gen_label = "🔄 Regenerate" if st.session_state.stage == "generated" else "✨ Generate Description & Keywords"
    if st.button(gen_label, type="primary"):
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

    # Show generated result (editable)
    if st.session_state.stage == "generated" and cur.get("description"):
        st.divider()
        st.subheader("⑥ Generated Content (editable)")
        cur["title"] = st.text_input("Title", value=cur.get("title", ""), max_chars=100)
        cur["description"] = st.text_area("Description", value=cur.get("description", ""), height=160)
        cur["keywords"] = st.text_input("Keywords", value=cur.get("keywords", ""))

        link_field = AFFILIATE_LINK if AFFILIATE_LINK else cur["ig_url"]

        st.divider()
        if st.button("➕ Add to Queue", type="primary"):
            st.session_state.pins.append({
                "Title": cur["title"],
                "Video URL": cur["video_url"],
                "Pinterest board": cur["board"],
                "Thumbnail": cur["thumbnail"],
                "Description": cur["description"],
                "Link": link_field,
                "Publish date": "",
                "Keywords": cur["keywords"],
            })
            st.session_state.cta_counter += 1
            st.session_state.stage = "input"
            st.session_state.current = {}
            st.success(f"✅ Pin added! Total: {len(st.session_state.pins)}")
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# QUEUE — Editable CSV preview
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.pins:
    st.divider()
    st.subheader(f"📋 Queue — {len(st.session_state.pins)} pin(s)")

    df = pd.DataFrame(st.session_state.pins, columns=CSV_COLUMNS)
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Video URL": st.column_config.TextColumn(width="medium"),
            "Description": st.column_config.TextColumn(width="large"),
            "Keywords": st.column_config.TextColumn(width="large"),
            "Publish date": st.column_config.TextColumn(width="medium"),
        },
        key="csv_editor",
    )
    # Always sync edits back immediately
    if edited_df is not None:
        st.session_state.pins = edited_df.fillna("").to_dict("records")

    # Schedule + Export
    st.divider()
    st.subheader("📅 Export CSV")

    use_schedule = st.toggle("Enable scheduling", value=False,
                              help="OFF = Publish date kosong (direct post). ON = randomize dalam rentang tanggal.")

    if use_schedule:
        col1, col2 = st.columns(2)
        with col1:
            sched_start = st.date_input("Start date", value=date.today() + timedelta(days=1))
        with col2:
            sched_end = st.date_input("End date", value=date.today() + timedelta(days=14))

    col_exp, col_clr = st.columns([3, 1])
    with col_exp:
        if st.button("📥 Export CSV", type="primary"):
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
                            p = {col: pin.get(col, "") for col in CSV_COLUMNS}
                            p["Publish date"] = schedules[i]
                            export.append(p)
                    else:
                        for pin in pins_now:
                            p = {col: pin.get(col, "") for col in CSV_COLUMNS}
                            p["Publish date"] = ""
                            export.append(p)

                    df_export = pd.DataFrame(export, columns=CSV_COLUMNS)
                    buf = io.StringIO()
                    df_export.to_csv(buf, index=False)
                    csv_bytes = buf.getvalue().encode("utf-8")

                    fname = f"SVGI_Pinterest_{sched_start}.csv" if use_schedule else "SVGI_Pinterest.csv"
                    st.session_state["csv_ready"] = csv_bytes
                    st.session_state["csv_filename"] = fname
                    st.session_state.pins = export
                    st.rerun()
            except ValueError as e:
                st.error(f"❌ {e}")

        if "csv_ready" in st.session_state:
            col_dl, col_pin = st.columns([1, 1])
            with col_dl:
                st.download_button(
                    "⬇️ Download CSV",
                    data=st.session_state["csv_ready"],
                    file_name=st.session_state.get("csv_filename", "SVGI_Pinterest.csv"),
                    mime="text/csv",
                )
            with col_pin:
                st.link_button(
                    "📌 Upload to Pinterest",
                    url="https://www.pinterest.com/settings/bulk-create-pins/",
                )
    with col_clr:
        if st.button("🗑️ Clear Queue"):
            st.session_state.pins = []
            if "csv_ready" in st.session_state:
                del st.session_state["csv_ready"]
            st.rerun()
