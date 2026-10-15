
"""
RACHNA PLAYWOO & HARDWEAR — Streamlit catalogue and workshop accounts.
Configure credentials in Streamlit Secrets; never hard-code database credentials.
Creates separate rachna_* tables in the configured PostgreSQL database and does not modify the existing tiffin table.
"""
import io, os, hmac, base64, html, hashlib, secrets, re
from urllib.parse import urlparse
from datetime import date, timedelta
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from PIL import Image
import requests
import streamlit.components.v1 as components

APP_NAME = "RACHNA PLAYWOOD & HARDWEAR"
st.set_page_config(page_title=APP_NAME, page_icon="🪵", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap');
header[data-testid="stHeader"]{height:0!important;min-height:0!important;background:transparent!important;border:0!important;overflow:visible!important;position:relative!important}
header[data-testid="stHeader"]>div{background:transparent!important}
/* Hide Streamlit chrome, but NEVER hide the sidebar open/collapse control. */
[data-testid="stSidebarCollapsedControl"],
button[data-testid="stSidebarCollapsedControl"],
button[data-testid="stSidebarCollapseButton"]{display:flex!important;visibility:visible!important;opacity:1!important;position:fixed!important;top:10px!important;left:10px!important;z-index:2147483647!important;pointer-events:auto!important}
[data-testid="stSidebarCollapsedControl"] svg,
button[data-testid="stSidebarCollapsedControl"] svg,
button[data-testid="stSidebarCollapseButton"] svg{visibility:visible!important;opacity:1!important}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
.stApp{background:linear-gradient(135deg,#071b33,#102c50);color:#f5f0e5}
h1,h2,h3{font-family:'Cormorant Garamond',serif!important;color:#d6ae52}
.brand-title{font-family:'Cormorant Garamond',serif;font-size:clamp(2rem,5vw,4rem);font-weight:700;letter-spacing:.04em;color:#d6ae52}
.brand-sub{letter-spacing:.24em;text-transform:uppercase;color:#9b7b42;font-size:.75rem}
.hero{padding:2rem;border-radius:22px;background:linear-gradient(120deg,#071b33,#102c50);color:white;border:1px solid #d6ae52}
.hero h2{color:white!important;font-size:2.4rem}.hero p{color:#f5ead2}
div[data-testid="stMetric"]{background:#102c50;border:1px solid #d6ae52;padding:14px;border-radius:15px}
section[data-testid="stSidebar"]{background:#071b33}
section[data-testid="stSidebar"] *{color:#f5f0e5!important}
.brand-marquee{width:100%;max-width:100%;min-width:0;box-sizing:border-box;display:flex;align-items:center;gap:10px;margin:.2rem 0 1rem;overflow:visible}
.brand-logo-slot{flex:0 0 100px;width:100px;height:48px;display:flex;align-items:center;justify-content:center;overflow:hidden}
.brand-logo-slot img{width:100%;height:42px;object-fit:contain;display:block}
.brand-marquee-viewport{flex:1 1 auto;min-width:0;overflow:hidden;position:relative}
.brand-marquee .marquee-track{width:max-content;min-width:max-content;display:flex;gap:24px;animation:brand-left 24s linear infinite;will-change:transform}
.brand-marquee .marquee-track span{display:inline-block;white-space:nowrap;flex:0 0 auto}
@keyframes brand-left{from{transform:translateX(0)}to{transform:translateX(-50%)}}
.marquee-wrap{width:100%;overflow:hidden;display:flex;flex-direction:column;gap:8px;margin:0}
.marquee-row{width:100%;overflow:hidden;white-space:nowrap;display:flex}
.marquee-track{display:flex;align-items:center;gap:10px;width:max-content;min-width:max-content;animation:move-left 30s linear infinite;will-change:transform}
.marquee-row.right .marquee-track{animation-name:move-right}
.marquee-track img{height:52px;width:84px;object-fit:contain;background:#fff;border-radius:9px;padding:4px;display:block;flex:0 0 auto}
@keyframes move-left{from{transform:translateX(0)}to{transform:translateX(-50%)}}
@keyframes move-right{from{transform:translateX(-50%)}to{transform:translateX(0)}}
@media(max-width:640px){.marquee-track img{height:40px;width:66px}.brand-marquee .marquee-track{gap:14px}}
div[data-testid="stStatusWidget"]{display:none!important}
.stButton>button{border-radius:10px;border:1px solid #d6ae52;font-weight:600}
div.stButton>button[kind="primary"]{background:#071b33;color:white}
.contact-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:1rem 0}
.contact-item{display:flex;align-items:center;justify-content:center;gap:8px;padding:12px;border:1px solid #d6ae52;border-radius:14px;background:#102c50;color:#f5f0e5;text-decoration:none;font-weight:700}
.contact-icon{width:28px;height:28px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;background:#071b33;border:1px solid #d6ae52;font-size:.78rem}
@media(max-width:800px){.contact-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style></style>
""", unsafe_allow_html=True)

def cfg(key, default=""):
    try:
        val=st.secrets.get(key, default)
        if val: return str(val)
    except Exception: pass
    return os.getenv(key, default)

def github_is_configured():
    return bool(cfg("GITHUB_TOKEN") and cfg("GITHUB_OWNER") and cfg("GITHUB_REPO"))


def db_connect():
    keys=["DB_HOST","DB_NAME","DB_USER","DB_PASSWORD","DB_PORT"]
    missing=[k for k in keys if not cfg(k)]
    if missing: raise RuntimeError("Missing Streamlit Secrets: "+", ".join(missing))
    return psycopg2.connect(host=cfg("DB_HOST"),dbname=cfg("DB_NAME"),user=cfg("DB_USER"),
        password=cfg("DB_PASSWORD"),port=int(cfg("DB_PORT")),sslmode=cfg("DB_SSLMODE","require"),
        connect_timeout=8,cursor_factory=RealDictCursor)

def query(sql, params=None, fetch=True):
    conn=db_connect()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql,params or ())
                return cur.fetchall() if fetch and cur.description else cur.rowcount
    finally: conn.close()

def init_db():
    sqls=[
    """CREATE TABLE IF NOT EXISTS rachna_products(id BIGSERIAL PRIMARY KEY,title TEXT NOT NULL,category TEXT NOT NULL DEFAULT 'Furniture',price NUMERIC(12,2),material TEXT,size TEXT,color TEXT,description TEXT,is_active BOOLEAN NOT NULL DEFAULT TRUE,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""",
    """CREATE TABLE IF NOT EXISTS rachna_product_images(id BIGSERIAL PRIMARY KEY,product_id BIGINT NOT NULL REFERENCES rachna_products(id) ON DELETE CASCADE,image_data BYTEA,image_url TEXT,mime_type TEXT NOT NULL DEFAULT 'image/jpeg',image_order INTEGER NOT NULL DEFAULT 0,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""",
    """CREATE TABLE IF NOT EXISTS rachna_staff(id BIGSERIAL PRIMARY KEY,name TEXT NOT NULL UNIQUE,serial_no INTEGER UNIQUE,role TEXT DEFAULT 'Karigar',phone TEXT,daily_rate NUMERIC(12,2) NOT NULL DEFAULT 0,active BOOLEAN NOT NULL DEFAULT TRUE,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""",
    """CREATE TABLE IF NOT EXISTS rachna_attendance(id BIGSERIAL PRIMARY KEY,staff_id BIGINT NOT NULL REFERENCES rachna_staff(id) ON DELETE CASCADE,work_date DATE NOT NULL,status TEXT NOT NULL CHECK(status IN ('Present','Absent','Half Day','Full Leave')),notes TEXT,updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),UNIQUE(staff_id,work_date))""",
    """CREATE TABLE IF NOT EXISTS rachna_ledger(id BIGSERIAL PRIMARY KEY,entry_date DATE NOT NULL DEFAULT CURRENT_DATE,person_name TEXT NOT NULL,entry_type TEXT NOT NULL CHECK(entry_type IN ('Payment','Advance','Expense','Due')),amount NUMERIC(12,2) NOT NULL CHECK(amount>=0),note TEXT,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""",
    "CREATE INDEX IF NOT EXISTS idx_rachna_products_active ON rachna_products(is_active,created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_rachna_images_product ON rachna_product_images(product_id,image_order)",
    "CREATE INDEX IF NOT EXISTS idx_rachna_attendance_date ON rachna_attendance(work_date DESC)",
    "CREATE INDEX IF NOT EXISTS idx_rachna_ledger_date ON rachna_ledger(entry_date DESC)",
    """CREATE TABLE IF NOT EXISTS rachna_site_settings(setting_key TEXT PRIMARY KEY,image_data BYTEA,image_url TEXT,mime_type TEXT,text_value TEXT,updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""",
    """ALTER TABLE rachna_product_images ADD COLUMN IF NOT EXISTS image_url TEXT""",
    """ALTER TABLE rachna_product_images ADD COLUMN IF NOT EXISTS image_hash TEXT""",
    """ALTER TABLE rachna_product_images ALTER COLUMN image_data DROP NOT NULL""",
    """ALTER TABLE rachna_site_settings ADD COLUMN IF NOT EXISTS image_url TEXT""",
    """ALTER TABLE rachna_site_settings ADD COLUMN IF NOT EXISTS image_hash TEXT""",
    """CREATE INDEX IF NOT EXISTS idx_rachna_product_images_hash ON rachna_product_images(image_hash)""",
    """CREATE UNIQUE INDEX IF NOT EXISTS uq_rachna_product_image_hash
       ON rachna_product_images(product_id,image_hash)
       WHERE image_hash IS NOT NULL""",
    """CREATE INDEX IF NOT EXISTS idx_rachna_site_settings_hash ON rachna_site_settings(image_hash)""",
    """CREATE TABLE IF NOT EXISTS rachna_image_registry(
        image_hash TEXT PRIMARY KEY,
        image_url TEXT NOT NULL,
        folder TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""",
"""ALTER TABLE rachna_staff ADD COLUMN IF NOT EXISTS serial_no INTEGER""",
    """ALTER TABLE rachna_staff ADD COLUMN IF NOT EXISTS daily_rate NUMERIC(12,2) NOT NULL DEFAULT 0""",
    """CREATE UNIQUE INDEX IF NOT EXISTS idx_rachna_staff_serial ON rachna_staff(serial_no) WHERE serial_no IS NOT NULL""",
    """CREATE TABLE IF NOT EXISTS rachna_page_config(page_name TEXT PRIMARY KEY,visible BOOLEAN NOT NULL DEFAULT TRUE)""",
     """CREATE TABLE IF NOT EXISTS rachna_admin_auth(id SMALLINT PRIMARY KEY DEFAULT 1,admin_id TEXT NOT NULL,password_hash TEXT NOT NULL,updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"""]
    conn=db_connect()
    try:
        with conn:
            with conn.cursor() as cur:
                for sql in sqls: cur.execute(sql)
    finally: conn.close()

def money(v):
    return "Price on request" if v is None else "₹{:,.2f}".format(float(v))

def _hash_admin_password(password):
    salt=secrets.token_bytes(16)
    digest=hashlib.pbkdf2_hmac("sha256",password.encode("utf-8"),salt,180_000)
    return base64.urlsafe_b64encode(salt).decode()+"$"+base64.urlsafe_b64encode(digest).decode()

def _verify_admin_password(stored,password):
    try:
        salt_b64,digest_b64=str(stored).split("$",1)
        salt=base64.urlsafe_b64decode(salt_b64.encode())
        expected=base64.urlsafe_b64decode(digest_b64.encode())
        actual=hashlib.pbkdf2_hmac("sha256",password.encode("utf-8"),salt,180_000)
        return hmac.compare_digest(actual,expected)
    except Exception:
        return False

def ensure_admin_auth_table():
    """Create the admin credential table if an older database was deployed without it."""
    query("""CREATE TABLE IF NOT EXISTS rachna_admin_auth(
        id SMALLINT PRIMARY KEY DEFAULT 1,
        admin_id TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""", fetch=False)


def password_ok(user_id,entered):
    try:
        ensure_admin_auth_table()
        rows=query("SELECT admin_id,password_hash FROM rachna_admin_auth WHERE id=1 LIMIT 1")
    except Exception:
        rows=[]
    if rows:
        return hmac.compare_digest(str(user_id),str(rows[0]["admin_id"])) and _verify_admin_password(rows[0]["password_hash"],str(entered))
    return hmac.compare_digest(str(user_id),str(cfg("ADMIN_ID","1"))) and hmac.compare_digest(str(entered),str(cfg("ADMIN_PASSWORD","11")))

def save_admin_credentials(admin_id,password):
    ensure_admin_auth_table()
    query("""INSERT INTO rachna_admin_auth(id,admin_id,password_hash,updated_at)
             VALUES(1,%s,%s,NOW())
             ON CONFLICT(id) DO UPDATE SET admin_id=EXCLUDED.admin_id,password_hash=EXCLUDED.password_hash,updated_at=NOW()""",
          (admin_id,_hash_admin_password(password)),fetch=False)


PAGE_NAMES = ["Home", "Gallery", "Master Gallery", "Account", "Master Account", "About", "Contact Us", "Login"]
SETTING_KEYS = {
    "App logo": "app_logo",
    **{f"{page} background": f"bg_{page.lower().replace(' ', '_')}" for page in PAGE_NAMES},
}

def github_config():
    token = cfg("GITHUB_TOKEN")
    owner = cfg("GITHUB_OWNER")
    repo = cfg("GITHUB_REPO")
    branch = cfg("GITHUB_BRANCH", "main")
    if not token or not owner or not repo:
        raise RuntimeError(
            "Missing GitHub Secrets: GITHUB_TOKEN, GITHUB_OWNER and GITHUB_REPO"
        )
    return token, owner, repo, branch


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def image_registry_url(image_hash):
    if not image_hash:
        return None
    rows = query(
        "SELECT image_url FROM rachna_image_registry WHERE image_hash=%s LIMIT 1",
        (image_hash,),
    )
    return rows[0]["image_url"] if rows else None


def register_image_url(image_hash, image_url, folder):
    if not image_hash or not image_url:
        return image_url
    query(
        """INSERT INTO rachna_image_registry(image_hash,image_url,folder)
           VALUES(%s,%s,%s)
           ON CONFLICT(image_hash) DO NOTHING""",
        (image_hash, image_url, folder),
        fetch=False,
    )
    rows = query(
        "SELECT image_url FROM rachna_image_registry WHERE image_hash=%s LIMIT 1",
        (image_hash,),
    )
    return rows[0]["image_url"] if rows else image_url


def github_upload(image_bytes, extension="jpg", prefix="image", folder="EXTRA", image_hash=None):
    """Upload once to GitHub and reuse the same URL for the same SHA-256 hash.

    The deterministic hash filename plus the registry prevents duplicate GitHub
    files even when a save button is clicked repeatedly.
    """
    token, owner, repo, branch = github_config()

    folder = (folder or "EXTRA").strip("/ ")
    if not folder:
        folder = "EXTRA"

    image_hash = image_hash or sha256_bytes(image_bytes)

    # Fast path: image already registered in PostgreSQL.
    existing = image_registry_url(image_hash)
    if existing:
        return existing

    ext = extension.lstrip(".").lower() or "jpg"
    filename = f"image_{image_hash}.{ext}"
    path = f"IMAGES/{folder}/{filename}"
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # Deterministic path is a second safety net for two nearly simultaneous clicks.
    check = requests.get(api_url, headers=headers, timeout=12)
    if check.status_code == 200:
        return register_image_url(image_hash, raw_url, folder)

    if check.status_code not in (404, 301, 302):
        try:
            detail = check.json().get("message", check.text)
        except Exception:
            detail = check.text
        raise RuntimeError(f"GitHub check failed ({check.status_code}): {detail}")

    encoded = base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "message": f"Upload {filename}",
        "content": encoded,
        "branch": branch,
    }

    response = requests.put(api_url, headers=headers, json=payload, timeout=30)
    if response.ok:
        return register_image_url(image_hash, raw_url, folder)

    # Another request may have created the same deterministic file first.
    if response.status_code == 422:
        check_again = requests.get(api_url, headers=headers, timeout=12)
        if check_again.status_code == 200:
            return register_image_url(image_hash, raw_url, folder)

    try:
        detail = response.json().get("message", response.text)
    except Exception:
        detail = response.text
    raise RuntimeError(f"GitHub upload failed ({response.status_code}): {detail}")


def image_row_source(row):
    """Return a displayable image source: GitHub URL for new rows, bytes for old rows."""
    url = row.get("image_url")
    if url:
        return str(url)

    raw = row.get("image_data")
    if raw is None:
        return None
    if isinstance(raw, memoryview):
        return raw.tobytes()
    if isinstance(raw, bytearray):
        return bytes(raw)
    if isinstance(raw, bytes):
        return raw
    return bytes(raw)


def image_src_for_html(row):
    """Return an HTML image src for either a URL-backed or legacy DB-backed image."""
    source = image_row_source(row)
    if source is None:
        return ""

    if isinstance(source, str):
        return html.escape(source, quote=True)

    mime = html.escape(row.get("mime_type") or "image/jpeg", quote=True)
    encoded = base64.b64encode(source).decode("ascii")
    return f"data:{mime};base64,{encoded}"


@st.cache_data(ttl=120, show_spinner=False)
def get_setting(key):
    """Return a fully pickle-safe plain dict for Streamlit cache.

    psycopg2 RealDictRow/memoryview objects cannot be pickled by st.cache_data.
    Legacy BYTEA images are converted to normal bytes before returning.
    """
    rows = query(
        "SELECT image_data,image_url,image_hash,mime_type,text_value "
        "FROM rachna_site_settings WHERE setting_key=%s",
        (key,),
    )
    if not rows:
        return None

    row = rows[0]
    raw = row.get("image_data")
    if raw is None:
        image_bytes = b""
    elif isinstance(raw, memoryview):
        image_bytes = raw.tobytes()
    elif isinstance(raw, bytearray):
        image_bytes = bytes(raw)
    elif isinstance(raw, bytes):
        image_bytes = raw
    else:
        image_bytes = bytes(raw)

    return {
        "image_data": image_bytes,
        "image_url": str(row.get("image_url") or ""),
        "image_hash": str(row.get("image_hash") or ""),
        "mime_type": str(row.get("mime_type") or "image/jpeg"),
        "text_value": str(row.get("text_value") or ""),
    }


def normalize_uploaded_image(uploaded, max_size=1600, quality=82):
    raw = uploaded.getvalue() if hasattr(uploaded, "getvalue") else bytes(uploaded)
    im = Image.open(io.BytesIO(raw))
    im.verify()
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    im.thumbnail((max_size, max_size))
    out = io.BytesIO()
    im.save(out, format="JPEG", quality=quality, optimize=True)
    normalized = out.getvalue()
    return normalized, sha256_bytes(normalized)


def save_image_setting(key, uploaded):
    if uploaded is None:
        return

    normalized, image_hash = normalize_uploaded_image(uploaded, max_size=2000, quality=82)

    # bg_* keys belong to BG_IMAGES; app_logo belongs to LOGO.
    image_folder = "BG_IMAGES" if str(key).lower().startswith("bg_") else "LOGO"
    image_url = github_upload(
        normalized,
        extension="jpg",
        prefix=key,
        folder=image_folder,
        image_hash=image_hash,
    )

    query(
        """INSERT INTO rachna_site_settings(
               setting_key,image_data,image_url,image_hash,mime_type,text_value,updated_at
           )
           VALUES(%s,NULL,%s,%s,'image/jpeg',NULL,NOW())
           ON CONFLICT(setting_key) DO UPDATE
           SET image_data=NULL,image_url=EXCLUDED.image_url,
               image_hash=EXCLUDED.image_hash,mime_type=EXCLUDED.mime_type,
               updated_at=NOW()""",
        (key, image_url, image_hash),
        fetch=False,
    )
    get_setting.clear()
    theme_settings.clear()

def upload_lock(lock_key):
    """Prevent repeated save actions in the same Streamlit session."""
    if st.session_state.get(lock_key, False):
        return False
    st.session_state[lock_key] = True
    return True


def release_upload_lock(lock_key):
    st.session_state[lock_key] = False


def _valid_link(value, kind="url"):
    value=str(value or "").strip()
    if not value: return True
    if kind=="phone": return bool(re.fullmatch(r"[\d\s+\-().]{7,20}",value))
    parsed=urlparse(value)
    return parsed.scheme in ("http","https","mailto","tel","whatsapp") and bool(parsed.netloc or parsed.scheme in ("mailto","tel","whatsapp"))

def _save_text_setting(key,value):
    query("""INSERT INTO rachna_site_settings(setting_key,text_value,updated_at)
             VALUES(%s,%s,NOW()) ON CONFLICT(setting_key) DO UPDATE
             SET text_value=EXCLUDED.text_value,updated_at=NOW()""",(key,str(value or "").strip()),fetch=False)

@st.cache_data(ttl=120,show_spinner=False)
def contact_settings():
    keys=["contact_instagram","contact_youtube","contact_whatsapp","contact_phone","contact_email","contact_address"]
    rows=query("SELECT setting_key,text_value FROM rachna_site_settings WHERE setting_key = ANY(%s)",(keys,))
    data={k:"" for k in keys}
    for r in rows: data[str(r["setting_key"])]=str(r.get("text_value") or "")
    return data

def site_admin_page():
    if not st.session_state.get("admin"):
        st.error("Admin login required."); return
    page_header("SITE CONTROL CENTER","Admin Master","Everything important can be managed here without editing code.")
    st.info("GitHub image folders: IMAGES/LOGO, IMAGES/BG_IMAGES, IMAGES/PRODUCT_IMG and IMAGES/EXTRA. Images are deduplicated by SHA-256 and reused.")

    with st.expander("Brand logo & sidebar logo",expanded=True):
        existing=get_setting("app_logo")
        if existing and image_row_source(existing): st.image(image_row_source(existing),caption="Current app/sidebar logo",width=180)
        logo=st.file_uploader("Upload app/sidebar logo (PNG / JPG / WEBP)",type=["png","jpg","jpeg","webp"],key="admin_logo_upload")
        if st.button("Save logo",type="primary",key="save_admin_logo") and upload_lock("lock_save_admin_logo"):
            try:
                if not logo: st.warning("Please choose a logo image first.")
                else:
                    save_image_setting("app_logo",logo); st.toast("Logo saved successfully.",icon="✅"); st.rerun()
            except Exception as e: st.error(f"Logo upload failed: {e}")
            finally: release_upload_lock("lock_save_admin_logo")

    st.subheader("About page — marquee logos")
    st.caption("No small fixed limit: upload 50+ logos. Duplicate images are skipped automatically. Saved logos are appended, not overwritten.")
    uploads=st.file_uploader("Choose marquee images",type=["png","jpg","jpeg","webp"],accept_multiple_files=True,key="marquee_uploads")
    if st.button("Save About marquee images",key="save_marquee_images",type="primary") and upload_lock("lock_save_marquee_images"):
        try:
            if not uploads: st.warning("Choose at least one image.")
            else:
                existing_rows=query("SELECT setting_key,image_hash FROM rachna_site_settings WHERE setting_key LIKE 'about_marquee_%%'")
                used={str(r["image_hash"]) for r in existing_rows if r.get("image_hash")}
                max_no=0
                for r in existing_rows:
                    m=re.search(r"about_marquee_(\d+)$",str(r["setting_key"]))
                    if m: max_no=max(max_no,int(m.group(1)))
                added=skipped=0
                for uploaded in uploads:
                    normalized,image_hash=normalize_uploaded_image(uploaded,max_size=1000,quality=78)
                    if image_hash in used: skipped+=1; continue
                    max_no+=1
                    image_url=github_upload(normalized,extension="jpg",prefix=f"about_marquee_{max_no}",folder="EXTRA",image_hash=image_hash)
                    query("""INSERT INTO rachna_site_settings(setting_key,image_data,image_url,image_hash,mime_type,updated_at)
                             VALUES(%s,NULL,%s,%s,'image/jpeg',NOW()) ON CONFLICT(setting_key) DO NOTHING""",
                          (f"about_marquee_{max_no}",image_url,image_hash),fetch=False)
                    used.add(image_hash); added+=1
                get_setting.clear(); about_marquee_rows.clear()
                st.toast(f"{added} marquee image(s) saved. {skipped} duplicate(s) skipped." if added else "No new images added — all selected images were duplicates.",icon="✅" if added else "ℹ️")
                st.rerun()
        except Exception as exc: st.error(f"Could not save marquee images: {exc}")
        finally: release_upload_lock("lock_save_marquee_images")

    rows=about_marquee_rows()
    st.write(f"**Saved marquee logos: {len(rows)}**")
    if rows:
        choices={f"{i+1}. {r['setting_key']}":r['setting_key'] for i,r in enumerate(rows)}
        selected_label=st.selectbox("Select marquee image to delete",list(choices),key="marquee_delete_select")
        selected_key=choices[selected_label]
        selected_row=next((r for r in rows if r["setting_key"]==selected_key),None)
        if selected_row:
            src=image_row_source(selected_row)
            if src: st.image(src,width=140,caption="Selected marquee image")
        c1,c2=st.columns(2)
        with c1:
            if st.button("Delete selected marquee image",key="delete_marquee_one"):
                query("DELETE FROM rachna_site_settings WHERE setting_key=%s",(selected_key,),fetch=False)
                about_marquee_rows.clear(); get_setting.clear(); st.toast("Marquee image deleted.",icon="🗑️"); st.rerun()
        with c2:
            if st.button("Delete ALL marquee images",key="delete_marquee_all"):
                query("DELETE FROM rachna_site_settings WHERE setting_key LIKE 'about_marquee_%%'",fetch=False)
                about_marquee_rows.clear(); get_setting.clear(); st.toast("All marquee images deleted.",icon="🗑️"); st.rerun()

    st.subheader("Page background images")
    st.caption("Upload a separate image for each page. Leave an uploader empty to keep its current background.")
    for page in PAGE_NAMES:
        key=f"bg_{page.lower().replace(' ','_')}"
        with st.expander(f"{page} background"):
            current=get_setting(key)
            if current and image_row_source(current): st.image(image_row_source(current),caption=f"Current {page} background",use_container_width=True)
            upload=st.file_uploader(f"Choose {page} background",type=["png","jpg","jpeg","webp"],key=f"upload_{key}")
            if st.button(f"Save {page} background",key=f"save_{key}") and upload_lock(f"lock_save_{key}"):
                try:
                    if not upload: st.warning("Choose an image first.")
                    else: save_image_setting(key,upload); st.toast(f"{page} background saved.",icon="✅"); st.rerun()
                except Exception as e: st.error(f"Background upload failed: {e}")
                finally: release_upload_lock(f"lock_save_{key}")

    st.subheader("Contact Us links")
    cs=contact_settings()
    with st.form("contact_settings_form"):
        instagram=st.text_input("Instagram URL",cs["contact_instagram"],placeholder="https://instagram.com/...")
        youtube=st.text_input("YouTube URL",cs["contact_youtube"],placeholder="https://youtube.com/...")
        whatsapp=st.text_input("WhatsApp link",cs["contact_whatsapp"],placeholder="https://wa.me/91...")
        phone=st.text_input("Call number / tel link",cs["contact_phone"],placeholder="+91 98765 43210")
        email=st.text_input("Gmail / email",cs["contact_email"],placeholder="example@gmail.com")
        address=st.text_area("Address",cs["contact_address"])
        save_contact=st.form_submit_button("Save Contact Us",type="primary")
    if save_contact:
        errors=[]
        if not _valid_link(instagram): errors.append("Instagram URL is invalid.")
        if not _valid_link(youtube): errors.append("YouTube URL is invalid.")
        if not _valid_link(whatsapp): errors.append("WhatsApp link is invalid.")
        if phone.strip() and not _valid_link(phone,"phone") and not phone.strip().startswith("tel:"): errors.append("Phone number is invalid.")
        if email.strip() and "@" not in email: errors.append("Email address is invalid.")
        if errors:
            for err in errors: st.error(err)
        else:
            phone_value=phone.strip()
            if phone_value and not phone_value.startswith("tel:"): phone_value="tel:"+re.sub(r"[^\d+]","",phone_value)
            email_value=email.strip()
            if email_value and not email_value.startswith("mailto:"): email_value="mailto:"+email_value
            for k,v in [("contact_instagram",instagram),("contact_youtube",youtube),("contact_whatsapp",whatsapp),("contact_phone",phone_value),("contact_email",email_value),("contact_address",address)]: _save_text_setting(k,v)
            contact_settings.clear(); st.toast("Contact Us settings saved.",icon="✅"); st.rerun()

    st.subheader("Admin ID & password")
    st.caption("First login uses ADMIN_ID / ADMIN_PASSWORD from Streamlit Secrets (or legacy 1 / 11). After saving here, the database login becomes active.")
    ensure_admin_auth_table()
    with st.form("admin_credentials_form"):
        current_auth=query("SELECT admin_id FROM rachna_admin_auth WHERE id=1 LIMIT 1")
        current_id=str(current_auth[0]["admin_id"]) if current_auth else str(cfg("ADMIN_ID","1"))
        new_admin_id=st.text_input("New Admin ID",current_id)
        new_password=st.text_input("New Admin Password",type="password")
        confirm_password=st.text_input("Confirm New Password",type="password")
        save_auth=st.form_submit_button("Save Admin ID & Password",type="primary")
    if save_auth:
        if not new_admin_id.strip(): st.error("Admin ID cannot be empty.")
        elif len(new_password)<4: st.error("Password must be at least 4 characters.")
        elif new_password!=confirm_password: st.error("Password confirmation does not match.")
        else:
            save_admin_credentials(new_admin_id.strip(),new_password)
            st.toast("Admin ID and password updated.",icon="🔐"); st.session_state.admin=False; st.session_state.page="Login"; st.rerun()

    st.subheader("Page access / public visibility")
    public_pages=["Home","Gallery","Account","About","Contact Us"]
    for pg in public_pages: query("INSERT INTO rachna_page_config(page_name,visible) VALUES(%s,TRUE) ON CONFLICT(page_name) DO NOTHING",(pg,),fetch=False)
    page_rows=query("SELECT page_name,visible FROM rachna_page_config WHERE page_name = ANY(%s) ORDER BY page_name",(public_pages,))
    with st.form("page_visibility_form"):
        visibility={r["page_name"]:st.checkbox("Show "+r["page_name"]+" to public users",value=bool(r["visible"]),key="page_vis_"+r["page_name"]) for r in page_rows}
        save_pages=st.form_submit_button("Save page visibility")
    if save_pages:
        for pg,val in visibility.items(): query("UPDATE rachna_page_config SET visible=%s WHERE page_name=%s",(val,pg),fetch=False)
        public_page_names.clear(); page_is_visible.clear(); st.toast("Page visibility saved.",icon="✅"); st.rerun()

    st.subheader("Global theme colors")
    with st.form("theme_color_form"):
        bg=st.color_picker("Background color","#071b33"); card=st.color_picker("Card / panel color","#102c50"); accent=st.color_picker("Accent / heading color","#d6ae52")
        save_theme=st.form_submit_button("Save theme colors")
    if save_theme:
        for key,val in [("theme_bg",bg),("theme_card",card),("theme_accent",accent)]: _save_text_setting(key,val)
        theme_settings.clear(); st.toast("Theme colors saved.",icon="🎨"); st.rerun()

@st.cache_data(ttl=120, show_spinner=False)
def theme_settings():
    rows=query("SELECT setting_key,text_value FROM rachna_site_settings WHERE setting_key IN ('theme_bg','theme_card','theme_accent')")
    return {r["setting_key"]:r["text_value"] for r in rows}


@st.cache_data(ttl=120, show_spinner=False)
def about_marquee_rows():
    """Return pickle-safe marquee rows.

    About only needs the image URL for new GitHub-backed images. Legacy DB
    BYTEA images are still converted to normal bytes so old records work too.
    """
    rows = query(
        "SELECT setting_key,image_data,image_url,mime_type "
        "FROM rachna_site_settings "
        "WHERE setting_key LIKE 'about_marquee_%%' "
        "AND (image_url IS NOT NULL OR image_data IS NOT NULL) "
        "ORDER BY setting_key"
    )
    safe_rows = []
    for row in rows:
        raw = row.get("image_data")
        if raw is None:
            image_bytes = b""
        elif isinstance(raw, memoryview):
            image_bytes = raw.tobytes()
        elif isinstance(raw, bytearray):
            image_bytes = bytes(raw)
        elif isinstance(raw, bytes):
            image_bytes = raw
        else:
            image_bytes = bytes(raw)

        safe_rows.append({
            "setting_key": str(row.get("setting_key") or ""),
            "image_url": str(row.get("image_url") or ""),
            "image_data": image_bytes,
            "mime_type": str(row.get("mime_type") or "image/jpeg"),
        })
    return safe_rows


@st.cache_data(ttl=120, show_spinner=False)
def public_page_names():
    rows=query("SELECT page_name FROM rachna_page_config WHERE visible=TRUE")
    return {r["page_name"] for r in rows}


@st.cache_data(ttl=120, show_spinner=False)
def page_is_visible(page_name):
    rows=query("SELECT visible FROM rachna_page_config WHERE page_name=%s",(page_name,))
    return bool(rows and rows[0]["visible"])


def apply_page_branding(page):
    try:
        theme=theme_settings()
        if theme:
            st.markdown(f"<style>.stApp{{background-color:{theme.get('theme_bg','#071b33')}!important}} div[data-testid='stMetric'],.stContainer{{background-color:{theme.get('theme_card','#102c50')}}} h1,h2,h3,.brand-title{{color:{theme.get('theme_accent','#d6ae52')}!important}}</style>",unsafe_allow_html=True)
    except Exception:
        pass
    bg_key = f"bg_{page.lower().replace(' ', '_')}"
    bg = get_setting(bg_key)
    logo = get_setting("app_logo")
    if bg and image_row_source(bg):
        bg_src = image_src_for_html(bg)
        st.markdown(f"""<style>
        .stApp {{ background-image: linear-gradient(rgba(5,18,35,.78),rgba(5,18,35,.84)),url('{bg_src}') !important;
        background-size: cover !important; background-position: center !important; background-attachment: fixed !important; }}
        </style>""", unsafe_allow_html=True)
    logo_src = image_src_for_html(logo) if logo and image_row_source(logo) else ""
    logo_html = (f'<div class="brand-logo-slot"><img src="{logo_src}" alt="Rachna logo"></div>' if logo_src else '<div class="brand-logo-slot"></div>')
    st.markdown(f"""<div class="brand-marquee">{logo_html}<div class="brand-marquee-viewport"><div class="marquee-track"><span>RACHNA PLAYWOO &amp; HARDWEAR&nbsp; ✦ &nbsp;CRAFTED FOR YOUR SPACE&nbsp; ✦ &nbsp;PREMIUM QUALITY&nbsp; ✦ &nbsp;</span><span>RACHNA PLAYWOO &amp; HARDWEAR&nbsp; ✦ &nbsp;CRAFTED FOR YOUR SPACE&nbsp; ✦ &nbsp;PREMIUM QUALITY&nbsp; ✦ &nbsp;</span><span>RACHNA PLAYWOO &amp; HARDWEAR&nbsp; ✦ &nbsp;CRAFTED FOR YOUR SPACE&nbsp; ✦ &nbsp;PREMIUM QUALITY&nbsp; ✦ &nbsp;</span></div></div></div>""", unsafe_allow_html=True)

def page_header(kicker,title,subtitle=""):
    st.markdown(f'<div class="brand-sub">{kicker}</div><div class="brand-title" style="font-size:2.8rem">{title}</div>',unsafe_allow_html=True)
    if subtitle: st.caption(subtitle)
    st.divider()

def login_page():
    _,c,_=st.columns([1,1.2,1])
    with c:
        page_header("ADMIN ACCESS","Welcome Back","Sign in to manage products, attendance and accounts.")
        with st.form("login"):
            user_id=st.text_input("Admin ID", value="")
            pw=st.text_input("Password",type="password")
            submit=st.form_submit_button("Sign in",type="primary",use_container_width=True)
        if submit:
            if password_ok(user_id, pw): st.session_state.admin=True; st.session_state.page="Home"; st.rerun()
            else: st.error("Incorrect Admin ID or password.")

@st.cache_data(ttl=30, show_spinner=False)
def products(active=True):
    where="WHERE p.is_active=TRUE" if active else ""
    return query(f"""SELECT p.* FROM rachna_products p {where} ORDER BY p.created_at DESC""")

@st.cache_data(ttl=120, show_spinner=False)
def images(pid):
    """Return only pickle-safe primitive values from PostgreSQL image rows."""
    rows = query(
        "SELECT id,image_url,image_data,mime_type FROM rachna_product_images "
        "WHERE product_id=%s ORDER BY image_order,id",
        (pid,),
    )
    safe_rows = []
    for row in rows:
        raw = row.get("image_data")
        if raw is None:
            image_bytes = b""
        elif isinstance(raw, memoryview):
            image_bytes = raw.tobytes()
        else:
            image_bytes = bytes(raw)

        safe_rows.append({
            "id": int(row["id"]),
            "image_url": str(row["image_url"]) if row.get("image_url") else "",
            "image_data": image_bytes,
            "mime_type": row.get("mime_type") or "image/jpeg",
        })
    return safe_rows


def product_image_source(imrow):
    return imrow["image_url"] if imrow.get("image_url") else imrow["image_data"]


@st.cache_data(ttl=120,show_spinner=False)
def product_images_map(product_ids):
    ids=tuple(int(x) for x in product_ids if x is not None)
    if not ids: return {}
    rows=query("SELECT id,product_id,image_url,image_data,mime_type FROM rachna_product_images WHERE product_id = ANY(%s) ORDER BY product_id,image_order,id",(list(ids),))
    result={pid:[] for pid in ids}
    for row in rows:
        raw=row.get("image_data")
        if raw is None: image_bytes=b""
        elif isinstance(raw,memoryview): image_bytes=raw.tobytes()
        elif isinstance(raw,bytearray): image_bytes=bytes(raw)
        else: image_bytes=bytes(raw)
        result.setdefault(int(row["product_id"]),[]).append({"id":int(row["id"]),"image_url":str(row.get("image_url") or ""),"image_data":image_bytes,"mime_type":str(row.get("mime_type") or "image/jpeg")})
    return result

def render_image_slider(ims,key,height=300):
    if not ims: return
    slides=[]; total=len(ims)
    for i,imrow in enumerate(ims):
        src=image_src_for_html(imrow)
        if src:
            loading="eager" if i==0 else "lazy"
            slides.append(f'<div class="slide"><img src="{src}" loading="{loading}" decoding="async" alt="Photo {i+1} of {total}"></div>')
    if not slides: return
    count_text=f"{total} photo"+("s" if total!=1 else "")
    html_doc=f"""<style>
    *{{box-sizing:border-box}}body{{margin:0;background:transparent;overflow:hidden}}
    .viewport{{width:100%;height:{height}px;overflow-x:auto;overflow-y:hidden;display:flex;scroll-snap-type:x mandatory;scrollbar-width:none;touch-action:pan-x;background:#071b33}}
    .viewport::-webkit-scrollbar{{display:none}}
    .slide{{flex:0 0 100%;width:100%;height:100%;display:flex;align-items:center;justify-content:center;scroll-snap-align:start;background:#fff}}
    .slide img{{width:100%;height:100%;object-fit:contain;display:block}}
    .hint{{text-align:center;color:#9fb0c3;font:12px Arial,sans-serif;margin-top:5px}}
    </style><div class="viewport">{''.join(slides)}</div><div class="hint">Swipe left / right - {count_text}</div>"""
    components.html(html_doc,height=height+24,scrolling=False)

def gallery(master=False):
    page_header("COLLECTION","Master Gallery" if master else "Gallery",
        "Admin product management" if master else "Browse furniture, plywood and hardware products.")
    if master and not st.session_state.get("admin"):
        st.warning("Admin login required."); return
    if not master:
        items = products(active=True)
        image_map = product_images_map([x['id'] for x in items])
        left, right = st.columns([2,1])
        term = left.text_input("Search products", key="gallery_search", placeholder="Name, color, category...")
        categories = sorted({str(x.get("category") or "Other") for x in items})
        cat = right.selectbox("Category", ["All"] + categories, key="gallery_category")
        items = [x for x in items if term.casefold() in " ".join(str(x.get(k) or "") for k in ("title","category","material","size","color","description")).casefold() and (cat=="All" or x.get("category")==cat)]
        if not items:
            st.info("No matching products found.")
            return
        for start in range(0, len(items), 2):
            cols = st.columns(2, gap="medium")
            for col, product in zip(cols, items[start:start+2]):
                with col:
                    ims = image_map.get(int(product["id"]), [])
                    with st.container(border=True):
                        if ims:
                            render_image_slider(ims, f"public_{product['id']}", height=300)
                        st.markdown(f"**{html.escape(str(product['title']))}**")
                        with st.expander("Learn More", expanded=False):
                            st.markdown(f"**Price:** <span style='color:#16803c;font-weight:800'>{html.escape(money(product['price']))}</span>", unsafe_allow_html=True)
                            st.write(product.get("description") or "No description added.")
                            for label,key in [("Category","category"),("Material","material"),("Size","size"),("colors","color")]:
                                if product.get(key): st.markdown(f"**{label}:** {html.escape(str(product[key]))}")
        return
    if master:
        with st.expander("＋ Add product",expanded=False):
            with st.form("add_product",clear_on_submit=True):
                title=st.text_input("Product name *")
                category=st.text_input("Category", "Hardware")
                price=st.number_input("Price (₹)",min_value=0.0,step=100.0)
                material=st.text_input("Material")
                size=st.text_input("Size")
                color_names=st.multiselect("Select product colors", ["Black","White","Red","Blue","Green","Yellow","Brown","Grey","Silver","Gold","Beige","Orange","Pink","Purple"])
                custom_colors=st.text_input("Extra colors / hex codes", placeholder="#123456, Teak")
                color=", ".join(color_names + [x.strip() for x in custom_colors.split(",") if x.strip()])
                desc=st.text_area("Details")
                uploads=st.file_uploader("Photos (up to 10)",type=["jpg","jpeg","png","webp"],accept_multiple_files=True)
                save=st.form_submit_button("Save product",type="primary")
            if save:
                if not title.strip(): st.error("Product name is required.")
                elif len(uploads or [])>10: st.error("Upload a maximum of 10 photos.")
                else:
                    try:
                        row=query("""INSERT INTO rachna_products(title,category,price,material,size,color,description)
                        VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                        (title.strip(),category,price or None,material,size,color,desc))[0]
                        seen_hashes=set()
                        for n,f in enumerate(uploads or []):
                            normalized, image_hash = normalize_uploaded_image(f, max_size=1600, quality=82)
                            if image_hash in seen_hashes:
                                continue
                            seen_hashes.add(image_hash)
                            duplicate=query(
                                "SELECT id FROM rachna_product_images WHERE product_id=%s AND image_hash=%s LIMIT 1",
                                (row["id"],image_hash),
                            )
                            if duplicate:
                                continue
                            image_url=github_upload(
                                normalized,
                                extension="jpg",
                                prefix=f"product_{row['id']}_{n+1}",
                                folder="PRODUCT_IMG",
                                image_hash=image_hash,
                            )
                            query("""INSERT INTO rachna_product_images(
                                product_id,image_data,image_url,image_hash,mime_type,image_order
                            ) VALUES(%s,NULL,%s,%s,%s,%s)""",
                                (row["id"],image_url,image_hash,"image/jpeg",n),fetch=False)
                        products.clear(); images.clear(); product_images_map.clear(); st.success("Product saved."); st.rerun()
                    except Exception as e: st.error(f"Could not save product: {e}")
    items=products(active=not master)
    if master: items=products(active=False)
    if not items: st.info("No products yet. Admin can add them from Master Gallery."); return
    image_map=product_images_map([x["id"] for x in items])
    a,b,c,d=st.columns([2,1,1,1])
    with a: search=st.text_input("Search by name, color or category")
    with b: cat=st.selectbox("Category",["All"]+sorted(set(p["category"] for p in items)))
    with c: color_filter=st.selectbox("Color",["All"]+sorted(set(v.strip() for p in items for v in str(p.get("color") or "").split(",") if v.strip())))
    with d: price_filter=st.selectbox("Price range",["Any","Under ₹500","₹500–₹2,000","₹2,000–₹10,000","Above ₹10,000"])
    def price_match(p):
        v=float(p.get("price") or 0)
        return {"Any":True,"Under ₹500":v<500,"₹500–₹2,000":500<=v<=2000,"₹2,000–₹10,000":2000<v<=10000,"Above ₹10,000":v>10000}[price_filter]
    items=[p for p in items if search.lower() in " ".join(str(p.get(k) or "") for k in ["title","category","material","size","color","description"]).lower() and (cat=="All" or p["category"]==cat) and (color_filter=="All" or color_filter.lower() in str(p.get("color") or "").lower()) and price_match(p)]
    for offset in range(0,len(items),2):
        cols=st.columns(2)
        for col,p in zip(cols,items[offset:offset+2]):
            with col:
                with st.container(border=True):
                    if master: st.caption(f'Product #{p["id"]} · {"Visible" if p["is_active"] else "Hidden"}')
                    ims=image_map.get(int(p["id"]),[])
                    if ims:
                        render_image_slider(ims, f"product_{p['id']}", height=300)
                    st.subheader(p["title"])
                    st.markdown(f'<div style="font-size:1.35rem;font-weight:800;color:#22c55e;margin:.35rem 0">{html.escape(money(p["price"]))}</div>',unsafe_allow_html=True)
                    if p.get("color"):
                        swatches={"black":"#111111","white":"#ffffff","red":"#ef4444","blue":"#2563eb","green":"#16a34a","yellow":"#facc15","brown":"#854d0e","grey":"#9ca3af","gray":"#9ca3af","silver":"#c0c0c0","gold":"#d4af37","beige":"#d6c3a1","orange":"#f97316","pink":"#ec4899","purple":"#9333ea"}
                        tokens=[x.strip() for x in str(p["color"]).split(",") if x.strip()]
                        hexes=[x if x.startswith("#") and len(x) in (4,7) else swatches.get(x.lower(),"#888888") for x in tokens]
                        if hexes:
                            gradient="conic-gradient("+", ".join(f"{hx} {i*100/len(hexes):.1f}% {(i+1)*100/len(hexes):.1f}%" for i,hx in enumerate(hexes))+")"
                            st.markdown(f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0 12px"><span style="width:22px;height:22px;border-radius:50%;border:1px solid #aaa;display:inline-block;background:{gradient}"></span><span style="font-size:.85rem;color:#cbd5e1">{html.escape(", ".join(tokens))}</span></div>',unsafe_allow_html=True)
                    st.markdown(f'<span class="brand-sub">{p["category"]}</span>',unsafe_allow_html=True)
                    for label,k in [("Material","material"),("Size","size"),("Color","color")]:
                        if p[k]: st.markdown(f"**{label}:** {p[k]}")
                    if p["description"]: st.write(p["description"])
                    if master:
                        with st.expander("Edit / delete product"):
                            with st.form(f'edit_{p["id"]}'):
                                t=st.text_input("Name",p["title"])
                                cat2=st.selectbox("Category",["Furniture","Hardware","Plywood","Other"],index=["Furniture","Hardware","Plywood","Other"].index(p["category"]) if p["category"] in ["Furniture","Hardware","Plywood","Other"] else 3)
                                pr=st.number_input("Price",min_value=0.0,value=float(p["price"] or 0),step=100.0)
                                ma=st.text_input("Material",p["material"] or "")
                                sz=st.text_input("Size",p["size"] or "")
                                co=st.text_input("Color",p["color"] or "")
                                de=st.text_area("Details",p["description"] or "")
                                active=st.checkbox("Show in public gallery",bool(p["is_active"]))
                                more=st.file_uploader("Add photos (max 10 total)",type=["jpg","jpeg","png","webp"],accept_multiple_files=True,key=f'more_{p["id"]}')
                                upd=st.form_submit_button("Update")
                            if upd:
                                if len(ims)+len(more or [])>10: st.error("Maximum 10 photos per product.")
                                else:
                                    query("""UPDATE rachna_products SET title=%s,category=%s,price=%s,material=%s,size=%s,color=%s,description=%s,is_active=%s,updated_at=NOW() WHERE id=%s""",
                                      (t,cat2,pr or None,ma,sz,co,de,active,p["id"]),fetch=False)
                                    seen_hashes=set()
                                    for n,f in enumerate(more or [],start=len(ims)):
                                        normalized, image_hash = normalize_uploaded_image(f, max_size=1600, quality=82)
                                        if image_hash in seen_hashes:
                                            continue
                                        seen_hashes.add(image_hash)
                                        duplicate=query(
                                            "SELECT id FROM rachna_product_images WHERE product_id=%s AND image_hash=%s LIMIT 1",
                                            (p["id"],image_hash),
                                        )
                                        if duplicate:
                                            continue
                                        image_url=github_upload(
                                            normalized,
                                            extension="jpg",
                                            prefix=f"product_{p['id']}_{n+1}",
                                            folder="PRODUCT_IMG",
                                            image_hash=image_hash,
                                        )
                                        query("""INSERT INTO rachna_product_images(
                                            product_id,image_data,image_url,image_hash,mime_type,image_order
                                        ) VALUES(%s,NULL,%s,%s,%s,%s)""",
                                            (p["id"],image_url,image_hash,"image/jpeg",n),fetch=False)
                                    products.clear(); images.clear(); product_images_map.clear(); st.success("Updated."); st.rerun()
                            if st.button("Delete product",key=f'del_{p["id"]}'):
                                query("DELETE FROM rachna_products WHERE id=%s",(p["id"],),fetch=False); products.clear(); images.clear(); product_images_map.clear(); st.rerun()
                            if ims:
                                choices={f'Photo {i+1} (ID {im["id"]})':im["id"] for i,im in enumerate(ims)}
                                chosen=st.selectbox("Photo to delete",list(choices),key=f'imgdel_sel_{p["id"]}')
                                if st.button("Delete selected photo",key=f'imgdel_{p["id"]}'):
                                    query("DELETE FROM rachna_product_images WHERE id=%s",(choices[chosen],),fetch=False); product_images_map.clear(); images.clear(); st.toast("Photo deleted.",icon="🗑️"); st.rerun()

def account(master=False):
    if not master:
        page_header("KARIGAR ATTENDANCE", "Attendance Check", "Enter your special serial number to view your own attendance only.")
        with st.form("attendance_lookup"):
            serial_text=st.text_input("Special serial number (1–9999)",max_chars=4)
            go=st.form_submit_button("Search attendance",type="primary",use_container_width=True)
        if not go:
            st.info("Enter your serial number to continue. No staff list or other account details are shown.")
            return
        if not serial_text.isdigit() or not 1 <= int(serial_text) <= 9999:
            st.error("Enter a valid serial number from 1 to 9999."); return
        rows=query("SELECT id,name,serial_no,daily_rate FROM rachna_staff WHERE serial_no=%s AND active=TRUE",(int(serial_text),))
        if not rows: st.error("Serial number not found."); return
        person=rows[0]
        st.subheader("Attendance for "+person["name"])
        start=st.date_input("From",value=date(date.today().year,date.today().month,1),key="att_from")
        finish=st.date_input("To",value=date.today(),key="att_to")
        if start>finish: st.error("From date must be before To date."); return
        att=query("SELECT work_date,status FROM rachna_attendance WHERE staff_id=%s AND work_date BETWEEN %s AND %s ORDER BY work_date",(person["id"],start,finish))
        workdays=sum(1 if r["status"]=="Present" else .5 if r["status"]=="Half Day" else 0 for r in att)
        absent=sum(1 for r in att if r["status"]=="Absent")
        earned=workdays*float(person.get("daily_rate") or 0)
        pr=query("SELECT COALESCE(SUM(amount),0) AS paid FROM rachna_ledger WHERE person_name=%s AND entry_type='Payment' AND entry_date BETWEEN %s AND %s",(person["name"],start,finish))
        paid=float(pr[0]["paid"] or 0)
        a,b,c,d=st.columns(4); a.metric("Paid work days",f"{workdays:g}"); b.metric("Absent days",str(absent)); c.metric("Earned amount",money(earned)); d.metric("Paid amount",money(paid))
        st.markdown(f'<div style="font-size:1.25rem;font-weight:800;color:#22c55e">Remaining amount: {html.escape(money(max(earned-paid,0)))}</div>',unsafe_allow_html=True)
        if att:
            import pandas as pd
            chart=[{"Date":r["work_date"],"Work days":1 if r["status"]=="Present" else .5 if r["status"]=="Half Day" else 0} for r in att]
            st.subheader("Attendance graph"); st.line_chart(pd.DataFrame(chart).set_index("Date"))
            st.dataframe([{"Date":r["work_date"],"Status":r["status"]} for r in att],use_container_width=True,hide_index=True)
        else: st.info("No attendance marked in this date range.")
        return
    page_header("WORKSHOP MANAGEMENT","Master Account","Admin-only staff, attendance and ledger controls.")
    staff_tab,att_tab,ledger_tab,week_tab=st.tabs(["Staff","Attendance","Account ledger","Weekly view"])
    with staff_tab:
        staff=query("SELECT * FROM rachna_staff WHERE active=TRUE ORDER BY name")
        with st.expander("＋ Add staff / karigar"):
            with st.form("staff_add"):
                name=st.text_input("Name *"); serial=st.number_input("Special serial number (1–9999)",min_value=1,max_value=9999,step=1); daily_rate=st.number_input("Daily wage (₹)",min_value=0.0,step=50.0)
                role=st.selectbox("Role",["Karigar","Carpenter","Helper","Painter","Installer","Other"]); phone=st.text_input("Phone")
                add=st.form_submit_button("Add staff")
            if add:
                try:
                    if not name.strip(): st.error("Name required.")
                    else:
                        query("INSERT INTO rachna_staff(name,serial_no,daily_rate,role,phone) VALUES(%s,%s,%s,%s,%s)",(name.strip(),int(serial),daily_rate,role,phone),fetch=False); st.success("Staff added."); st.rerun()
                except Exception as e: st.error(f"Could not add staff. Serial number may already be used: {e}")
        if staff: st.dataframe([{"Serial":x["serial_no"],"Name":x["name"],"Role":x["role"],"Daily wage":money(x["daily_rate"]),"Phone":x["phone"] or ""} for x in staff],use_container_width=True,hide_index=True)
    with att_tab:
        staff=query("SELECT * FROM rachna_staff WHERE active=TRUE ORDER BY name"); d=st.date_input("Attendance date",value=date.today())
        if staff:
            old={r["staff_id"]:r for r in query("SELECT * FROM rachna_attendance WHERE work_date=%s",(d,))}
            with st.form("attendance"):
                vals=[]; opts=["Present","Absent","Half Day","Full Leave"]
                for x in staff:
                    prev=old.get(x["id"]); default=opts.index(prev["status"]) if prev and prev["status"] in opts else 0
                    status=st.selectbox(f'{x["name"]} (#{x["serial_no"] or "—"})',opts,index=default,key=f'st_{d}_{x["id"]}')
                    note=st.text_input("Note — "+x["name"],prev["notes"] or "" if prev else "",key=f'nt_{d}_{x["id"]}')
                    vals.append((x["id"],status,note))
                save=st.form_submit_button("Save attendance",type="primary")
            if save:
                conn=db_connect()
                try:
                    with conn:
                        with conn.cursor() as cur:
                            for sid,status,note in vals:
                                cur.execute("INSERT INTO rachna_attendance(staff_id,work_date,status,notes) VALUES(%s,%s,%s,%s) ON CONFLICT(staff_id,work_date) DO UPDATE SET status=EXCLUDED.status,notes=EXCLUDED.notes,updated_at=NOW()",(sid,d,status,note))
                    st.success("Attendance saved."); st.rerun()
                finally: conn.close()
    with ledger_tab:
        with st.form("ledger_add"):
            dt=st.date_input("Date",value=date.today()); person=st.text_input("Exact staff name / supplier"); typ=st.selectbox("Type",["Payment","Advance","Expense","Due"]); amt=st.number_input("Amount (₹)",min_value=0.0,step=100.0); note=st.text_input("Note")
            add=st.form_submit_button("Save entry")
        if add and person.strip() and amt>0:
            query("INSERT INTO rachna_ledger(entry_date,person_name,entry_type,amount,note) VALUES(%s,%s,%s,%s,%s)",(dt,person.strip(),typ,amt,note),fetch=False); st.rerun()
        rows=query("SELECT * FROM rachna_ledger ORDER BY entry_date DESC,id DESC LIMIT 500")
        if rows: st.dataframe([{"Date":r["entry_date"],"Name":r["person_name"],"Type":r["entry_type"],"Amount":money(r["amount"]),"Note":r["note"] or ""} for r in rows],use_container_width=True,hide_index=True)
    with week_tab:
        start=date.today()-timedelta(days=date.today().weekday()); end=start+timedelta(days=6)
        rows=query("SELECT s.name,s.serial_no,a.work_date,a.status FROM rachna_attendance a JOIN rachna_staff s ON s.id=a.staff_id WHERE a.work_date BETWEEN %s AND %s ORDER BY a.work_date,s.name",(start,end))
        if rows: st.dataframe([{"Date":r["work_date"],"Name":r["name"],"Serial":r["serial_no"],"Status":r["status"]} for r in rows],use_container_width=True,hide_index=True)
        else: st.info("No attendance records for this week.")

@st.cache_resource(show_spinner=False)
def init_db_cached():
    # Schema setup happens once per Streamlit server process, not on every rerun.
    init_db()
    return True


def render_about_marquee(rows):
    sources=[]
    for r in rows:
        src=image_src_for_html(r)
        if src: sources.append(src)
    if not sources: return
    groups=[sources[i::3] for i in range(3)]
    row_html=[]
    for idx,group in enumerate(groups):
        if not group: continue
        imgs="".join(f'<img src="{html.escape(src,quote=True)}" loading="lazy" decoding="async" alt="Rachna marquee logo">' for src in group)
        # Four copies keep even small groups continuously filling the full width.
        # Row 1: right -> left, Row 2: left -> right, Row 3: right -> left.
        repeated=imgs*4
        direction="left" if idx in (0,2) else "right"
        row_html.append(f'<div class="row {direction}"><div class="track">{repeated}</div></div>')
    html_doc=f"""<style>
    *{{box-sizing:border-box}}html,body{{margin:0;padding:0;background:transparent;overflow:hidden}}
    .wrap{{width:100%;overflow:hidden;display:flex;flex-direction:column;gap:8px}}
    .row{{width:100%;overflow:hidden;white-space:nowrap;display:flex}}
    .track{{display:flex;align-items:center;gap:10px;width:max-content;min-width:max-content;will-change:transform;animation:left 32s linear infinite}}
    .row.right .track{{animation-name:right}}
    img{{width:84px;height:52px;object-fit:contain;background:#fff;border-radius:9px;padding:4px;display:block;flex:0 0 auto}}
    @keyframes left{{from{{transform:translateX(0)}}to{{transform:translateX(-50%)}}}}
    @keyframes right{{from{{transform:translateX(-50%)}}to{{transform:translateX(0)}}}}
    @media(max-width:640px){{img{{width:66px;height:40px}}}}
    </style><div class="wrap">{"".join(row_html)}</div>"""
    components.html(html_doc,height=185,scrolling=False)


def main():
    try: init_db_cached()
    except Exception as e:
        st.error("PostgreSQL connection or table setup failed."); st.code(str(e))
        st.info("Set DB_HOST, DB_NAME, DB_USER, DB_PASSWORD and DB_PORT in Streamlit Secrets. Aiven normally requires SSL.")
        st.stop()
    if "admin" not in st.session_state: st.session_state.admin=False
    if "page" not in st.session_state: st.session_state.page="Home"
    with st.sidebar:
        sidebar_logo=get_setting("app_logo")
        if sidebar_logo and image_row_source(sidebar_logo):
            st.image(image_row_source(sidebar_logo),use_container_width=True)
        else:
            st.markdown('<div class="brand-title" style="font-size:2.2rem;color:#d6ae52">RACHNA</div><div class="brand-sub">PLAYWOOD & HARDWARE</div>',unsafe_allow_html=True)
        st.divider()
        nav=["Home","Gallery","Account","About","Contact Us"]
        if not st.session_state.admin:
            try:
                visible=public_page_names()
                if visible:
                    nav=[item for item in nav if item in visible]
            except Exception:
                pass
        if st.session_state.admin: nav += ["Master Gallery","Master Account","Admin Master"]
        # Keep navigation labels unique so Streamlit widget keys never collide.
        nav = list(dict.fromkeys(nav))
        for p in nav:
            if st.button(p,key="nav_"+p,use_container_width=True,type="primary" if st.session_state.page==p else "secondary"):
                st.session_state.page=p; st.rerun()
        st.divider()
        if st.session_state.admin:
            st.success("Admin signed in")
            if st.button("Log out",use_container_width=True): st.session_state.admin=False; st.session_state.page="Home"; st.rerun()
        else:
            st.caption("Public access: product browsing")
            if st.button("Admin Login",use_container_width=True): st.session_state.page="Login"; st.rerun()
        st.caption("© Rachna Playwoo & Hardwear")
    p=st.session_state.page
    if not st.session_state.admin and p != "Login":
        try:
            if not page_is_visible(p):
                st.session_state.page="Home"; p="Home"
                st.warning("This page is not available to public users.")
        except Exception:
            pass
    apply_page_branding(p)
    if p=="Login": login_page()
    elif p=="Home":
        st.markdown(f'<div class="hero"><div class="brand-sub">CRAFTED FOR YOUR SPACE</div><h2>{APP_NAME}</h2><p>Furniture, plywood and hardware — explore our collection.</p></div>',unsafe_allow_html=True)
        items=products()
        home_image_map=product_images_map([x['id'] for x in items[:3]])
        a,b,c=st.columns(3); a.metric("Products",len(items)); b.metric("Furniture",sum(x["category"]=="Furniture" for x in items)); c.metric("Hardware / plywood",sum(x["category"] in ["Hardware","Plywood"] for x in items))
        st.subheader("Featured collection")
        if items:
            cols=st.columns(min(3,len(items)))
            for col,x in zip(cols,items[:3]):
                with col:
                    ims=home_image_map.get(int(x['id']),[])
                    if ims: st.image(product_image_source(ims[0]),use_container_width=True)
                    st.subheader(x["title"]); st.markdown(f"**{money(x['price'])}**"); st.caption(x["category"]); st.write((x["description"] or "")[:160])
        else: st.info("Admin can add products using Master Gallery.")
    elif p=="Gallery": gallery(False)
    elif p=="Master Gallery": gallery(True)
    elif p=="Account": account(False)
    elif p=="Master Account": account(True)
    elif p=="Admin Master": site_admin_page()
    elif p=="About":
        page_header("OUR STORY","About RACHNA PLYWOOD & HARDWARE","Thoughtful materials. Reliable workmanship.")
        st.markdown(f'<div class="hero"><div class="brand-sub">PLYWOOD · FURNITURE · HARDWARE</div><h2>{APP_NAME}</h2><p>A digital catalogue to showcase furniture, plywood and hardware products.</p></div>',unsafe_allow_html=True)
        try: rows=about_marquee_rows()
        except Exception: rows=[]
        if not rows:
            logo=get_setting("app_logo")
            rows=[logo] if logo and image_row_source(logo) else []
        if rows: render_about_marquee(rows)
        a,b,c=st.columns(3)
        a.markdown("### 🪵 Furniture\\nMade-to-order furniture.")
        b.markdown("### 🧰 Hardware\\nFittings and hardware products.")
        c.markdown("### 📐 Materials\\nPlywood, sizes and colours.")
    elif p=="Contact Us":
        page_header("GET IN TOUCH","Contact Us","Reach Rachna Playwood & Hardwear directly.")
        cs=contact_settings()
        items=[]
        if cs.get("contact_instagram"): items.append(("◎","Instagram",cs["contact_instagram"]))
        if cs.get("contact_youtube"): items.append(("▶","YouTube",cs["contact_youtube"]))
        if cs.get("contact_whatsapp"): items.append(("WA","WhatsApp",cs["contact_whatsapp"]))
        if cs.get("contact_phone"): items.append(("☎","Call",cs["contact_phone"]))
        if cs.get("contact_email"): items.append(("✉","Email",cs["contact_email"]))
        if items:
            links="".join(f'<a class="contact-item" href="{html.escape(url,quote=True)}" target="_blank" rel="noopener"><span class="contact-icon">{html.escape(icon)}</span>{html.escape(label)}</a>' for icon,label,url in items)
            st.markdown(f'<div class="contact-grid">{links}</div>',unsafe_allow_html=True)
        else: st.info("Contact links are managed from Admin Master.")
        if cs.get("contact_address"):
            addr=html.escape(cs["contact_address"]).replace(chr(10),"<br>")
            st.markdown(f'<div class="hero"><div class="brand-sub">VISIT US</div><h2>Address</h2><p>{addr}</p></div>',unsafe_allow_html=True)


# st.markdown('<div style="margin-top:2rem;padding:1rem 0;border-top:1px solid #d6ae5255;text-align:center;color:#aab6c5;font-size:.8rem">© RACHNA PLAYWOO &amp; HARDWEAR · All rights reserved</div>', unsafe_allow_html=True)

if __name__=="__main__": main()

