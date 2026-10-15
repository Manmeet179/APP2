
"""
RACHNA PLAYWOO & HARDWEAR — Streamlit catalogue and workshop accounts.
Configure credentials in Streamlit Secrets; never hard-code database credentials.
Creates separate rachna_* tables in the configured PostgreSQL database and does not modify the existing tiffin table.
"""
import io, os, hmac, base64, html
from datetime import date, timedelta
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from PIL import Image

APP_NAME = "RACHNA PLAYWOO & HARDWEAR"
st.set_page_config(page_title=APP_NAME, page_icon="🪵", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=DM+Sans:wght@400;500;600;700&display=swap');
header[data-testid="stHeader"]{background:transparent!important} html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
.stApp{background:linear-gradient(135deg,#071b33,#102c50);color:#f5f0e5}
h1,h2,h3{font-family:'Cormorant Garamond',serif!important;color:#d6ae52}
.brand-title{font-family:'Cormorant Garamond',serif;font-size:clamp(2rem,5vw,4rem);font-weight:700;letter-spacing:.04em;color:#d6ae52}
.brand-sub{letter-spacing:.24em;text-transform:uppercase;color:#9b7b42;font-size:.75rem}
.hero{padding:2rem;border-radius:22px;background:linear-gradient(120deg,#071b33,#102c50);color:white;border:1px solid #d6ae52}
.hero h2{color:white!important;font-size:2.4rem}.hero p{color:#f5ead2}
div[data-testid="stMetric"]{background:#102c50;border:1px solid #d6ae52;padding:14px;border-radius:15px}
section[data-testid="stSidebar"]{background:#071b33}
section[data-testid="stSidebar"] *{color:#f5f0e5!important}

.product-card{background:#f5f6f8;color:#26313d;border:1px solid #e4e7eb;border-radius:16px;padding:10px}
.marquee-wrap{overflow:hidden;display:flex;flex-direction:column;gap:8px;margin:1rem 0}
.marquee-row{overflow:hidden;white-space:nowrap;display:flex}
.marquee-track{display:flex;gap:10px;width:max-content;animation:move-left 35s linear infinite}
.marquee-row.right .marquee-track{animation-name:move-right}
.marquee-track img{height:48px;width:76px;object-fit:contain;background:#fff;border-radius:9px;padding:4px}
@keyframes move-left{from{transform:translateX(-50%)}to{transform:translateX(0)}}
@keyframes move-right{from{transform:translateX(0)}to{transform:translateX(-50%)}}
@media(max-width:640px){.marquee-track img{height:38px;width:60px}}
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
    """CREATE TABLE IF NOT EXISTS rachna_product_images(id BIGSERIAL PRIMARY KEY,product_id BIGINT NOT NULL REFERENCES rachna_products(id) ON DELETE CASCADE,image_data BYTEA NOT NULL,mime_type TEXT NOT NULL DEFAULT 'image/jpeg',image_order INTEGER NOT NULL DEFAULT 0,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""",
    """CREATE TABLE IF NOT EXISTS rachna_staff(id BIGSERIAL PRIMARY KEY,name TEXT NOT NULL UNIQUE,serial_no INTEGER UNIQUE,role TEXT DEFAULT 'Karigar',phone TEXT,daily_rate NUMERIC(12,2) NOT NULL DEFAULT 0,active BOOLEAN NOT NULL DEFAULT TRUE,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""",
    """CREATE TABLE IF NOT EXISTS rachna_attendance(id BIGSERIAL PRIMARY KEY,staff_id BIGINT NOT NULL REFERENCES rachna_staff(id) ON DELETE CASCADE,work_date DATE NOT NULL,status TEXT NOT NULL CHECK(status IN ('Present','Absent','Half Day','Full Leave')),notes TEXT,updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),UNIQUE(staff_id,work_date))""",
    """CREATE TABLE IF NOT EXISTS rachna_ledger(id BIGSERIAL PRIMARY KEY,entry_date DATE NOT NULL DEFAULT CURRENT_DATE,person_name TEXT NOT NULL,entry_type TEXT NOT NULL CHECK(entry_type IN ('Payment','Advance','Expense','Due')),amount NUMERIC(12,2) NOT NULL CHECK(amount>=0),note TEXT,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""",
    "CREATE INDEX IF NOT EXISTS idx_rachna_products_active ON rachna_products(is_active,created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_rachna_images_product ON rachna_product_images(product_id,image_order)",
    "CREATE INDEX IF NOT EXISTS idx_rachna_attendance_date ON rachna_attendance(work_date DESC)",
    "CREATE INDEX IF NOT EXISTS idx_rachna_ledger_date ON rachna_ledger(entry_date DESC)",
    """CREATE TABLE IF NOT EXISTS rachna_site_settings(setting_key TEXT PRIMARY KEY,image_data BYTEA,mime_type TEXT,text_value TEXT,updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""",
    """ALTER TABLE rachna_staff ADD COLUMN IF NOT EXISTS serial_no INTEGER""",
    """ALTER TABLE rachna_staff ADD COLUMN IF NOT EXISTS daily_rate NUMERIC(12,2) NOT NULL DEFAULT 0""",
    """CREATE UNIQUE INDEX IF NOT EXISTS idx_rachna_staff_serial ON rachna_staff(serial_no) WHERE serial_no IS NOT NULL""",
    """CREATE TABLE IF NOT EXISTS rachna_page_config(page_name TEXT PRIMARY KEY,visible BOOLEAN NOT NULL DEFAULT TRUE)"""]
    conn=db_connect()
    try:
        with conn:
            with conn.cursor() as cur:
                for sql in sqls: cur.execute(sql)
    finally: conn.close()

def money(v):
    return "Price on request" if v is None else "₹{:,.2f}".format(float(v))

def password_ok(user_id, entered):
    # Temporary testing credentials requested by the owner. Replace with hashed credentials before production.
    return hmac.compare_digest(str(user_id), "1") and hmac.compare_digest(str(entered), "11")


PAGE_NAMES = ["Home", "Gallery", "Master Gallery", "Account", "Master Account", "About", "Contact Us", "Login"]
SETTING_KEYS = {
    "App logo": "app_logo",
    **{f"{page} background": f"bg_{page.lower().replace(' ', '_')}" for page in PAGE_NAMES},
}

def get_setting(key):
    rows = query("SELECT image_data,mime_type,text_value FROM rachna_site_settings WHERE setting_key=%s", (key,))
    return rows[0] if rows else None

def save_image_setting(key, uploaded):
    if uploaded is None:
        return
    raw = uploaded.getvalue()
    # Validate and normalize images to keep the database payload safe and predictable.
    im = Image.open(io.BytesIO(raw))
    im.verify()
    mime = uploaded.type if uploaded.type in ("image/png", "image/jpeg", "image/webp") else "image/jpeg"
    query("""INSERT INTO rachna_site_settings(setting_key,image_data,mime_type,text_value,updated_at)
             VALUES(%s,%s,%s,NULL,NOW())
             ON CONFLICT(setting_key) DO UPDATE SET image_data=EXCLUDED.image_data,mime_type=EXCLUDED.mime_type,updated_at=NOW()""",
          (key, psycopg2.Binary(raw), mime), fetch=False)

def site_admin_page():
    if not st.session_state.get("admin"):
        st.error("Admin login required.")
        return
    page_header("SITE CONTROL CENTER", "Admin Master", "Manage the logo, marquee and page backgrounds without editing code.")
    st.info("Uploaded images are stored in your PostgreSQL database, not in a server-side image folder.")
    with st.expander("Brand logo & marquee", expanded=True):
        existing = get_setting("app_logo")
        if existing and existing.get("image_data"):
            st.image(bytes(existing["image_data"]), caption="Current app logo", width=180)
        logo = st.file_uploader("Upload app logo (PNG / JPG / WEBP)", type=["png", "jpg", "jpeg", "webp"], key="admin_logo_upload")
        if st.button("Save logo", type="primary", key="save_admin_logo"):
            if not logo:
                st.warning("Please choose a logo image first.")
            else:
                try:
                    save_image_setting("app_logo", logo)
                    st.success("Logo saved. It will appear in the app header marquee.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Logo upload failed: {e}")
    st.subheader("Page background images")
    st.caption("Upload a separate image for each page. Leave an uploader empty to keep its current background.")
    for page in PAGE_NAMES:
        key = f"bg_{page.lower().replace(' ', '_')}"
        with st.expander(f"{page} background"):
            current = get_setting(key)
            if current and current.get("image_data"):
                st.image(bytes(current["image_data"]), caption=f"Current {page} background", use_container_width=True)
            upload = st.file_uploader(f"Choose {page} background", type=["png", "jpg", "jpeg", "webp"], key=f"upload_{key}")
            if st.button(f"Save {page} background", key=f"save_{key}"):
                if not upload:
                    st.warning("Choose an image first.")
                else:
                    try:
                        save_image_setting(key, upload)
                        st.success(f"{page} background saved.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Background upload failed: {e}")
    st.subheader("About page — marquee images")
    st.caption("Upload up to 12 logos or product images. They repeat across four alternating rows.")
    uploads = st.file_uploader("Choose marquee images", type=["png","jpg","jpeg","webp"], accept_multiple_files=True, key="marquee_uploads")
    if st.button("Save About marquee images", key="save_marquee_images"):
        if not uploads or len(uploads)>12:
            st.warning("Choose between 1 and 12 images.")
        else:
            try:
                for idx, uploaded in enumerate(uploads, 1):
                    img=Image.open(io.BytesIO(uploaded.getvalue())).convert("RGB")
                    img.thumbnail((600,400))
                    buf=io.BytesIO(); img.save(buf,format="JPEG",quality=78,optimize=True)
                    query("""INSERT INTO rachna_site_settings(setting_key,image_data,mime_type,updated_at)
                    VALUES(%s,%s,'image/jpeg',NOW()) ON CONFLICT(setting_key) DO UPDATE SET image_data=EXCLUDED.image_data,mime_type=EXCLUDED.mime_type,updated_at=NOW()""",
                    (f"about_marquee_{idx}",psycopg2.Binary(buf.getvalue())),fetch=False)
                st.success("Marquee images saved."); st.rerun()
            except Exception as exc: st.error(f"Could not save images: {exc}")
    st.markdown("**Theme:** Navy blue `#071B33` · Royal navy `#102C50` · Gold `#D6AE52`")
    st.caption("Premium typography: Cormorant Garamond headings + DM Sans interface.")
    st.subheader("Page access / public visibility")
    public_pages=["Home","Gallery","Account","About","Contact Us"]
    for pg in public_pages:
        query("INSERT INTO rachna_page_config(page_name,visible) VALUES(%s,TRUE) ON CONFLICT(page_name) DO NOTHING",(pg,),fetch=False)
    page_rows=query("SELECT page_name,visible FROM rachna_page_config WHERE page_name = ANY(%s) ORDER BY page_name",(public_pages,))
    with st.form("page_visibility_form"):
        visibility={r["page_name"]:st.checkbox("Show "+r["page_name"]+" to public users",value=bool(r["visible"]),key="page_vis_"+r["page_name"]) for r in page_rows}
        save_pages=st.form_submit_button("Save page visibility")
    if save_pages:
        for pg,val in visibility.items():
            query("UPDATE rachna_page_config SET visible=%s WHERE page_name=%s",(val,pg),fetch=False)
        st.success("Page visibility saved."); st.rerun()
    st.subheader("Global theme colors")
    with st.form("theme_color_form"):
        bg=st.color_picker("Background color","#071b33")
        card=st.color_picker("Card / panel color","#102c50")
        accent=st.color_picker("Accent / heading color","#d6ae52")
        save_theme=st.form_submit_button("Save theme colors")
    if save_theme:
        for key,val in [("theme_bg",bg),("theme_card",card),("theme_accent",accent)]:
            query("INSERT INTO rachna_site_settings(setting_key,text_value) VALUES(%s,%s) ON CONFLICT(setting_key) DO UPDATE SET text_value=EXCLUDED.text_value,updated_at=NOW()", (key,val),fetch=False)
        st.success("Theme colors saved."); st.rerun()

def apply_page_branding(page):
    try:
        theme_rows=query("SELECT setting_key,text_value FROM rachna_site_settings WHERE setting_key IN ('theme_bg','theme_card','theme_accent')")
        theme={r["setting_key"]:r["text_value"] for r in theme_rows}
        if theme:
            st.markdown(f"<style>.stApp{{background-color:{theme.get('theme_bg','#071b33')}!important}} div[data-testid='stMetric'],.stContainer{{background-color:{theme.get('theme_card','#102c50')}}} h1,h2,h3,.brand-title{{color:{theme.get('theme_accent','#d6ae52')}!important}}</style>",unsafe_allow_html=True)
    except Exception:
        pass
    bg_key = f"bg_{page.lower().replace(' ', '_')}"
    bg = get_setting(bg_key)
    logo = get_setting("app_logo")
    if bg and bg.get("image_data"):
        encoded = base64.b64encode(bytes(bg["image_data"])).decode("ascii")
        mime = bg.get("mime_type") or "image/jpeg"
        st.markdown(f"""<style>
        .stApp {{ background-image: linear-gradient(rgba(5,18,35,.78),rgba(5,18,35,.84)),url('data:{mime};base64,{encoded}') !important;
        background-size: cover !important; background-position: center !important; background-attachment: fixed !important; }}
        </style>""", unsafe_allow_html=True)
    logo_html = ""
    if logo and logo.get("image_data"):
        encoded_logo = base64.b64encode(bytes(logo["image_data"])).decode("ascii")
        mime = logo.get("mime_type") or "image/png"
        logo_html = f'<img src="data:{mime};base64,{encoded_logo}" style="height:42px;max-width:100px;object-fit:contain;margin-right:14px"/>'
    st.markdown(f"""<div class="brand-marquee">{logo_html}<div class="marquee-track"><span>RACHNA PLAYWOO &amp; HARDWEAR&nbsp; ✦ &nbsp;CRAFTED FOR YOUR SPACE&nbsp; ✦ &nbsp;PREMIUM QUALITY&nbsp; ✦ &nbsp;</span><span>RACHNA PLAYWOO &amp; HARDWEAR&nbsp; ✦ &nbsp;CRAFTED FOR YOUR SPACE&nbsp; ✦ &nbsp;PREMIUM QUALITY&nbsp; ✦ &nbsp;</span></div></div>""", unsafe_allow_html=True)

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
        "SELECT id, image_data FROM rachna_product_images WHERE product_id=%s ORDER BY image_order,id",
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
        safe_rows.append({"id": int(row["id"]), "image_data": image_bytes})
    return safe_rows

def gallery(master=False):
    page_header("COLLECTION","Master Gallery" if master else "Gallery",
        "Admin product management" if master else "Browse furniture, plywood and hardware products.")
    if master and not st.session_state.get("admin"):
        st.warning("Admin login required."); return
    if not master:
        items = products(active=True)
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
                    ims = images(product["id"])
                    with st.container(border=True):
                        if ims:
                            st.image(bytes(ims[0]["image_data"]), use_container_width=True)
                        st.markdown(f"**{html.escape(str(product['title']))}**")
                        with st.expander("Learn More", expanded=False):
                            if len(ims)>1:
                                st.image([bytes(x["image_data"]) for x in ims], use_container_width=True)
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
                        for n,f in enumerate(uploads or []):
                            im=Image.open(io.BytesIO(f.getvalue())).convert("RGB"); im.thumbnail((1800,1800))
                            out=io.BytesIO(); im.save(out,format="JPEG",quality=88,optimize=True)
                            query("INSERT INTO rachna_product_images(product_id,image_data,mime_type,image_order) VALUES(%s,%s,%s,%s)",
                                (row["id"],psycopg2.Binary(out.getvalue()),"image/jpeg",n),fetch=False)
                        products.clear(); images.clear(); st.success("Product saved."); st.rerun()
                    except Exception as e: st.error(f"Could not save product: {e}")
    items=products(active=not master)
    if master: items=products(active=False)
    if not items: st.info("No products yet. Admin can add them from Master Gallery."); return
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
                    ims=images(p["id"])
                    if ims:
                        key=f'carousel_{p["id"]}'
                        if key not in st.session_state: st.session_state[key]=0
                        idx=st.session_state[key]%len(ims)
                        st.image(bytes(ims[idx]["image_data"]),caption=f"Photo {idx+1} of {len(ims)}",use_container_width=True)
                        if len(ims)>1:
                            import streamlit.components.v1 as components
                            slides=[]
                            for imrow in ims:
                                b64=base64.b64encode(bytes(imrow["image_data"])).decode("ascii")
                                slides.append(f'<img src="data:image/jpeg;base64,{b64}" style="width:100%;height:260px;object-fit:contain;flex:0 0 100%;scroll-snap-align:center"/>')
                            components.html(f'<div style="display:flex;overflow-x:auto;scroll-snap-type:x mandatory;gap:8px;touch-action:pan-x;border-radius:12px">{"".join(slides)}</div><div style="text-align:center;color:#aaa;font:12px sans-serif;margin-top:5px">Swipe to view more photos · {len(ims)} photos</div>',height=290)
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
                                    for n,f in enumerate(more or [],start=len(ims)):
                                        im=Image.open(io.BytesIO(f.getvalue())).convert("RGB"); im.thumbnail((1800,1800))
                                        out=io.BytesIO(); im.save(out,format="JPEG",quality=88,optimize=True)
                                        query("INSERT INTO rachna_product_images(product_id,image_data,mime_type,image_order) VALUES(%s,%s,%s,%s)",
                                            (p["id"],psycopg2.Binary(out.getvalue()),"image/jpeg",n),fetch=False)
                                    products.clear(); images.clear(); st.success("Updated."); st.rerun()
                            if st.button("Delete product",key=f'del_{p["id"]}'):
                                query("DELETE FROM rachna_products WHERE id=%s",(p["id"],),fetch=False); products.clear(); images.clear(); st.rerun()
                            if ims:
                                choices={f'Photo {i+1} (ID {im["id"]})':im["id"] for i,im in enumerate(ims)}
                                chosen=st.selectbox("Photo to delete",list(choices),key=f'imgdel_sel_{p["id"]}')
                                if st.button("Delete selected photo",key=f'imgdel_{p["id"]}'):
                                    query("DELETE FROM rachna_product_images WHERE id=%s",(choices[chosen],),fetch=False); st.rerun()

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

def main():
    try: init_db()
    except Exception as e:
        st.error("PostgreSQL connection or table setup failed."); st.code(str(e))
        st.info("Set DB_HOST, DB_NAME, DB_USER, DB_PASSWORD and DB_PORT in Streamlit Secrets. Aiven normally requires SSL.")
        st.stop()
    if "admin" not in st.session_state: st.session_state.admin=False
    if "page" not in st.session_state: st.session_state.page="Home"
    with st.sidebar:
        logo_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "rachna_logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        else:
            st.markdown('<div class="brand-title" style="font-size:2.2rem;color:#d6ae52">RACHNA</div><div class="brand-sub">PLAYWOOD & HARDWARE</div>',unsafe_allow_html=True)
        st.divider()
        nav=["Home","Gallery","Account","About","Contact Us"]
        if not st.session_state.admin:
            try:
                visible_rows=query("SELECT page_name FROM rachna_page_config WHERE visible=TRUE")
                if visible_rows:
                    visible={r["page_name"] for r in visible_rows}
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
            access=query("SELECT visible FROM rachna_page_config WHERE page_name=%s",(p,))
            if access and not bool(access[0]["visible"]):
                st.session_state.page="Home"; p="Home"
                st.warning("This page is not available to public users.")
        except Exception:
            pass
    apply_page_branding(p)
    if p=="Login": login_page()
    elif p=="Home":
        st.markdown(f'<div class="hero"><div class="brand-sub">CRAFTED FOR YOUR SPACE</div><h2>{APP_NAME}</h2><p>Furniture, plywood and hardware — explore our collection.</p></div>',unsafe_allow_html=True)
        items=products()
        a,b,c=st.columns(3); a.metric("Products",len(items)); b.metric("Furniture",sum(x["category"]=="Furniture" for x in items)); c.metric("Hardware / plywood",sum(x["category"] in ["Hardware","Plywood"] for x in items))
        st.subheader("Featured collection")
        if items:
            cols=st.columns(min(3,len(items)))
            for col,x in zip(cols,items[:3]):
                with col:
                    ims=images(x["id"])
                    if ims: st.image(bytes(ims[0]["image_data"]),use_container_width=True)
                    st.subheader(x["title"]); st.markdown(f"**{money(x['price'])}**"); st.caption(x["category"]); st.write((x["description"] or "")[:160])
        else: st.info("Admin can add products using Master Gallery.")
    elif p=="Gallery": gallery(False)
    elif p=="Master Gallery": gallery(True)
    elif p=="Account": account(False)
    elif p=="Master Account": account(True)
    elif p=="Admin Master": site_admin_page()
    elif p=="About":
        page_header("OUR STORY","About Rachna","Thoughtful materials. Reliable workmanship.")
        st.markdown(f'<div class="hero"><div class="brand-sub">PLAYWOOD · FURNITURE · HARDWARE</div><h2>{APP_NAME}</h2><p>A digital catalogue to showcase furniture, plywood and hardware products.</p></div>',unsafe_allow_html=True)
        try:
            rows=query("SELECT setting_key,image_data,mime_type FROM rachna_site_settings WHERE setting_key LIKE 'about_marquee_%' AND image_data IS NOT NULL ORDER BY setting_key")
        except Exception: rows=[]
        if not rows:
            logo=get_setting("app_logo")
            rows=[logo] if logo and logo.get("image_data") else []
        if rows:
            imgs="".join(f'<img src="data:{r.get("mime_type") or "image/jpeg"};base64,{base64.b64encode(bytes(r["image_data"])).decode("ascii")}" alt="Rachna image"/>' for r in rows)
            track=imgs*2
            markup='<div class="marquee-wrap">'
            for i in range(4):
                direction="right" if i in (1,3) else "left"
                markup+=f'<div class="marquee-row {direction}"><div class="marquee-track">{track}</div></div>'
            st.markdown(markup+'</div>',unsafe_allow_html=True)
        a,b,c=st.columns(3)
        a.markdown("### 🪵 Furniture\\nMade-to-order furniture.")
        b.markdown("### 🧰 Hardware\\nFittings and hardware products.")
        c.markdown("### 📐 Materials\\nPlywood, sizes and colours.")
    elif p=="Contact Us":
        page_header("GET IN TOUCH","Contact Us","Contact details will be added when provided.")
        st.markdown('<div class="hero"><h2>We would love to hear from you.</h2><p>Contact information coming soon.</p></div>',unsafe_allow_html=True)

# st.markdown('<div style="margin-top:2rem;padding:1rem 0;border-top:1px solid #d6ae5255;text-align:center;color:#aab6c5;font-size:.8rem">© RACHNA PLAYWOO &amp; HARDWEAR · All rights reserved</div>', unsafe_allow_html=True)

if __name__=="__main__": main()

