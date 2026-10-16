
"""
RACHNA PLAYWOO & HARDWEAR — Streamlit catalogue and workshop accounts.
Configure credentials in Streamlit Secrets; never hard-code database credentials.
Creates separate rachna_* tables in the configured PostgreSQL database and does not modify the existing tiffin table.
"""
import io, os, hmac, base64, html, hashlib, smtplib, ssl, json
from datetime import date, timedelta
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from PIL import Image
import requests

APP_NAME = "RACHNA PLAYWOOD & HARDWEAR"
st.set_page_config(page_title=APP_NAME, page_icon="🪵", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap');
header[data-testid="stHeader"]{display:flex!important;background:transparent!important;height:3.25rem!important;visibility:visible!important}
#MainMenu{visibility:hidden!important}.stDeployButton{display:none!important}
header[data-testid="stHeader"] [data-testid="stToolbar"]{visibility:visible!important}
header[data-testid="stHeader"] button[data-testid="stSidebarCollapseButton"],header[data-testid="stHeader"] button[data-testid="stSidebarExpandButton"],header[data-testid="stHeader"] [data-testid="stSidebarCollapsedControl"]{visibility:visible!important;display:flex!important;opacity:1!important;color:#d6ae52!important;background:#071b33!important;border:2px solid #d6ae52!important;border-radius:12px!important;width:44px!important;height:42px!important;align-items:center!important;justify-content:center!important;z-index:1000000!important}
header[data-testid="stHeader"] button[data-testid="stSidebarCollapseButton"] svg,header[data-testid="stHeader"] button[data-testid="stSidebarExpandButton"] svg,header[data-testid="stHeader"] [data-testid="stSidebarCollapsedControl"] svg{display:none!important}
header[data-testid="stHeader"] button[data-testid="stSidebarCollapseButton"]::after,header[data-testid="stHeader"] button[data-testid="stSidebarExpandButton"]::after,header[data-testid="stHeader"] [data-testid="stSidebarCollapsedControl"]::after{content:"☰"!important;display:block!important;color:#d6ae52!important;font-size:25px!important;line-height:1!important;font-weight:700!important}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
.stApp{background:linear-gradient(135deg,#071b33,#102c50);color:#f5f0e5}
.block-container{padding-top:4.5rem!important;padding-left:clamp(1rem,3vw,3rem)!important;padding-right:clamp(1rem,3vw,3rem)!important;max-width:1500px}
h1,h2,h3,h4{font-family:'Cormorant Garamond',serif!important;color:#d6ae52!important;text-align:center}
.brand-title{font-family:'Cormorant Garamond',serif;font-size:clamp(2rem,5vw,4rem);font-weight:700;letter-spacing:.04em;color:#d6ae52;text-align:center}
.brand-sub{letter-spacing:.24em;text-transform:uppercase;color:#d6ae52;font-size:.75rem;text-align:center}
.hero{padding:1.4rem;border-radius:22px;background:linear-gradient(120deg,#071b33,#102c50);color:white;border:1px solid #d6ae52;text-align:center}
.hero h2{color:#d6ae52!important;font-size:2.4rem}.hero p{color:#f5ead2;text-align:center}
div[data-testid="stMetric"]{background:#102c50;border:1px solid #d6ae52;padding:14px;border-radius:15px}
section[data-testid="stSidebar"]{background:#071b33!important;z-index:100000!important}
section[data-testid="stSidebar"] *{color:#f5f0e5!important}
/* Keep Streamlit's native sidebar toggle clickable; style it as the reliable three-line menu. */
.custom-menu-wrap{display:none!important}
button[kind="headerNoPadding"]{visibility:visible!important}

.product-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.product-mini{min-width:0;border:1px solid #d6ae524d;border-radius:14px;padding:8px;background:#071b33cc;overflow:hidden}
.product-mini img{width:100%;height:var(--product-h,150px);object-fit:contain;background:#fff;border-radius:10px;display:block}
.product-mini .name{font-weight:800;color:#f7f0df;font-size:.95rem;margin-top:7px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.product-mini .price{color:#d6ae52;font-weight:800;font-size:.9rem}
.product-mini .cat{color:#aab6c5;font-size:.72rem}
.product-dots{color:#d6ae52;text-align:center;font-size:.9rem;letter-spacing:3px;margin-top:3px}
.profile-card{border:1px solid #d6ae52;border-radius:22px;padding:20px;background:#071b33dd;text-align:center}
.dp{width:92px;height:92px;border-radius:50%;object-fit:cover;border:3px solid #d6ae52;margin:auto;display:block}
.att-row{border-radius:12px;padding:8px 12px;margin:5px 0;border:1px solid #ffffff22}
.marquee-wrap{overflow:hidden;display:flex;flex-direction:column;gap:9px;margin:1rem 0}
.marquee-row{overflow:hidden;white-space:nowrap;display:flex}
.marquee-track{display:flex;gap:10px;width:max-content;animation:move-left 30s linear infinite}
.marquee-row.right .marquee-track{animation-name:move-right}
.marquee-track img{height:52px;width:84px;object-fit:contain;background:#fff;border-radius:9px;padding:4px}
@keyframes move-left{from{transform:translateX(-50%)}to{transform:translateX(0)}}
@keyframes move-right{from{transform:translateX(0)}to{transform:translateX(-50%)}}
@media(max-width:1100px){.product-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:720px){.block-container{padding-top:4rem!important}.product-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.product-mini{padding:6px}.product-mini img{height:var(--product-h-mobile,125px)}.marquee-track img{height:40px;width:66px}header[data-testid="stHeader"] button[data-testid="stSidebarCollapseButton"],header[data-testid="stHeader"] button[data-testid="stSidebarExpandButton"]{width:42px!important;height:40px!important}}
@media(max-width:430px){.product-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.product-mini .name{font-size:.82rem}.product-mini .price{font-size:.78rem}}
.stButton>button{border-radius:10px;border:1px solid #d6ae52;font-weight:600}
div.stButton>button[kind="primary"]{background:#071b33;color:white}
</style>
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
    """CREATE TABLE IF NOT EXISTS rachna_admin_auth(id INTEGER PRIMARY KEY CHECK(id=1),admin_id TEXT NOT NULL,admin_password TEXT NOT NULL,updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""",
    """CREATE TABLE IF NOT EXISTS rachna_users(id BIGSERIAL PRIMARY KEY,name TEXT NOT NULL,phone TEXT NOT NULL UNIQUE,email TEXT NOT NULL UNIQUE,dp_url TEXT,dp_hash TEXT,age INTEGER,address TEXT,pincode TEXT,password_hash TEXT NOT NULL,staff_id BIGINT REFERENCES rachna_staff(id) ON DELETE SET NULL,is_admin BOOLEAN NOT NULL DEFAULT FALSE,active BOOLEAN NOT NULL DEFAULT TRUE,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""",
    """CREATE TABLE IF NOT EXISTS rachna_orders(id BIGSERIAL PRIMARY KEY,user_id BIGINT REFERENCES rachna_users(id) ON DELETE SET NULL,customer_name TEXT NOT NULL,phone TEXT NOT NULL,address TEXT,delivery_date DATE NOT NULL,product_id BIGINT REFERENCES rachna_products(id) ON DELETE SET NULL,category TEXT,product_name TEXT NOT NULL,quantity NUMERIC(12,2) NOT NULL CHECK(quantity>0),unit_price NUMERIC(12,2),total_price NUMERIC(12,2),created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""",
    """ALTER TABLE rachna_staff ADD COLUMN IF NOT EXISTS color TEXT DEFAULT '#3b82f6'""",
    """ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS pincode TEXT""",
    """ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS staff_id BIGINT REFERENCES rachna_staff(id) ON DELETE SET NULL""",
    """CREATE INDEX IF NOT EXISTS idx_rachna_users_email ON rachna_users(email)""",
    """CREATE INDEX IF NOT EXISTS idx_rachna_orders_date ON rachna_orders(created_at DESC)""",
    "INSERT INTO rachna_page_config(page_name,visible) VALUES ('Home',TRUE),('Gallery',TRUE),('Order',TRUE),('Account',TRUE),('About',TRUE),('Contact Us',TRUE) ON CONFLICT(page_name) DO NOTHING""" ]
    conn=db_connect()
    try:
        with conn:
            with conn.cursor() as cur:
                for sql in sqls: cur.execute(sql)
    finally: conn.close()

def money(v):
    return "Price on request" if v is None else "₹{:,.2f}".format(float(v))

def password_hash(value):
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def admin_credentials():
    try:
        rows=query("SELECT admin_id,admin_password FROM rachna_admin_auth WHERE id=1")
        if rows:
            return str(rows[0]["admin_id"]), str(rows[0]["admin_password"])
    except Exception:
        pass
    return cfg("ADMIN_ID","1"), cfg("ADMIN_PASSWORD","11")


def password_ok(user_id, entered):
    aid, apw = admin_credentials()
    return hmac.compare_digest(str(user_id), str(aid)) and hmac.compare_digest(str(entered), str(apw))


PAGE_NAMES = ["Home", "Gallery", "Order", "Account", "Master Gallery", "Master Account", "About", "Contact Us", "Login", "Admin Master"]
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


def site_admin_page():
    if not st.session_state.get('admin'):
        st.error('Admin login required.'); return
    page_header('SITE CONTROL CENTER','Admin Master','Brand, visibility, product sizing and admin access')
    with st.expander('Brand logo & backgrounds',expanded=True):
        existing=get_setting('app_logo')
        if existing and image_row_source(existing): st.image(image_row_source(existing),caption='Current app logo',width=180)
        logo=st.file_uploader('Upload app logo',type=['png','jpg','jpeg','webp'],key='admin_logo_upload')
        if st.button('Save logo',type='primary',key='save_admin_logo') and upload_lock('lock_save_admin_logo'):
            try: save_image_setting('app_logo',logo); release_upload_lock('lock_save_admin_logo'); st.rerun()
            except Exception as e: release_upload_lock('lock_save_admin_logo'); st.error(str(e))
        for page in ['Home','Gallery','Order','Account','About','Contact Us']:
            key=f'bg_{page.lower().replace(" ","_")}'; up=st.file_uploader(f'{page} background',type=['png','jpg','jpeg','webp'],key=f'upload_{key}')
            if st.button(f'Save {page} background',key=f'save_{key}') and upload_lock(f'lock_{key}'):
                try: save_image_setting(key,up); release_upload_lock(f'lock_{key}'); st.rerun()
                except Exception as e: release_upload_lock(f'lock_{key}'); st.error(str(e))
    st.subheader('About page — marquee images')
    uploads=st.file_uploader('Add any number of logos/images',type=['png','jpg','jpeg','webp'],accept_multiple_files=True,key='marquee_uploads')
    if st.button('Save About marquee images',key='save_marquee_images') and upload_lock('lock_save_marquee_images'):
        try:
            for idx,uploaded in enumerate(uploads or [],1):
                normalized,h=normalize_uploaded_image(uploaded,max_size=900,quality=78); url=github_upload(normalized,extension='jpg',folder='EXTRA',image_hash=h)
                query("INSERT INTO rachna_site_settings(setting_key,image_data,image_url,image_hash,mime_type,updated_at) VALUES(%s,NULL,%s,%s,'image/jpeg',NOW()) ON CONFLICT(setting_key) DO UPDATE SET image_url=EXCLUDED.image_url,image_hash=EXCLUDED.image_hash,image_data=NULL,updated_at=NOW()",(f'about_marquee_{idx}',url,h),fetch=False)
            get_setting.clear(); about_marquee_rows.clear(); release_upload_lock('lock_save_marquee_images'); st.rerun()
        except Exception as e: release_upload_lock('lock_save_marquee_images'); st.error(str(e))
    st.subheader('Product image size')
    with st.form('product_size_form'):
        w=st.slider('Product image width (%)',60,100,int(float(text_setting('product_image_width','100')))); h=st.slider('Product image height (px)',80,300,int(float(text_setting('product_image_height','150')))); save=st.form_submit_button('Save product size',type='primary')
    if save: save_text_setting('product_image_width',w); save_text_setting('product_image_height',h); st.success('Product size saved.'); st.rerun()
    st.subheader('Page access / public visibility')
    public_pages=['Home','Gallery','Order','Account','About','Contact Us']
    for pg in public_pages: query('INSERT INTO rachna_page_config(page_name,visible) VALUES(%s,TRUE) ON CONFLICT(page_name) DO NOTHING',(pg,),fetch=False)
    page_rows=query('SELECT page_name,visible FROM rachna_page_config WHERE page_name=ANY(%s) ORDER BY page_name',(public_pages,))
    with st.form('page_visibility_form'):
        visibility={r['page_name']:st.checkbox('Show '+r['page_name']+' to public users',value=bool(r['visible']),key='page_vis_'+r['page_name']) for r in page_rows}; save_pages=st.form_submit_button('Save page visibility')
    if save_pages:
        for pg,val in visibility.items(): query('UPDATE rachna_page_config SET visible=%s WHERE page_name=%s',(val,pg),fetch=False)
        public_page_names.clear(); page_is_visible.clear(); st.rerun()
    st.subheader('Global theme colors')
    with st.form('theme_color_form'):
        bg=st.color_picker('Background color',theme_settings().get('theme_bg','#071b33')); card=st.color_picker('Card / panel color',theme_settings().get('theme_card','#102c50')); accent=st.color_picker('Golden heading/text color',theme_settings().get('theme_accent','#d6ae52')); btn=st.color_picker('Button color',theme_settings().get('theme_btn','#ff4b4b')); save_theme=st.form_submit_button('Save theme colors')
    if save_theme:
        for key,val in [('theme_bg',bg),('theme_card',card),('theme_accent',accent),('theme_btn',btn)]: save_text_setting(key,val)
        st.rerun()
    st.subheader('Admin ID & password')
    aid,apw=admin_credentials()
    with st.form('admin_auth_form'):
        na=st.text_input('Admin ID',aid); np=st.text_input('Admin password',apw,type='password'); save_auth=st.form_submit_button('Save admin login',type='primary')
    if save_auth:
        query("INSERT INTO rachna_admin_auth(id,admin_id,admin_password,updated_at) VALUES(1,%s,%s,NOW()) ON CONFLICT(id) DO UPDATE SET admin_id=EXCLUDED.admin_id,admin_password=EXCLUDED.admin_password,updated_at=NOW()",(na.strip(),np),fetch=False); st.success('Admin login saved.')

    st.subheader('User accounts / admin rights')
    users=query('SELECT id,name,email,phone,is_admin,active FROM rachna_users ORDER BY created_at DESC LIMIT 500')
    for u in users:
        c1,c2,c3,c4=st.columns([2,2,1,1]); c1.write(u['name']); c2.write(u['email']); c3.write('Admin' if u['is_admin'] else 'User')
        if c4.button('Remove admin' if u['is_admin'] else 'Make admin',key=f"user_role_{u['id']}"):
            query('UPDATE rachna_users SET is_admin=%s,updated_at=NOW() WHERE id=%s',(not bool(u['is_admin']),u['id']),fetch=False); st.rerun()

@st.cache_data(ttl=120, show_spinner=False)
def theme_settings():
    rows=query("SELECT setting_key,text_value FROM rachna_site_settings WHERE setting_key IN ('theme_bg','theme_card','theme_accent','theme_btn')")
    return {r["setting_key"]:r["text_value"] for r in rows}


@st.cache_data(ttl=120, show_spinner=False)
def about_marquee_rows():
    rows=query("SELECT setting_key,image_data,image_url,image_hash,mime_type FROM rachna_site_settings WHERE setting_key LIKE %s AND (image_url IS NOT NULL OR image_data IS NOT NULL) ORDER BY setting_key",("about_marquee_%",))
    safe=[]
    for r in rows:
        raw=r.get("image_data")
        if raw is None: b=b""
        elif isinstance(raw,memoryview): b=raw.tobytes()
        else: b=bytes(raw)
        safe.append({"setting_key":str(r.get("setting_key") or ""),"image_data":b,"image_url":str(r.get("image_url") or ""),"image_hash":str(r.get("image_hash") or ""),"mime_type":str(r.get("mime_type") or "image/jpeg")})
    return safe


@st.cache_data(ttl=120, show_spinner=False)
def public_page_names():
    rows=query("SELECT page_name FROM rachna_page_config WHERE visible=TRUE")
    return {r["page_name"] for r in rows}


@st.cache_data(ttl=120, show_spinner=False)
def page_is_visible(page_name):
    rows=query("SELECT visible FROM rachna_page_config WHERE page_name=%s",(page_name,))
    return bool(rows and rows[0]["visible"])


def text_setting(key, default=""):
    rows=query("SELECT text_value FROM rachna_site_settings WHERE setting_key=%s",(key,))
    return str(rows[0]["text_value"] or default) if rows else default


def save_text_setting(key, value):
    query("INSERT INTO rachna_site_settings(setting_key,text_value,updated_at) VALUES(%s,%s,NOW()) ON CONFLICT(setting_key) DO UPDATE SET text_value=EXCLUDED.text_value,updated_at=NOW()",(key,str(value)),fetch=False)
    theme_settings.clear()
    get_setting.clear()


def product_size_settings():
    try:
        w=int(float(text_setting("product_image_width","100")))
        h=int(float(text_setting("product_image_height","150")))
    except Exception: w,h=100,150
    return max(60,min(w,100)),max(80,min(h,500))


def find_user_by_id(uid):
    rows=query("SELECT * FROM rachna_users WHERE id=%s AND active=TRUE",(uid,))
    return rows[0] if rows else None


def current_user():
    uid=st.session_state.get("user_id")
    return find_user_by_id(uid) if uid else None


def lookup_pincode(pin):
    pin="".join(ch for ch in str(pin) if ch.isdigit())
    if len(pin)!=6: return ""
    try:
        r=requests.get(f"https://api.postalpincode.in/pincode/{pin}",timeout=4)
        data=r.json()
        if data and data[0].get("Status")=="Success" and data[0].get("PostOffice"):
            po=data[0]["PostOffice"][0]
            return ", ".join([x for x in [po.get("Name"),po.get("District"),po.get("State")] if x])
    except Exception: pass
    return ""


def save_user_dp(uploaded, user_id):
    normalized,h=normalize_uploaded_image(uploaded,max_size=600,quality=82)
    url=github_upload(normalized,extension="jpg",prefix=f"user_{user_id}",folder="EXTRA",image_hash=h)
    query("UPDATE rachna_users SET dp_url=%s,dp_hash=%s,updated_at=NOW() WHERE id=%s",(url,h,user_id),fetch=False)
    return url


def send_order_email(order, debug=False):
    """Send order email with detailed safe diagnostics.
    Uses EmailMessage so Unicode characters such as ₹ are handled correctly.
    Never prints the SMTP password.
    Supports SMTP_USER/SMTP_USERNAME/SMTP_EMAIL aliases.
    """
    def log(msg):
        print(f"[RACHNA EMAIL] {msg}", flush=True)
        if debug:
            st.write(f"📧 {msg}")

    host = cfg("SMTP_HOST")
    user = cfg("SMTP_USER", cfg("SMTP_USERNAME", cfg("SMTP_EMAIL")))
    pw = cfg("SMTP_PASSWORD")
    to = cfg("ORDER_EMAIL", cfg("ADMIN_EMAIL", cfg("SMTP_TO", user)))
    port_raw = cfg("SMTP_PORT", "465")

    log("Step 1/6: Reading SMTP secrets")
    log(f"SMTP_HOST present: {bool(host)}")
    log(f"SMTP_USER/USERNAME/EMAIL present: {bool(user)}")
    log(f"SMTP_PASSWORD present: {bool(pw)}")
    log(f"ORDER_EMAIL/ADMIN_EMAIL present: {bool(to)}")
    log(f"SMTP_PORT: {port_raw}")

    if not all([host, user, pw, to]):
        missing = []
        if not host: missing.append("SMTP_HOST")
        if not user: missing.append("SMTP_USER (or SMTP_USERNAME/SMTP_EMAIL)")
        if not pw: missing.append("SMTP_PASSWORD")
        if not to: missing.append("ORDER_EMAIL (or ADMIN_EMAIL)")
        msg = "Missing SMTP secrets: " + ", ".join(missing)
        log("FAILED: " + msg)
        return False, msg

    try:
        port = int(port_raw)
    except Exception:
        msg = f"Invalid SMTP_PORT: {port_raw}"
        log("FAILED: " + msg)
        return False, msg

    body = (
        f"New Rachna Order\n\n"
        f"Customer: {order['customer_name']}\n"
        f"Phone: {order['phone']}\n"
        f"Address: {order.get('address') or ''}\n"
        f"Delivery date: {order['delivery_date']}\n"
        f"Category: {order.get('category') or ''}\n"
        f"Product: {order['product_name']}\n"
        f"Quantity: {order['quantity']}\n"
        f"Unit price: {money(order.get('unit_price'))}\n"
        f"Total: {money(order.get('total_price'))}"
    )

    email_msg = EmailMessage()
    email_msg["Subject"] = "New Rachna Order"
    email_msg["From"] = user
    email_msg["To"] = to
    email_msg.set_content(body)

    try:
        if port == 465:
            log("Step 2/6: Connecting using SMTP SSL on port 465")
            with smtplib.SMTP_SSL(
                host, port, context=ssl.create_default_context(), timeout=15
            ) as smtp:
                log("Step 3/6: SMTP SSL connection successful")
                log("Step 4/6: Logging in to SMTP server")
                smtp.login(user, pw)
                log("Step 5/6: SMTP login successful")
                smtp.send_message(email_msg)
                log("Step 6/6: Email accepted by SMTP server")
        else:
            log(f"Step 2/6: Connecting using SMTP on port {port}")
            with smtplib.SMTP(host, port, timeout=15) as smtp:
                log("Step 3/6: SMTP connection successful")
                log("Step 4/6: Starting TLS")
                smtp.ehlo()
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
                log("TLS successful; logging in")
                smtp.login(user, pw)
                log("Step 5/6: SMTP login successful")
                smtp.send_message(email_msg)
                log("Step 6/6: Email accepted by SMTP server")
        return True, "Email accepted by SMTP server"
    except smtplib.SMTPAuthenticationError as e:
        msg = f"SMTP authentication failed. Check Gmail App Password/username. SMTP code={getattr(e, 'smtp_code', '?')}"
        log("FAILED: " + msg)
        return False, msg
    except smtplib.SMTPConnectError as e:
        msg = f"SMTP connection failed: {e}"
        log("FAILED: " + msg)
        return False, msg
    except smtplib.SMTPException as e:
        msg = f"SMTP error: {e}"
        log("FAILED: " + msg)
        return False, msg
    except Exception as e:
        msg = f"Email error: {type(e).__name__}: {e}"
        log("FAILED: " + msg)
        return False, msg


def apply_page_branding(page):
    theme=theme_settings()
    bg_key=f'bg_{page.lower().replace(" ","_")}'; bg=get_setting(bg_key); logo=get_setting('app_logo')
    if bg and image_row_source(bg):
        src=image_src_for_html(bg); st.markdown(f"<style>.stApp{{background-image:linear-gradient(rgba(5,18,35,.76),rgba(5,18,35,.84)),url('{src}')!important;background-size:cover!important;background-position:center!important;background-attachment:fixed!important}}</style>",unsafe_allow_html=True)
    accent=theme.get('theme_accent','#d6ae52'); btn=theme.get('theme_btn','#ff4b4b'); card=theme.get('theme_card','#102c50'); base=theme.get('theme_bg','#071b33')
    st.markdown(f"<style>.stApp{{background-color:{base}!important}}div[data-testid='stMetric'],.product-mini{{background-color:{card}!important}}h1,h2,h3,h4,.brand-title,.brand-sub{{color:{accent}!important}}.stButton>button{{border-color:{accent}!important}}div.stButton>button[kind='primary']{{background:{btn}!important;border-color:{btn}!important}}</style>",unsafe_allow_html=True)
    logo_html=''
    if logo and image_row_source(logo): logo_html=f"<img src='{image_src_for_html(logo)}' style='height:40px;max-width:92px;object-fit:contain;background:#fff;border-radius:6px;padding:2px'/><span style='margin:0 10px;color:{accent}'>✦</span>"
    st.markdown(f"<div style='display:flex;align-items:center;justify-content:center;gap:2px;margin:.1rem auto .7rem;overflow:hidden;white-space:nowrap'><div style='display:flex;align-items:center;animation:move-left 24s linear infinite;width:max-content'><span>{logo_html}RACHNA PLAYWOO &amp; HARDWEAR ✦ CRAFTED FOR YOUR SPACE ✦ PREMIUM QUALITY ✦ {logo_html}</span></div></div>",unsafe_allow_html=True)

def page_header(kicker,title,subtitle=""):
    st.markdown(f'<div class="brand-sub">{html.escape(kicker)}</div><div class="brand-title">{html.escape(title)}</div>',unsafe_allow_html=True)
    if subtitle: st.markdown(f'<div style="text-align:center;color:#cbd5e1;margin:.2rem 0 1rem">{html.escape(subtitle)}</div>',unsafe_allow_html=True)


def login_page():
    if st.session_state.get("user_id") or st.session_state.get("admin"):
        st.info("You are already signed in.")
        if st.button("Continue to Home", type="primary"):
            st.session_state.page="Home"; st.rerun()
        return
    page_header("WELCOME","Sign in to Rachna","Admin and normal user access")
    tabs=st.tabs(["Sign in","Create account"])
    with tabs[0]:
        with st.form("login"):
            uid=st.text_input("Email / User ID")
            pw=st.text_input("Password / 4-digit PIN",type="password")
            submit=st.form_submit_button("Sign in",type="primary",use_container_width=True)
        if submit:
            if password_ok(uid,pw):
                st.session_state.admin=True; st.session_state.user_id=None; st.session_state.page="Home"; st.rerun()
            else:
                rows=query("SELECT id,name,password_hash FROM rachna_users WHERE (email=%s OR phone=%s) AND active=TRUE LIMIT 1",(uid,uid))
                if rows and hmac.compare_digest(password_hash(pw),str(rows[0]["password_hash"])):
                    st.session_state.user_id=int(rows[0]["id"]); st.session_state.admin=bool(rows[0].get("is_admin")); st.session_state.page="Home"; st.rerun()
                else: st.error("Incorrect ID or password.")
    with tabs[1]:
        with st.form("signup",clear_on_submit=False):
            name=st.text_input("Name *"); phone=st.text_input("Phone *"); email=st.text_input("Email *"); age=st.number_input("Age",min_value=1,max_value=120,value=18); address=st.text_area("Address"); pin=st.text_input("Pincode",max_chars=6); dp=st.file_uploader("Profile photo (optional)",type=["jpg","jpeg","png","webp"]); password=st.text_input("Password / 4-digit PIN *",type="password",max_chars=64); create=st.form_submit_button("Create account",type="primary",use_container_width=True)
        if create:
            if not name.strip() or not phone.strip() or not email.strip() or not password.strip(): st.error("Name, phone, email and password are required.")
            elif len(password)==4 and not password.isdigit(): st.error("If using a 4-digit PIN, all 4 characters must be digits.")
            else:
                try:
                    row=query("INSERT INTO rachna_users(name,phone,email,age,address,pincode,password_hash) VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id",(name.strip(),phone.strip(),email.strip().lower(),int(age),address.strip(),pin.strip(),password_hash(password)))[0]
                    if dp: save_user_dp(dp,row["id"])
                    st.session_state.user_id=int(row["id"]); st.session_state.admin=False; st.session_state.page="Home"; st.success("Account created."); st.rerun()
                except Exception as e: st.error(f"Could not create account: {e}")

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


def auto_product_card(product, ims, width, height):
    if not ims: return
    imgs=[image_src_for_html(x) for x in ims]
    safe_imgs=json.dumps(imgs)
    name=html.escape(str(product.get("title") or "")); cat=html.escape(str(product.get("category") or "")); price=html.escape(money(product.get("price")))
    dots="" if len(imgs)<=1 else "·"*len(imgs)
    card=f"""<div class='product-mini' style='--product-h:{height}px;--product-h-mobile:{max(90,height-20)}px'><div id='pc_{product['id']}'><img src='{imgs[0]}'></div><div class='product-dots'>{dots}</div><div class='name'>{name}</div><div class='price'>{price}</div><div class='cat'>{cat}</div></div>"""
    script="""<script>(function(){const imgs=__IMGS__;let i=0;const root=document.getElementById('pc_ID');if(!root||imgs.length<2)return;setInterval(()=>{i=(i+1)%imgs.length;root.innerHTML='<img src=\"'+imgs[i]+'\" style=\"width:100%;height:100%;object-fit:contain;background:#fff;border-radius:10px;display:block\">'},1000)})();</script>""".replace('__IMGS__',safe_imgs).replace('ID',str(product['id']))
    import streamlit.components.v1 as components
    components.html(card+script,height=height+78,scrolling=False)


def gallery(master=False):
    page_header("COLLECTION","Master Gallery" if master else "Gallery","Admin product management" if master else "Browse furniture, plywood and hardware products.")
    if master and not st.session_state.get("admin"):
        st.warning("Admin login required."); return
    if master:
        with st.expander("＋ Add product",expanded=False):
            with st.form("add_product",clear_on_submit=True):
                title=st.text_input("Product name *"); category=st.text_input("Category","Hardware"); price=st.number_input("Price (₹)",min_value=0.0,step=100.0); material=st.text_input("Material"); size=st.text_input("Size"); color_names=st.multiselect("Select product colors",["Black","White","Red","Blue","Green","Yellow","Brown","Grey","Silver","Gold","Beige","Orange","Pink","Purple"]); custom_colors=st.text_input("Extra colors / hex codes",placeholder="#123456, Teak"); color=", ".join(color_names+[x.strip() for x in custom_colors.split(',') if x.strip()]); desc=st.text_area("Details"); uploads=st.file_uploader("Photos (up to 10)",type=["jpg","jpeg","png","webp"],accept_multiple_files=True); save=st.form_submit_button("Save product",type="primary")
            if save:
                if not title.strip(): st.error("Product name is required.")
                elif len(uploads or [])>10: st.error("Upload a maximum of 10 photos.")
                else:
                    try:
                        row=query("INSERT INTO rachna_products(title,category,price,material,size,color,description) VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id",(title.strip(),category,price or None,material,size,color,desc))[0]
                        for n,f in enumerate(uploads or []):
                            normalized,h=normalize_uploaded_image(f,max_size=1400,quality=80); url=github_upload(normalized,extension='jpg',folder='PRODUCT_IMG',image_hash=h)
                            query("INSERT INTO rachna_product_images(product_id,image_data,image_url,image_hash,mime_type,image_order) VALUES(%s,NULL,%s,%s,'image/jpeg',%s) ON CONFLICT DO NOTHING",(row['id'],url,h,n),fetch=False)
                        products.clear(); images.clear(); st.success("Product saved quickly."); st.rerun()
                    except Exception as e: st.error(f"Could not save product: {e}")
    items=products(active=not master)
    left,right=st.columns([2,1]); term=left.text_input("Search products",key=f"search_{master}",placeholder="Name, color, category..."); categories=sorted({str(x.get('category') or 'Other') for x in items}); cat=right.selectbox("Category",["All"]+categories,key=f"cat_{master}")
    items=[x for x in items if term.casefold() in ' '.join(str(x.get(k) or '') for k in ('title','category','material','size','color','description')).casefold() and (cat=='All' or x.get('category')==cat)]
    if not items: st.info("No products found."); return
    width,height=product_size_settings()
    st.markdown(f"<div style='text-align:center;color:#d6ae52;font-size:.78rem;margin-bottom:.6rem'>Responsive grid · {width}% width · {height}px image height · auto slide every 1 second</div>",unsafe_allow_html=True)
    # Dense responsive product grid; each product remains independently auto-sliding.
    for start_idx in range(0,len(items),4):
        cols=st.columns(4,gap='small')
        for col,p in zip(cols,items[start_idx:start_idx+4]):
            with col:
                ims=images(p['id'])
                auto_product_card(p,ims,width,height)
                if master:
                    with st.expander(f"Edit · {p['title']}"):
                        with st.form(f"edit_{p['id']}"):
                            t=st.text_input("Name",p['title']); c=st.text_input("Category",p['category']); pr=st.number_input("Price",min_value=0.0,value=float(p['price'] or 0),step=100.0); ma=st.text_input("Material",p['material'] or ''); sz=st.text_input("Size",p['size'] or ''); co=st.text_input("Color",p['color'] or ''); de=st.text_area("Details",p['description'] or ''); active=st.checkbox("Show in public gallery",bool(p['is_active'])); more=st.file_uploader("Add photos",type=['jpg','jpeg','png','webp'],accept_multiple_files=True,key=f"more_{p['id']}"); upd=st.form_submit_button("Update")
                        if upd:
                            query("UPDATE rachna_products SET title=%s,category=%s,price=%s,material=%s,size=%s,color=%s,description=%s,is_active=%s,updated_at=NOW() WHERE id=%s",(t,c,pr or None,ma,sz,co,de,active,p['id']),fetch=False)
                            for n,f in enumerate(more or [],start=len(ims)):
                                norm,h=normalize_uploaded_image(f,max_size=1400,quality=80); url=github_upload(norm,extension='jpg',folder='PRODUCT_IMG',image_hash=h); query("INSERT INTO rachna_product_images(product_id,image_data,image_url,image_hash,mime_type,image_order) VALUES(%s,NULL,%s,%s,'image/jpeg',%s) ON CONFLICT DO NOTHING",(p['id'],url,h,n),fetch=False)
                            products.clear(); images.clear(); st.rerun()
                    if st.button("Delete product",key=f"del_{p['id']}"):
                        query("DELETE FROM rachna_products WHERE id=%s",(p['id'],),fetch=False); products.clear(); images.clear(); st.rerun()

def attendance_color(status):
    return {"Present":"#16a34a","Absent":"#ef4444","Half Day":"#f59e0b","Full Leave":"#8b5cf6"}.get(status,"#64748b")


def account(master=False):
    if not master:
        user=current_user()
        page_header("ACCOUNT","My Account","Profile, attendance and personal details")
        if not user:
            st.info("Please sign in first.")
            if st.button("Go to Login",type="primary"): st.session_state.page="Login"; st.rerun()
            return
        dp=user.get('dp_url') or ''
        if dp: st.markdown(f"<img class='dp' src='{html.escape(dp,quote=True)}'>",unsafe_allow_html=True)
        else: st.markdown("<div class='profile-card'>👤</div>",unsafe_allow_html=True)
        st.markdown(f"<div class='profile-card'><h2>{html.escape(user['name'])}</h2><div>{html.escape(user['email'])} · {html.escape(user['phone'])}</div></div>",unsafe_allow_html=True)
        tabs=st.tabs(["Profile","Attendance"])
        with tabs[0]:
            with st.form("profile_edit"):
                st.text_input("Name",user['name'],disabled=True); st.text_input("Phone",user['phone'],disabled=True); st.text_input("Email",user['email'],disabled=True); age=st.number_input("Age",1,120,int(user.get('age') or 18)); address=st.text_area("Address",user.get('address') or ''); pin=st.text_input("Pincode",value=user.get('pincode') or '',max_chars=6); new_dp=st.file_uploader("Change DP",type=['jpg','jpeg','png','webp']); save=st.form_submit_button("Save profile",type='primary')
            if save:
                auto=lookup_pincode(pin) if pin else ''
                final_addr=auto if auto and not address.strip() else address.strip()
                query("UPDATE rachna_users SET age=%s,address=%s,pincode=%s,updated_at=NOW() WHERE id=%s",(int(age),final_addr,pin.strip(),user['id']),fetch=False)
                if new_dp: save_user_dp(new_dp,user['id'])
                st.success("Profile updated."); st.rerun()
            if user.get('pincode'):
                addr=lookup_pincode(user['pincode'])
                if addr: st.caption("Pincode location: "+addr)
                else: st.markdown(f"[Select location on map](https://www.google.com/maps/search/?api=1&query={user['pincode']})")
        with tabs[1]:
            staff=None
            if user.get('staff_id'): staff=find_user_staff(user['staff_id'])
            serial=st.text_input("Staff serial number",value=str(staff.get('serial_no')) if staff else '',max_chars=4)
            if serial.isdigit():
                rr=query("SELECT * FROM rachna_staff WHERE serial_no=%s AND active=TRUE",(int(serial),)); staff=rr[0] if rr else None
            if not staff: st.info("Enter your staff serial number to mark attendance.")
            else:
                d=st.date_input("Attendance date",value=date.today(),min_value=date.today(),key='user_att_date')
                opts=['Present','Absent','Half Day','Full Leave']; existing=query("SELECT status,notes FROM rachna_attendance WHERE staff_id=%s AND work_date=%s",(staff['id'],d)); default=opts.index(existing[0]['status']) if existing and existing[0]['status'] in opts else 0
                status=st.selectbox("Attendance",opts,index=default); note=st.text_input("Note",existing[0]['notes'] if existing else '')
                if st.button("Mark / Update attendance",type='primary'):
                    query("INSERT INTO rachna_attendance(staff_id,work_date,status,notes) VALUES(%s,%s,%s,%s) ON CONFLICT(staff_id,work_date) DO UPDATE SET status=EXCLUDED.status,notes=EXCLUDED.notes,updated_at=NOW()",(staff['id'],d,status,note),fetch=False); st.success("Attendance saved."); st.rerun()
                att=query("SELECT work_date,status,notes FROM rachna_attendance WHERE staff_id=%s ORDER BY work_date DESC LIMIT 90",(staff['id'],))
                for r in att:
                    st.markdown(f"<div class='att-row' style='border-left:5px solid {attendance_color(r['status'])}'><b>{r['work_date']}</b> · <span style='color:{attendance_color(r['status'])};font-weight:800'>{r['status']}</span> · {html.escape(r['notes'] or '')}</div>",unsafe_allow_html=True)
        return
    if not st.session_state.get('admin'):
        st.warning('Admin login required.'); return
    page_header("WORKSHOP MANAGEMENT","Master Account","Admin-only staff, attendance and ledger controls")
    staff_tab,att_tab,ledger_tab,week_tab=st.tabs(["Staff","Attendance","Account ledger","Weekly view"])
    with staff_tab:
        staff=query("SELECT * FROM rachna_staff WHERE active=TRUE ORDER BY name")
        with st.expander("＋ Add staff / karigar"):
            with st.form('staff_add'):
                name=st.text_input('Name *'); serial=st.number_input('Special serial number (1–9999)',1,9999,1); daily_rate=st.number_input('Daily wage (₹)',0.0,step=50.0); role=st.selectbox('Role',['Karigar','Carpenter','Helper','Painter','Installer','Other']); phone=st.text_input('Phone'); staff_color=st.color_picker('Staff color','#3b82f6'); add=st.form_submit_button('Add staff')
            if add:
                try: query('INSERT INTO rachna_staff(name,serial_no,daily_rate,role,phone,color) VALUES(%s,%s,%s,%s,%s,%s)',(name.strip(),int(serial),daily_rate,role,phone,staff_color),fetch=False); st.success('Staff added.'); st.rerun()
                except Exception as e: st.error(f'Could not add staff: {e}')
        for x in staff:
            c1,c2,c3,c4=st.columns([2,1,1,1]); c1.markdown(f"<span style='color:{x.get('color') or '#3b82f6'};font-weight:800'>●</span> {html.escape(x['name'])} #{x.get('serial_no') or '—'}",unsafe_allow_html=True); c2.write(x.get('role') or ''); c3.write(money(x.get('daily_rate'))); 
            if c4.button('Delete',key=f"staffdel_{x['id']}"):
                query('DELETE FROM rachna_staff WHERE id=%s',(x['id'],),fetch=False); st.rerun()
    with att_tab:
        d=st.date_input('Attendance date',value=date.today(),key='admin_att_date'); staff=query('SELECT * FROM rachna_staff WHERE active=TRUE ORDER BY name'); old={r['staff_id']:r for r in query('SELECT * FROM rachna_attendance WHERE work_date=%s',(d,))}
        for x in staff:
            prev=old.get(x['id']); opts=['Present','Absent','Half Day','Full Leave']; default=opts.index(prev['status']) if prev and prev['status'] in opts else 0
            c1,c2,c3=st.columns([2,2,1]); c1.markdown(f"<span style='color:{x.get('color') or '#3b82f6'}'>●</span> <b>{html.escape(x['name'])}</b>",unsafe_allow_html=True); status=c2.selectbox('Status',opts,index=default,key=f"admst_{d}_{x['id']}")
            if c3.button('Save',key=f"attsave_{d}_{x['id']}"):
                query('INSERT INTO rachna_attendance(staff_id,work_date,status,notes) VALUES(%s,%s,%s,%s) ON CONFLICT(staff_id,work_date) DO UPDATE SET status=EXCLUDED.status,updated_at=NOW()', (x['id'],d,status,''),fetch=False); st.rerun()
            if prev and c3.button('Delete entry',key=f"attdel_{d}_{x['id']}"):
                query('DELETE FROM rachna_attendance WHERE staff_id=%s AND work_date=%s',(x['id'],d),fetch=False); st.rerun()
    with ledger_tab:
        with st.form('ledger_add'):
            dt=st.date_input('Date',value=date.today()); person=st.text_input('Exact staff name / supplier'); typ=st.selectbox('Type',['Payment','Advance','Expense','Due']); amt=st.number_input('Amount (₹)',0.0,step=100.0); note=st.text_input('Note'); add=st.form_submit_button('Save entry')
        if add and person.strip() and amt>0: query('INSERT INTO rachna_ledger(entry_date,person_name,entry_type,amount,note) VALUES(%s,%s,%s,%s,%s)',(dt,person.strip(),typ,amt,note),fetch=False); st.rerun()
        rows=query('SELECT * FROM rachna_ledger ORDER BY entry_date DESC,id DESC LIMIT 500');
        if rows: st.dataframe([{'Date':r['entry_date'],'Name':r['person_name'],'Type':r['entry_type'],'Amount':money(r['amount']),'Note':r['note'] or ''} for r in rows],use_container_width=True,hide_index=True)
    with week_tab:
        start=date.today()-timedelta(days=date.today().weekday()); end=start+timedelta(days=6); rows=query('SELECT s.name,s.serial_no,s.color,a.work_date,a.status FROM rachna_attendance a JOIN rachna_staff s ON s.id=a.staff_id WHERE a.work_date BETWEEN %s AND %s ORDER BY a.work_date,s.name',(start,end));
        if rows: st.dataframe([{'Date':r['work_date'],'Name':r['name'],'Serial':r['serial_no'],'Status':r['status']} for r in rows],use_container_width=True,hide_index=True)
        else: st.info('No attendance marked this week.')


def find_user_staff(staff_id):
    rows=query('SELECT * FROM rachna_staff WHERE id=%s AND active=TRUE',(staff_id,)); return rows[0] if rows else None


def ensure_orders_table():
    """Ensure the orders table exists before an order is inserted."""
    query("""CREATE TABLE IF NOT EXISTS rachna_orders (
        id BIGSERIAL PRIMARY KEY,
        user_id BIGINT REFERENCES rachna_users(id) ON DELETE SET NULL,
        customer_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        address TEXT,
        delivery_date DATE NOT NULL,
        product_id BIGINT REFERENCES rachna_products(id) ON DELETE SET NULL,
        category TEXT,
        product_name TEXT NOT NULL,
        quantity NUMERIC(12,2) NOT NULL CHECK (quantity > 0),
        unit_price NUMERIC(12,2),
        total_price NUMERIC(12,2),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""", fetch=False)
    query("CREATE INDEX IF NOT EXISTS idx_rachna_orders_date ON rachna_orders(created_at DESC)", fetch=False)


def order_page():
    page_header('ORDER','Place an Order','Choose a product, quantity and delivery details')
    user=current_user(); items=products();
    if not items: st.info('No products available.'); return
    names=[p['title'] for p in items]; chosen=st.selectbox('Product',names); product=next(p for p in items if p['title']==chosen); qty=st.number_input('Quantity',min_value=1.0,step=1.0,value=1.0); total=float(product.get('price') or 0)*qty
    st.markdown(f"<div class='hero'><h2>{money(total)}</h2><p>{html.escape(product['category'])} · {html.escape(product['title'])} · Qty {qty:g}</p></div>",unsafe_allow_html=True)
    with st.form('order_form'):
        name=st.text_input('Customer name',value=user['name'] if user else ''); phone=st.text_input('Phone',value=user['phone'] if user else ''); address=st.text_area('Address',value=user.get('address') if user else ''); delivery=st.date_input('Delivery date',value=date.today()+timedelta(days=2),min_value=date.today()+timedelta(days=2),max_value=date.today()+timedelta(days=2)); submit=st.form_submit_button('Submit order',type='primary')
    if submit:
        if not name.strip() or not phone.strip(): st.error('Name and phone are required.')
        else:
            data={'customer_name':name.strip(),'phone':phone.strip(),'address':address.strip(),'delivery_date':delivery,'category':product['category'],'product_name':product['title'],'quantity':qty,'unit_price':product.get('price'),'total_price':total}
            ensure_orders_table()
            query('INSERT INTO rachna_orders(user_id,customer_name,phone,address,delivery_date,product_id,category,product_name,quantity,unit_price,total_price) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(user['id'] if user else None,*[data[k] for k in ['customer_name','phone','address','delivery_date']],product['id'],data['category'],data['product_name'],qty,data['unit_price'],total),fetch=False)
            st.success('Step 1/2: Order saved successfully in PostgreSQL.')
            debug_email = st.checkbox('Show email sending debug details', value=True, key='order_email_debug')
            mailed, email_status = send_order_email(data, debug=debug_email)
            if mailed:
                st.success('Step 2/2: Email sent successfully. SMTP server accepted the message.')
                st.info(f'Email destination: {cfg("ORDER_EMAIL", cfg("ADMIN_EMAIL", cfg("SMTP_TO", cfg("SMTP_USER", cfg("SMTP_USERNAME", "")))))}')
            else:
                st.error('Step 2/2: Email was NOT sent.')
                st.code(email_status)
                st.warning('Order is saved, but email failed. Check the diagnostic steps above and Streamlit Manage App → Logs for the same [RACHNA EMAIL] messages.')


@st.cache_resource(show_spinner=False)
def init_db_cached():
    # Schema setup happens once per Streamlit server process, not on every rerun.
    init_db()
    return True


def main():
    try: init_db_cached()
    except Exception as e:
        st.error('PostgreSQL connection or table setup failed.'); st.code(str(e)); st.stop()
    if 'admin' not in st.session_state: st.session_state.admin=False
    if 'user_id' not in st.session_state: st.session_state.user_id=None
    if 'page' not in st.session_state: st.session_state.page='Login'
    # Sidebar visibility is controlled by Streamlit's native, accessible hamburger toggle.
    if st.session_state.user_id and not st.session_state.admin:
        u=current_user(); dp=u.get('dp_url') if u else ''
        icon=(f"<img src='{html.escape(dp,quote=True)}' style='width:44px;height:44px;border-radius:50%;object-fit:cover;border:2px solid #d6ae52'>" if dp else "<div style='width:44px;height:44px;border-radius:50%;background:#071b33;border:2px solid #d6ae52;display:flex;align-items:center;justify-content:center;font-size:22px'>👤</div>")
        st.markdown(f"<a href='?page=Account' title='Open profile' style='position:fixed;top:.55rem;right:.75rem;z-index:999999;text-decoration:none'>{icon}</a>",unsafe_allow_html=True)
    qp=st.query_params.get('page')
    if qp in {'Home','Gallery','Order','Account','About','Contact Us','Master Gallery','Master Account','Admin Master','Login'}:
        st.session_state.page=qp
    # Keep the sidebar usable while replacing its visible Streamlit header control with the custom button.
    with st.sidebar:
        logo=get_setting('app_logo')
        if logo and image_row_source(logo): st.image(image_row_source(logo),use_container_width=True)
        st.markdown('<div style="text-align:center;color:#d6ae52;font-weight:800">RACHNA PLAYWOOD & HARDWARE</div>',unsafe_allow_html=True)
        st.divider()
        if st.session_state.admin:
            nav=['Home','Gallery','Order','Account','About','Contact Us','Master Gallery','Master Account','Admin Master']
        elif st.session_state.user_id:
            nav=['Home','Gallery','Order','Account','About','Contact Us']
        else:
            nav=['Login']
        if st.session_state.user_id and not st.session_state.admin:
            visible=public_page_names(); nav=[x for x in nav if x in visible or x=='Login']
        for p in nav:
            if st.button(p,key='nav_'+p,use_container_width=True,type='primary' if st.session_state.page==p else 'secondary'):
                st.session_state.page=p; st.rerun()
        st.divider()
        if st.session_state.admin or st.session_state.user_id:
            if st.button('Log out',use_container_width=True): st.session_state.admin=False; st.session_state.user_id=None; st.session_state.page='Login'; st.rerun()
        st.caption('© Rachna Playwoo & Hardwear')
    p=st.session_state.page
    if not st.session_state.admin and p not in ('Login',) and not st.session_state.user_id:
        p='Login'; st.session_state.page='Login'
    if not st.session_state.admin and p not in ('Login',):
        try:
            if not page_is_visible(p): st.session_state.page='Home'; p='Home'
        except Exception: pass
    apply_page_branding(p)
    if p=='Login': login_page()
    elif p=='Home':
        st.markdown(f'<div class="hero"><div class="brand-sub">CRAFTED FOR YOUR SPACE</div><h2>{APP_NAME}</h2><p>Furniture, plywood and hardware — explore our collection.</p></div>',unsafe_allow_html=True)
        items=products(); a,b,c=st.columns(3); a.metric('Products',len(items)); b.metric('Furniture',sum(x['category']=='Furniture' for x in items)); c.metric('Hardware / plywood',sum(x['category'] in ['Hardware','Plywood'] for x in items))
        if items:
            st.subheader('Featured collection'); width,height=product_size_settings();
            for start_idx in range(0,min(8,len(items)),4):
                cols=st.columns(4)
                for col,x in zip(cols,items[start_idx:start_idx+4]):
                    with col: auto_product_card(x,images(x['id']),width,height)
        else: st.info('Admin can add products using Master Gallery.')
    elif p=='Gallery': gallery(False)
    elif p=='Master Gallery': gallery(True)
    elif p=='Order': order_page()
    elif p=='Account': account(False)
    elif p=='Master Account': account(True)
    elif p=='Admin Master': site_admin_page()
    elif p=='About':
        page_header('OUR STORY','About RACHNA PLYWOOD & HARDWARE','Thoughtful materials. Reliable workmanship.')
        st.markdown(f'<div class="hero"><div class="brand-sub">PLAYWOOD · FURNITURE · HARDWARE</div><h2>{APP_NAME}</h2><p>A digital catalogue to showcase furniture, plywood and hardware products.</p></div>',unsafe_allow_html=True)
        rows=about_marquee_rows()
        if not rows:
            logo=get_setting('app_logo'); rows=[logo] if logo and image_row_source(logo) else []
        if rows:
            per_row=5; nrows=max(1,(len(rows)+per_row-1)//per_row); markup='<div class="marquee-wrap">'
            for i in range(nrows):
                group=rows[i*per_row:(i+1)*per_row] or rows; imgs=''.join(f"<img src='{image_src_for_html(r)}' alt='Rachna logo'>" for r in group); track=imgs*2; direction='right' if i%2 else 'left'; markup+=f"<div class='marquee-row {direction}'><div class='marquee-track'>{track}</div></div>"
            st.markdown(markup+'</div>',unsafe_allow_html=True)
        a,b,c=st.columns(3); a.markdown('### 🪵 Furniture\nMade-to-order furniture.'); b.markdown('### 🧰 Hardware\nFittings and hardware products.'); c.markdown('### 📐 Materials\nPlywood, sizes and colours.')
    elif p=='Contact Us':
        page_header('GET IN TOUCH','Contact Us','Contact details will be added when provided.'); st.markdown('<div class="hero"><h2>We would love to hear from you.</h2><p>Contact information coming soon.</p></div>',unsafe_allow_html=True)

# st.markdown('<div style="margin-top:2rem;padding:1rem 0;border-top:1px solid #d6ae5255;text-align:center;color:#aab6c5;font-size:.8rem">© RACHNA PLAYWOO &amp; HARDWEAR · All rights reserved</div>', unsafe_allow_html=True)

if __name__=="__main__": main()

