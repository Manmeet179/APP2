from email.message import EmailMessage

"""
RACHNA PLAYWOO & HARDWEAR — Streamlit catalogue and workshop accounts.
Configure credentials in Streamlit Secrets; never hard-code database credentials.
Creates separate rachna_* tables in the configured PostgreSQL database and does not modify the existing tiffin table.
"""
import io, os, hmac, base64, html, hashlib, smtplib, ssl, json, mimetypes, secrets
from datetime import date, timedelta, datetime
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from PIL import Image
import requests
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.utils import ImageReader

APP_NAME = "RACHNA PLAYWOOD & HARDWEAR"
st.set_page_config(page_title=APP_NAME, page_icon="🪵", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
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
.marquee-wrap{overflow:hidden;display:flex;flex-direction:column;gap:10px;margin:1rem 0;width:100%}
.marquee-row{overflow:hidden;white-space:nowrap;display:flex;width:100%}
.marquee-track{display:flex;align-items:center;gap:10px;width:max-content;animation:move-left 30s linear infinite;will-change:transform}
.marquee-row.right .marquee-track{animation-name:move-right}
.marquee-logo-box{width:84px!important;height:52px!important;min-width:84px!important;max-width:84px!important;flex:0 0 84px!important;box-sizing:border-box!important;display:flex!important;align-items:center!important;justify-content:center!important;background:#fff;border-radius:9px;padding:4px;overflow:hidden}
.marquee-logo-box img{width:100%!important;height:100%!important;max-width:100%!important;max-height:100%!important;display:block!important;object-fit:contain!important;object-position:center!important}
@keyframes move-left{from{transform:translateX(-50%)}to{transform:translateX(0)}}
@keyframes move-right{from{transform:translateX(0)}to{transform:translateX(-50%)}}
@media(max-width:1100px){.product-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:720px){.block-container{padding-top:4rem!important}.product-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.product-mini{padding:6px}.product-mini img{height:var(--product-h-mobile,125px)}.marquee-logo-box{width:72px!important;height:44px!important;min-width:72px!important;max-width:72px!important;flex-basis:72px!important;padding:3px}header[data-testid="stHeader"] button[data-testid="stSidebarCollapseButton"],header[data-testid="stHeader"] button[data-testid="stSidebarExpandButton"]{width:42px!important;height:40px!important}}
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
    """CREATE TABLE IF NOT EXISTS rachna_order_items(id BIGSERIAL PRIMARY KEY,order_id BIGINT NOT NULL REFERENCES rachna_orders(id) ON DELETE CASCADE,product_id BIGINT REFERENCES rachna_products(id) ON DELETE SET NULL,product_name TEXT NOT NULL,category TEXT,quantity NUMERIC(12,2) NOT NULL CHECK(quantity>0),unit_price NUMERIC(12,2),line_total NUMERIC(12,2),created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""",
    """ALTER TABLE rachna_orders ADD COLUMN IF NOT EXISTS order_number TEXT""",
    """ALTER TABLE rachna_orders ADD COLUMN IF NOT EXISTS customer_email TEXT""",
    """ALTER TABLE rachna_orders ADD COLUMN IF NOT EXISTS payment_method TEXT DEFAULT 'COD'""",
    """ALTER TABLE rachna_orders ADD COLUMN IF NOT EXISTS payment_status TEXT DEFAULT 'Pending'""",
    """ALTER TABLE rachna_orders ADD COLUMN IF NOT EXISTS order_status TEXT DEFAULT 'Order Placed'""",
    """ALTER TABLE rachna_orders ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()""",
    """ALTER TABLE rachna_orders ADD COLUMN IF NOT EXISTS tracking_token TEXT""",
    """CREATE UNIQUE INDEX IF NOT EXISTS uq_rachna_order_tracking_token ON rachna_orders(tracking_token) WHERE tracking_token IS NOT NULL""",
    """CREATE UNIQUE INDEX IF NOT EXISTS uq_rachna_order_number ON rachna_orders(order_number) WHERE order_number IS NOT NULL""",
    """CREATE INDEX IF NOT EXISTS idx_rachna_orders_user ON rachna_orders(user_id,created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS rachna_order_status_history(id BIGSERIAL PRIMARY KEY,order_id BIGINT NOT NULL REFERENCES rachna_orders(id) ON DELETE CASCADE,status TEXT NOT NULL,note TEXT,changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""",
    """CREATE INDEX IF NOT EXISTS idx_rachna_order_status_history ON rachna_order_status_history(order_id,changed_at)""",
    """ALTER TABLE rachna_staff ADD COLUMN IF NOT EXISTS color TEXT DEFAULT '#3b82f6'""",
    """ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS pincode TEXT""",
    """ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS staff_id BIGINT REFERENCES rachna_staff(id) ON DELETE SET NULL""",
    """ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS otp_hash TEXT""",
    """ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS otp_expires_at TIMESTAMPTZ""",
    """ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS otp_attempts INTEGER NOT NULL DEFAULT 0""",
    """ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE""",
    """ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS otp_hash TEXT""",
    """ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS otp_expires_at TIMESTAMPTZ""",
    """ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS otp_attempts INTEGER NOT NULL DEFAULT 0""",
    """UPDATE rachna_users SET email_verified=TRUE WHERE email_verified=FALSE AND COALESCE(password_hash,'') <> ''""",
    """CREATE INDEX IF NOT EXISTS idx_rachna_users_email ON rachna_users(email)""",
    """CREATE TABLE IF NOT EXISTS rachna_email_log(
        id BIGSERIAL PRIMARY KEY,
        sender_email TEXT, sender_name TEXT, recipient_email TEXT NOT NULL, cc_email TEXT,
        subject TEXT NOT NULL, text_body TEXT, html_body TEXT,
        email_type TEXT NOT NULL DEFAULT 'Manual', related_order_id BIGINT REFERENCES rachna_orders(id) ON DELETE SET NULL,
        status TEXT NOT NULL DEFAULT 'Sent', error_message TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""",
    """CREATE INDEX IF NOT EXISTS idx_rachna_email_log_created ON rachna_email_log(created_at DESC)""",
    """CREATE INDEX IF NOT EXISTS idx_rachna_orders_date ON rachna_orders(created_at DESC)""",
    "INSERT INTO rachna_page_config(page_name,visible) VALUES ('Home',TRUE),('Gallery',TRUE),('Order',TRUE),('Account',TRUE),('About',TRUE),('Contact Us',TRUE) ON CONFLICT(page_name) DO NOTHING""" ]
    # Run schema statements independently so one non-critical migration cannot
    # roll back later migrations (important for existing installations).
    for sql in sqls:
        conn = db_connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        except Exception:
            conn.rollback()
            # Keep startup alive; critical tables/columns are re-checked below.
        finally:
            conn.close()

    # Mandatory user-auth migration: run separately and commit each statement.
    user_migrations = [
        "ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS otp_hash TEXT",
        "ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS otp_expires_at TIMESTAMPTZ",
        "ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS otp_attempts INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
    ]
    for sql in user_migrations:
        conn = db_connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        finally:
            conn.close()

    # Existing password/PIN users are trusted as already-verified accounts.
    conn = db_connect()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE rachna_users SET email_verified=TRUE WHERE email_verified=FALSE AND COALESCE(password_hash,'') <> ''")
        conn.commit()
    finally:
        conn.close()

def ensure_auth_schema():
    """Repair auth columns on every app start, even when Streamlit cache is warm."""
    conn = db_connect()
    try:
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS otp_hash TEXT")
            cur.execute("ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS otp_expires_at TIMESTAMPTZ")
            cur.execute("ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS otp_attempts INTEGER NOT NULL DEFAULT 0")
            cur.execute("ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE")
            cur.execute("ALTER TABLE rachna_users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def money(v):
    return "Price on request" if v is None else "₹{:,.2f}".format(float(v))

def password_hash(value):
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()

def make_otp():
    return f"{secrets.randbelow(900000) + 100000:06d}"

def email_brand_name():
    return str(cfg("EMAIL_BRAND_NAME", "RACHNA PLYWOOD & HARDWEAR VADGAM")).strip() or "RACHNA PLYWOOD & HARDWEAR VADGAM"

def get_email_logo():
    logo_url=""; logo_bytes=None; logo_mime="image/jpeg"
    try:
        logo=get_setting("app_logo")
        if logo:
            logo_url=str(logo.get("image_url") or "").strip()
            logo_bytes=logo.get("image_data") or None
            logo_mime=str(logo.get("mime_type") or "image/jpeg")
            if logo_url and not logo_bytes:
                try:
                    lr=requests.get(logo_url,timeout=8)
                    if lr.ok:
                        logo_bytes=lr.content
                        logo_mime=lr.headers.get("Content-Type","image/jpeg").split(";")[0]
                except Exception:
                    pass
    except Exception:
        pass
    logo_html=(f'<img src="cid:rachna_logo" alt="Rachna" style="max-height:76px;max-width:240px;display:block;margin:0 auto 12px;object-fit:contain;">' if logo_bytes else (f'<img src="{html.escape(logo_url, quote=True)}" alt="Rachna" style="max-height:76px;max-width:240px;display:block;margin:0 auto 12px;object-fit:contain;">' if logo_url else ""))
    return logo_html,logo_bytes,logo_mime

def email_shell(body_html, logo_html, title, subtitle=""):
    brand=html.escape(email_brand_name())
    title_e=html.escape(title)
    sub_html=f'<div style="color:#cbd5e1;font-size:13px;margin-top:6px;">{html.escape(subtitle)}</div>' if subtitle else ""
    return (f'<!doctype html><html><body style="margin:0;padding:0;background:#f3f0e8;font-family:Arial,Helvetica,sans-serif;color:#172033;">'
            f'<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:#f3f0e8;padding:24px 8px;"><tr><td align="center">'
            f'<table width="620" cellpadding="0" cellspacing="0" role="presentation" style="max-width:620px;width:100%;background:#fff;border-radius:18px;overflow:hidden;">'
            f'<tr><td style="background:#071b33;padding:28px 22px;text-align:center;border-bottom:4px solid #d6ae52;">{logo_html}'
            f'<div style="color:#d6ae52;font-size:13px;letter-spacing:3px;text-transform:uppercase;font-weight:800;">{brand}</div>'
            f'<div style="color:#fff;font-size:24px;font-weight:800;margin-top:8px;">{title_e}</div>{sub_html}</td></tr>'
            f'<tr><td style="padding:26px 24px;">{body_html}</td></tr>'
            f'<tr><td style="background:#071b33;padding:18px 20px;text-align:center;color:#d8d8d8;font-size:12px;line-height:1.6;">'
            f'<b style="color:#d6ae52;">{brand}</b><br>Crafted for your space · Premium quality</td></tr></table></td></tr></table></body></html>')

def log_email_message(recipient, cc, subject, text_body, html_body, email_type="Manual", related_order_id=None, status="Sent", error_message=None, sender_email=None, sender_name=None):
    try:
        query("""INSERT INTO rachna_email_log(sender_email,sender_name,recipient_email,cc_email,subject,text_body,html_body,email_type,related_order_id,status,error_message,created_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())""",
              (sender_email or str(cfg("SMTP_USER") or cfg("SMTP_USERNAME") or cfg("SMTP_EMAIL") or ""),sender_name or email_brand_name(),recipient,cc,subject,text_body,html_body,email_type,related_order_id,status,error_message),fetch=False)
    except Exception as e:
        print(f"[RACHNA EMAIL LOG] {type(e).__name__}: {e}",flush=True)

def send_generic_email(to_email, subject, details, email_type="Admin Manual"):
    host=cfg("SMTP_HOST","smtp.gmail.com"); port=int(cfg("SMTP_PORT","587")); user=cfg("SMTP_USER") or cfg("SMTP_USERNAME") or cfg("SMTP_EMAIL"); pw=cfg("SMTP_PASSWORD"); from_name=str(cfg("SMTP_FROM_NAME") or email_brand_name()).strip()
    recipient=str(to_email or "").strip().lower(); subject=str(subject or "").strip(); details=str(details or "").strip()
    if not recipient or "@" not in recipient: return False,"Enter a valid recipient email."
    if not subject: return False,"Subject is required."
    if not details: return False,"Details are required."
    if not user or not pw: return False,"SMTP_USER/SMTP_PASSWORD are not configured."
    logo_html,logo_bytes,logo_mime=get_email_logo()
    body=f'<div style="white-space:pre-wrap;font-size:15px;line-height:1.7;color:#27364b;">{html.escape(details)}</div>'
    html_body=email_shell(body,logo_html,subject,email_type.upper())
    text_body=f"{email_brand_name()}\n\n{details}"
    msg=EmailMessage(); msg["Subject"]=subject; msg["From"]=f"{from_name} <{user}>"; msg["To"]=recipient; msg.set_content(text_body); msg.add_alternative(html_body,subtype="html")
    if logo_bytes:
        mt,st=logo_mime.split("/",1) if "/" in logo_mime else ("image","jpeg")
        msg.get_payload()[1].add_related(logo_bytes,maintype=mt,subtype=st,cid="<rachna_logo>",filename="rachna-logo")
    try:
        if port==465:
            with smtplib.SMTP_SSL(host,port,context=ssl.create_default_context(),timeout=15) as smtp:
                smtp.login(user,pw); smtp.send_message(msg)
        else:
            with smtplib.SMTP(host,port,timeout=15) as smtp:
                smtp.ehlo(); smtp.starttls(context=ssl.create_default_context()); smtp.ehlo(); smtp.login(user,pw); smtp.send_message(msg)
        log_email_message(recipient,"",subject,text_body,html_body,email_type,status="Sent",sender_email=user,sender_name=from_name)
        return True,"Email sent successfully."
    except Exception as e:
        err=f"{type(e).__name__}: {e}"; log_email_message(recipient,"",subject,text_body,html_body,email_type,status="Failed",error_message=err,sender_email=user,sender_name=from_name)
        return False,f"Email failed: {err}"

def send_registration_otp(email, name, otp):
    subject=f"{email_brand_name()} — Email Verification OTP"
    logo_html,logo_bytes,logo_mime=get_email_logo()
    body=f'<div style="text-align:center;"><h2 style="color:#071b33;margin:0 0 8px;">Verify your email</h2><p style="color:#5b6778;">Hello {html.escape(name)}, use this 6-digit OTP to complete registration.</p><div style="display:inline-block;background:#fff;color:#071b33;font-size:32px;font-weight:800;letter-spacing:9px;padding:16px 22px;border-radius:14px;border:1px solid #d6ae52;margin:14px 0;">{otp}</div><p style="color:#777;font-size:13px;">Valid for 5 minutes · One-time use</p></div>'
    html_body=email_shell(body,logo_html,"Verify your email","EMAIL VERIFICATION OTP")
    text_body=f"Hello {name},\n\nYour 6-digit OTP is: {otp}\n\nValid for 5 minutes and one-time use.\n\n{email_brand_name()}"
    host=cfg("SMTP_HOST","smtp.gmail.com"); port=int(cfg("SMTP_PORT","587")); user=cfg("SMTP_USER") or cfg("SMTP_USERNAME") or cfg("SMTP_EMAIL"); pw=cfg("SMTP_PASSWORD"); from_name=str(cfg("SMTP_FROM_NAME") or email_brand_name()).strip()
    if not user or not pw: return False,"SMTP_USER/SMTP_PASSWORD are not configured."
    msg=EmailMessage(); msg["Subject"]=subject; msg["From"]=f"{from_name} <{user}>"; msg["To"]=email; msg.set_content(text_body); msg.add_alternative(html_body,subtype="html")
    if logo_bytes:
        mt,st=logo_mime.split("/",1) if "/" in logo_mime else ("image","jpeg"); msg.get_payload()[1].add_related(logo_bytes,maintype=mt,subtype=st,cid="<rachna_logo>",filename="rachna-logo")
    try:
        if port==465:
            with smtplib.SMTP_SSL(host,port,context=ssl.create_default_context(),timeout=15) as smtp: smtp.login(user,pw); smtp.send_message(msg)
        else:
            with smtplib.SMTP(host,port,timeout=15) as smtp: smtp.ehlo(); smtp.starttls(context=ssl.create_default_context()); smtp.ehlo(); smtp.login(user,pw); smtp.send_message(msg)
        log_email_message(email,"",subject,text_body,html_body,"OTP",status="Sent",sender_email=user,sender_name=from_name)
        return True,"OTP email sent."
    except Exception as e:
        err=f"{type(e).__name__}: {e}"; log_email_message(email,"",subject,text_body,html_body,"OTP",status="Failed",error_message=err,sender_email=user,sender_name=from_name); return False,f"OTP email failed: {err}"


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


PAGE_NAMES = ["Home", "Gallery", "Order", "Account", "Order History", "Order Details", "Track Order", "Master Gallery", "Master Account", "About", "Contact Us", "Login", "Admin Master"]
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


def ensure_email_log_table():
    # Safety net for existing deployments where the startup migration was not run.
    query("""CREATE TABLE IF NOT EXISTS rachna_email_log(
        id BIGSERIAL PRIMARY KEY,
        sender_email TEXT, sender_name TEXT, recipient_email TEXT NOT NULL, cc_email TEXT,
        subject TEXT NOT NULL, text_body TEXT, html_body TEXT,
        email_type TEXT NOT NULL DEFAULT 'Manual', related_order_id BIGINT REFERENCES rachna_orders(id) ON DELETE SET NULL,
        status TEXT NOT NULL DEFAULT 'Sent', error_message TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""", fetch=False)
    query("CREATE INDEX IF NOT EXISTS idx_rachna_email_log_created ON rachna_email_log(created_at DESC)", fetch=False)


def emails_page():
    if not st.session_state.get('admin'):
        st.error('Admin login required.'); return
    ensure_email_log_table()
    page_header('COMMUNICATIONS','Communications','Send Rachna-branded emails and view emails sent from this app')
    tab_send, tab_inbox = st.tabs(['✉ Send Mail','📥 Mailbox'])
    with tab_send:
        with st.form('admin_send_mail_form', clear_on_submit=False):
            recipient=st.text_input('To Email *', placeholder='customer@example.com')
            subject=st.text_input('Subject *', placeholder='Your message subject')
            details=st.text_area('Details *', height=220, placeholder='Write your message here...')
            send=st.form_submit_button('Send Mail', type='primary', use_container_width=True)
        if send:
            ok,msg=send_generic_email(recipient,subject,details,'Admin Manual')
            if ok: st.success(msg)
            else: st.error(msg)
    with tab_inbox:
        search=st.text_input('Search mails', placeholder='Email, subject, order...')
        rows=query('SELECT id,sender_email,sender_name,recipient_email,cc_email,subject,text_body,html_body,email_type,related_order_id,status,error_message,created_at FROM rachna_email_log ORDER BY created_at DESC LIMIT 500')
        if search.strip():
            q=search.strip().casefold(); rows=[r for r in rows if q in ' '.join(str(r.get(k) or '') for k in ('sender_email','sender_name','recipient_email','cc_email','subject','email_type','related_order_id')).casefold()]
        if not rows:
            st.info('No emails found. Emails sent by OTP, orders and Admin → Emails will appear here.')
        else:
            for r in rows:
                status_icon='✅' if r.get('status')=='Sent' else '❌'; when=str(r.get('created_at') or '')
                label=f"{status_icon} {r.get('subject') or '(No subject)'} · {r.get('recipient_email') or ''} · {when}"
                with st.expander(label, expanded=False):
                    c1,c2=st.columns([3,1])
                    c1.markdown(f"**From:** {html.escape(str(r.get('sender_name') or email_brand_name()))} <{html.escape(str(r.get('sender_email') or ''))}>  \n**To:** {html.escape(str(r.get('recipient_email') or ''))}  \n**CC:** {html.escape(str(r.get('cc_email') or '—'))}  \n**Type:** {html.escape(str(r.get('email_type') or ''))}  \n**Date:** {html.escape(when)}")
                    c2.metric('Status',str(r.get('status') or ''))
                    if r.get('status')!='Sent' and r.get('error_message'): st.error(str(r['error_message']))
                    st.divider()
                    if r.get('html_body'): st.components.v1.html(str(r['html_body']),height=700,scrolling=True)
                    else: st.text(str(r.get('text_body') or ''))


def site_admin_page():
    if not st.session_state.get('admin'):
        st.error('Admin login required.'); return
    page_header('ADMIN CONSOLE','Admin Console','Brand, visibility, product sizing and admin access')
    if st.button('✉ Open Communications', type='primary', use_container_width=True, key='open_emails_from_admin_master'):
        st.session_state.page='Emails'; st.session_state._consumed_page_qp='Emails'; st.rerun()
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

    st.subheader('About statistics controls')
    real_stats=st.checkbox('Show real customer/product/company counts',value=text_setting('about_real_stats','true').lower()=='true',key='about_real_stats_toggle')
    if st.button('Save statistics mode',key='save_stats_mode'):
        save_text_setting('about_real_stats','true' if real_stats else 'false'); st.success('Statistics mode saved.'); st.rerun()

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


@st.cache_data(ttl=30, show_spinner=False)
def current_user_by_id(uid):
    return find_user_by_id(uid) if uid else None

def current_user():
    uid=st.session_state.get("user_id")
    return current_user_by_id(uid) if uid else None


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



def order_status_steps():
    return ["Order Placed", "Order Confirmed", "Order on Shipment", "Order in the Way", "Order Delivered"]

def status_index(status):
    try: return order_status_steps().index(status)
    except ValueError: return 0

def tracking_html(status):
    """Email-safe tracking bar. Five equal segments prevent the old bar overflow."""
    steps=order_status_steps(); current=status_index(status)
    circles=[]; labels=[]; bars=[]
    for i,step in enumerate(steps):
        done=i<=current
        bg="#16a34a" if done else "#cbd5e1"
        fg="#166534" if done else "#64748b"
        circles.append(f'<td width="20%" align="center" style="padding:0 2px"><div style="width:24px;height:24px;border-radius:50%;background:{bg};color:white;line-height:24px;margin:auto;text-align:center;font-weight:700">{"✓" if done else i+1}</div></td>')
        labels.append(f'<td width="20%" align="center" valign="top" style="padding:5px 2px 0;font-size:10px;line-height:13px;color:{fg};font-weight:700">{html.escape(step)}</td>')
        bars.append(f'<td width="20%" style="padding:0 1px"><div style="height:6px;background:{bg};border-radius:8px;width:100%"></div></td>')
    return (
        '<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="table-layout:fixed">'
        '<tr>'+''.join(circles)+'</tr>'
        '<tr style="height:8px">'+''.join(bars)+'</tr>'
        '<tr>'+''.join(labels)+'</tr>'
        '</table>'
    )

def app_base_url():
    configured=str(cfg("APP_URL") or "").strip().rstrip("/")
    return configured

def tracking_url(order):
    token=str(order.get("tracking_token") or "").strip()
    base=app_base_url()
    if token and base:
        return f"{base}/?track={token}"
    return ""

def ensure_tracking_token(order_id):
    rows=query("SELECT tracking_token FROM rachna_orders WHERE id=%s",(order_id,))
    if rows and rows[0].get("tracking_token"):
        return str(rows[0]["tracking_token"])
    token=secrets.token_urlsafe(24)
    query("UPDATE rachna_orders SET tracking_token=%s WHERE id=%s",(token,order_id),fetch=False)
    return token

def _invoice_logo_bytes():
    try:
        logo=get_setting('app_logo')
        if not logo: return None
        raw=logo.get('image_data')
        if raw:
            if isinstance(raw,memoryview): raw=raw.tobytes()
            return bytes(raw)
        url=str(logo.get('image_url') or '').strip()
        if url:
            r=requests.get(url,timeout=8)
            if r.ok: return r.content
    except Exception: pass
    return None

def order_items_for_invoice(order_id, fallback_order=None):
    rows=query('SELECT product_name,category,quantity,unit_price,line_total FROM rachna_order_items WHERE order_id=%s ORDER BY id',(order_id,))
    if rows: return rows
    if fallback_order:
        return [{'product_name':fallback_order.get('product_name') or '', 'category':fallback_order.get('category') or '', 'quantity':fallback_order.get('quantity') or 0, 'unit_price':fallback_order.get('unit_price') or 0, 'line_total':fallback_order.get('total_price') or 0}]
    return []

def build_invoice_pdf(order):
    buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=36,leftMargin=36,topMargin=30,bottomMargin=36)
    styles=getSampleStyleSheet(); title=ParagraphStyle('it',parent=styles['Title'],alignment=TA_CENTER,fontSize=20,textColor=colors.HexColor('#071b33')); normal=ParagraphStyle('in',parent=styles['Normal'],fontSize=10,leading=14); right=ParagraphStyle('ir',parent=normal,alignment=TA_RIGHT)
    no=str(order.get('order_number') or order.get('id') or '—'); story=[]
    lb=_invoice_logo_bytes()
    if lb:
        try:
            im=RLImage(io.BytesIO(lb)); im.drawHeight=55; im.drawWidth=min(190,55*(im.imageWidth/max(im.imageHeight,1))); im.hAlign='CENTER'; story += [im,Spacer(1,6)]
        except Exception: pass
    story += [Paragraph(html.escape(email_brand_name()),title),Paragraph('ORDER INVOICE',ParagraphStyle('sub',parent=title,fontSize=14,textColor=colors.HexColor('#b48618'))),Spacer(1,12)]
    meta=Table([[Paragraph(f'<b>Order:</b> {html.escape(no)}',normal),Paragraph(f'<b>Date:</b> {html.escape(str(order.get("created_at") or date.today()))}',right)],[Paragraph(f'<b>Customer:</b> {html.escape(str(order.get("customer_name") or ""))}',normal),Paragraph(f'<b>Email:</b> {html.escape(str(order.get("customer_email") or ""))}',right)]],colWidths=[270,240]); meta.setStyle(TableStyle([('BOX',(0,0),(-1,-1),.5,colors.HexColor('#d6ae52')),('INNERGRID',(0,0),(-1,-1),.25,colors.HexColor('#e5e7eb')),('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#fffaf0')),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)])); story += [meta,Spacer(1,18)]
    rows=[['Product','Category','Qty','Unit Price','Total']]; total_sum=0
    for it in order_items_for_invoice(order.get('id'),order):
        lt=float(it.get('line_total') or 0); total_sum += lt; rows.append([str(it.get('product_name') or ''),str(it.get('category') or ''),str(it.get('quantity') or ''),money(it.get('unit_price')),money(lt)])
    tbl=Table(rows,colWidths=[180,100,45,90,95]); tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#071b33')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#d9dde3')),('ALIGN',(2,1),(-1,-1),'RIGHT'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)])); story += [tbl,Spacer(1,12),Paragraph(f'<b>Grand Total: {html.escape(money(total_sum or order.get("total_price")))}</b>',right),Spacer(1,14)]
    info=Table([['Payment',str(order.get('payment_method') or 'COD')],['Payment status',str(order.get('payment_status') or 'Pending')],['Order status',str(order.get('order_status') or 'Order Placed')],['Delivery date',str(order.get('delivery_date') or '')],['Phone',str(order.get('phone') or '')],['Address',str(order.get('address') or '')]],colWidths=[130,380]); info.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.3,colors.HexColor('#e5e7eb')),('BACKGROUND',(0,0),(0,-1),colors.HexColor('#f5f7fa')),('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)])); story += [info,Spacer(1,20),Paragraph('Thank you for choosing RACHNA PLAYWOOD &amp; HARDWEAR VADGAM.',normal)]
    doc.build(story); return buf.getvalue()

def send_order_email(order, debug=False, event_title="Order Confirmation"):
    # Authenticated SMTP account sends the message; logged-in customer is the primary recipient.
    def log(msg):
        print(f'[RACHNA EMAIL] {msg}', flush=True)
        if debug: st.write(f'📧 {msg}')
    host=cfg('SMTP_HOST'); user=cfg('SMTP_USER', cfg('SMTP_USERNAME', cfg('SMTP_EMAIL'))); pw=cfg('SMTP_PASSWORD')
    customer_email=str(order.get('customer_email') or '').strip()
    admin_email=str(cfg('ADMIN_EMAIL') or cfg('ORDER_EMAIL') or cfg('SMTP_TO') or '').strip()
    from_name=str(cfg('SMTP_FROM_NAME') or email_brand_name()).strip()
    port_raw=cfg('SMTP_PORT','465')
    log('Step 1/7: Reading SMTP secrets and order recipient')
    log(f'SMTP_HOST present: {bool(host)}'); log(f'SMTP_USER/USERNAME/EMAIL present: {bool(user)}'); log(f'SMTP_PASSWORD present: {bool(pw)}')
    log(f'Customer email present: {bool(customer_email)}'); log(f'ADMIN_EMAIL present: {bool(admin_email)}'); log(f'SMTP_PORT: {port_raw}')
    if not host or not user or not pw:
        missing=[]
        if not host: missing.append('SMTP_HOST')
        if not user: missing.append('SMTP_USER')
        if not pw: missing.append('SMTP_PASSWORD')
        msg='Missing SMTP secrets: '+', '.join(missing); log('FAILED: '+msg); return False,msg
    if not customer_email:
        msg="Logged-in user's email is missing. Add an email to the user's account before placing an order."; log('FAILED: '+msg); return False,msg
    try: port=int(port_raw)
    except Exception:
        msg=f'Invalid SMTP_PORT: {port_raw}'; log('FAILED: '+msg); return False,msg
    logo_url=''
    logo_bytes=None
    logo_mime='image/jpeg'
    try:
        logo=get_setting('app_logo')
        if logo:
            logo_url=str(logo.get('image_url') or '').strip()
            logo_bytes=logo.get('image_data') or None
            logo_mime=str(logo.get('mime_type') or 'image/jpeg')
            if logo_url and not logo_bytes:
                try:
                    lr=requests.get(logo_url,timeout=8)
                    if lr.ok:
                        logo_bytes=lr.content
                        logo_mime=lr.headers.get('Content-Type','image/jpeg').split(';')[0]
                except Exception as le:
                    log(f'Logo download warning: {type(le).__name__}: {le}')
    except Exception as e:
        log(f'Logo lookup warning: {type(e).__name__}: {e}')
    logo_html=('<img src="cid:rachna_logo" alt="Rachna Playwood & Hardwear" style="max-height:76px;max-width:240px;display:block;margin:0 auto 12px;object-fit:contain;">' if logo_bytes else (f'<img src="{html.escape(logo_url, quote=True)}" alt="Rachna Playwood & Hardwear" style="max-height:76px;max-width:240px;display:block;margin:0 auto 12px;object-fit:contain;">' if logo_url else '<div style="font-size:28px;font-weight:800;letter-spacing:1px;">RACHNA PLAYWOOD &amp; HARDWEAR</div>'))
    if not order.get('tracking_token'):
        try: order['tracking_token']=ensure_tracking_token(order.get('id'))
        except Exception as te: log(f'Tracking token warning: {type(te).__name__}: {te}')
    live_track=tracking_url(order)
    track_block=(f'<div style="margin-top:18px;text-align:center"><a href="{html.escape(live_track,quote=True)}" style="display:inline-block;background:#16a34a;color:#fff;text-decoration:none;font-weight:800;padding:12px 20px;border-radius:10px">View live order status</a><div style="font-size:11px;color:#777;margin-top:7px">Status changes appear here automatically. This is your live order tracking page.</div></div>' if live_track else '<div style="margin-top:18px;text-align:center;font-size:12px;color:#777">Add APP_URL in Streamlit Secrets to enable live tracking from this email.</div>')
    customer=html.escape(str(order.get('customer_name') or '')); phone=html.escape(str(order.get('phone') or '')); address=html.escape(str(order.get('address') or '—')); delivery=html.escape(str(order.get('delivery_date') or '')); category=html.escape(str(order.get('category') or '')); product_name=html.escape(str(order.get('product_name') or '')); quantity=html.escape(str(order.get('quantity') or '')); unit_price=html.escape(money(order.get('unit_price'))); total=html.escape(money(order.get('total_price')))
    is_status_update=event_title.lower().startswith('order status')
    notice_title='Order status updated' if is_status_update else 'Order received'
    notice_text=f"Your order status is now <b>{html.escape(str(order.get('order_status') or 'Order Placed'))}</b>." if is_status_update else 'Your order has been successfully placed.'
    html_body=f'''<!doctype html><html><body style="margin:0;padding:0;background:#f3f0e8;font-family:Arial,Helvetica,sans-serif;color:#172033;"><table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:#f3f0e8;padding:24px 8px;"><tr><td align="center"><table width="620" cellpadding="0" cellspacing="0" role="presentation" style="max-width:620px;width:100%;background:#fff;border-radius:18px;overflow:hidden;"><tr><td style="background:#071b33;padding:28px 22px;text-align:center;border-bottom:4px solid #d6ae52;">{logo_html}<div style="color:#d6ae52;font-size:13px;letter-spacing:3px;text-transform:uppercase;font-weight:800;">{html.escape(email_brand_name())}</div><div style="color:#d6ae52;font-size:12px;letter-spacing:3px;text-transform:uppercase;font-weight:700;margin-top:7px;">{html.escape(event_title.upper())}</div><div style="color:#fff;font-size:24px;font-weight:700;margin-top:8px;">Thank you, {customer}!</div></td></tr><tr><td style="padding:26px 24px;"><div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:14px;padding:16px 18px;margin-bottom:18px;"><div style="font-weight:800;color:#071b33;margin-bottom:10px;">ORDER TRACKING</div>{tracking_html(str(order.get("order_status") or "Order Placed"))}</div><div style="background:#fffaf0;border:1px solid #ead7a0;border-radius:14px;padding:16px 18px;margin-bottom:18px;"><div style="font-size:12px;color:#8a6a25;text-transform:uppercase;letter-spacing:1px;font-weight:700;">{notice_title}</div><div style="font-size:16px;font-weight:700;color:#071b33;margin-top:5px;">{notice_text}</div></div><table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="border-collapse:collapse;"><tr><td style="padding:11px 8px;border-bottom:1px solid #eee;color:#777;">Product</td><td align="right" style="padding:11px 8px;border-bottom:1px solid #eee;font-weight:700;">{product_name}</td></tr><tr><td style="padding:11px 8px;border-bottom:1px solid #eee;color:#777;">Category</td><td align="right" style="padding:11px 8px;border-bottom:1px solid #eee;">{category}</td></tr><tr><td style="padding:11px 8px;border-bottom:1px solid #eee;color:#777;">Quantity</td><td align="right" style="padding:11px 8px;border-bottom:1px solid #eee;">{quantity}</td></tr><tr><td style="padding:11px 8px;border-bottom:1px solid #eee;color:#777;">Unit price</td><td align="right" style="padding:11px 8px;border-bottom:1px solid #eee;">{unit_price}</td></tr><tr><td style="padding:14px 8px;color:#071b33;font-size:17px;font-weight:800;">Total</td><td align="right" style="padding:14px 8px;color:#b48618;font-size:20px;font-weight:800;">{total}</td></tr></table><div style="margin-top:14px;padding:14px;background:#fffaf0;border:1px solid #ead7a0;border-radius:12px;"><b>Payment:</b> {html.escape(str(order.get("payment_method") or "COD"))} · {html.escape(str(order.get("payment_status") or "Pending"))}</div><div style="margin-top:20px;padding:16px;background:#f7f7f7;border-radius:12px;"><div style="font-weight:800;color:#071b33;margin-bottom:8px;">Delivery details</div><div style="font-size:14px;line-height:1.7;color:#555;"><b>Phone:</b> {phone}<br><b>Delivery date:</b> {delivery}<br><b>Address:</b> {address}</div></div>{track_block}</td></tr><tr><td style="background:#071b33;padding:18px 20px;text-align:center;color:#d8d8d8;font-size:12px;line-height:1.6;"><b style="color:#d6ae52;">{html.escape(email_brand_name())}</b><br>Crafted for your space · Premium quality</td></tr></table></td></tr></table></body></html>'''
    text_body=(f"RACHNA PLAYWOOD & HARDWEAR - {event_title}\n\nThank you, {order.get('customer_name') or ''}!\n\nCurrent status: {order.get('order_status') or 'Order Placed'}\n\nProduct: {order.get('product_name') or ''}\nCategory: {order.get('category') or ''}\nQuantity: {order.get('quantity') or ''}\nUnit price: {money(order.get('unit_price'))}\nTotal: {money(order.get('total_price'))}\n\nPhone: {order.get('phone') or ''}\nDelivery date: {order.get('delivery_date') or ''}\nAddress: {order.get('address') or ''}\n\nLive tracking: {live_track or 'Set APP_URL in Streamlit Secrets to enable it.'}\n")
    email_msg=EmailMessage(); email_msg['Subject']=f"Rachna Order #{order.get('order_number') or order.get('id') or ''} — {event_title}"; email_msg['From']=f'{from_name} <{user}>'; email_msg['To']=customer_email
    if admin_email and admin_email.lower()!=customer_email.lower(): email_msg['Cc']=admin_email
    email_msg.set_content(text_body)
    email_msg.add_alternative(html_body,subtype='html')
    try: email_msg.add_attachment(build_invoice_pdf(order),maintype='application',subtype='pdf',filename=f"Rachna_Invoice_{order.get('order_number') or order.get('id')}.pdf")
    except Exception as e: log(f'Invoice PDF warning: {type(e).__name__}: {e}')
    if logo_bytes:
        maintype, subtype = logo_mime.split('/',1) if '/' in logo_mime else ('image','jpeg')
        email_msg.get_payload()[1].add_related(logo_bytes, maintype=maintype, subtype=subtype, cid='<rachna_logo>', filename='rachna-logo')
    recipients=[customer_email]+([admin_email] if admin_email and admin_email.lower()!=customer_email.lower() else [])
    try:
        if port==465:
            log('Step 2/7: Connecting using SMTP SSL on port 465')
            with smtplib.SMTP_SSL(host,port,context=ssl.create_default_context(),timeout=15) as smtp:
                log('Step 3/7: SMTP SSL connection successful'); log('Step 4/7: Logging in to SMTP server'); smtp.login(user,pw); log('Step 5/7: SMTP login successful'); smtp.send_message(email_msg,to_addrs=recipients); log(f'Step 6/7: Email accepted for {len(recipients)} recipient(s)')
        else:
            log(f'Step 2/7: Connecting using SMTP on port {port}')
            with smtplib.SMTP(host,port,timeout=15) as smtp:
                log('Step 3/7: SMTP connection successful'); log('Step 4/7: Starting TLS'); smtp.ehlo(); smtp.starttls(context=ssl.create_default_context()); smtp.ehlo(); log('TLS successful; logging in'); smtp.login(user,pw); log('Step 5/7: SMTP login successful'); smtp.send_message(email_msg,to_addrs=recipients); log(f'Step 6/7: Email accepted for {len(recipients)} recipient(s)')
        log('Step 7/7: Order email process completed'); log_email_message(customer_email, admin_email if admin_email and admin_email.lower()!=customer_email.lower() else '', email_msg.get('Subject') or '', text_body, html_body, 'Order', related_order_id=order.get('id'), status='Sent', sender_email=user, sender_name=from_name); return True,'Order confirmation email accepted by SMTP server'
    except smtplib.SMTPAuthenticationError as e:
        msg=f'SMTP authentication failed. Check Gmail App Password/username. SMTP code={getattr(e,"smtp_code","?")}'; log('FAILED: '+msg); return False,msg
    except smtplib.SMTPConnectError as e:
        msg=f'SMTP connection failed: {e}'; log('FAILED: '+msg); return False,msg
    except smtplib.SMTPException as e:
        msg=f'SMTP error: {e}'; log('FAILED: '+msg); return False,msg
    except Exception as e:
        msg=f'Email error: {type(e).__name__}: {e}'; log('FAILED: '+msg); return False,msg


def send_order_status_email(order):
    return send_order_email(order,debug=False)


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


def _complete_pin_setup(user_id):
    user = find_user_by_id(user_id)
    if not user:
        st.session_state.pop("pin_setup_user_id", None)
        return
    st.markdown("""
    <div style="max-width:520px;margin:1.5rem auto;padding:26px;border:2px solid #d6ae52;
         border-radius:22px;background:linear-gradient(145deg,#071b33,#102c50);text-align:center;
         box-shadow:0 18px 50px rgba(0,0,0,.28)">
      <div style="font-size:36px">🔐</div>
      <h2 style="margin:4px 0;color:#d6ae52!important">Set your 4-digit PIN</h2>
      <p style="color:#dbe4ef;margin:0">Your email is verified. Create a PIN for future sign in.</p>
    </div>""", unsafe_allow_html=True)
    with st.form("mandatory_pin_setup"):
        pin1 = st.text_input("4-digit PIN", type="password", max_chars=4, placeholder="••••")
        pin2 = st.text_input("Confirm PIN", type="password", max_chars=4, placeholder="••••")
        save_pin = st.form_submit_button("Save PIN & Continue", type="primary", use_container_width=True)
    if save_pin:
        if not (pin1.isdigit() and len(pin1) == 4):
            st.error("PIN must contain exactly 4 digits."); return
        if pin1 != pin2:
            st.error("PIN and Confirm PIN do not match."); return
        query("UPDATE rachna_users SET password_hash=%s,updated_at=NOW() WHERE id=%s", (password_hash(pin1), user_id), fetch=False)
        st.session_state.user_id = int(user_id); st.session_state.admin = False; st.session_state.page = "Home"
        st.session_state.pop("pin_setup_user_id", None)
        st.success("PIN saved. Welcome to Rachna!"); st.rerun()


def login_page():
    pin_user = st.session_state.get("pin_setup_user_id")
    if pin_user:
        _complete_pin_setup(int(pin_user)); return
    page_header("WELCOME", "Sign in to Rachna", "Email + 4-digit PIN")
    tabs = st.tabs(["Sign in", "Create account"])
    with tabs[0]:
        with st.form("login"):
            uid = st.text_input("Email / Phone")
            pin = st.text_input("4-digit PIN / existing password", type="password", max_chars=64)
            submit = st.form_submit_button("Sign in", type="primary", use_container_width=True)
        if submit:
            if password_ok(uid, pin):
                st.session_state.admin=True; st.session_state.user_id=None; st.session_state.page="Home"; st.session_state._consumed_page_qp="Home"; st.rerun()
            else:
                rows=query("SELECT id,password_hash,is_admin,email_verified FROM rachna_users WHERE (email=%s OR phone=%s) AND active=TRUE LIMIT 1", (uid.strip().lower(),uid.strip()))
                if not rows: st.error("Account not found. Please create an account first.")
                elif not bool(rows[0].get("email_verified")): st.warning("Your email is not verified. Please register again.")
                elif len(pin)!=4 or not pin.isdigit() or not rows[0].get("password_hash"): st.error("Enter your 4-digit PIN.")
                elif hmac.compare_digest(password_hash(pin),str(rows[0]["password_hash"])):
                    st.session_state.user_id=int(rows[0]["id"]); st.session_state.admin=bool(rows[0].get("is_admin")); st.session_state.page="Home"; st.session_state._consumed_page_qp="Home"; st.rerun()
                else: st.error("Incorrect email/phone or PIN.")
    with tabs[1]:
        pending=st.session_state.get("registration_pending")
        if not pending:
            with st.form("signup_start",clear_on_submit=False):
                name=st.text_input("Name *"); email=st.text_input("Email *"); phone=st.text_input("Phone *")
                start=st.form_submit_button("Send 6-digit OTP",type="primary",use_container_width=True)
            if start:
                name=name.strip(); email=email.strip().lower(); phone=phone.strip()
                if not name or not email or not phone: st.error("Name, email and phone are required.")
                elif "@" not in email: st.error("Enter a valid email address.")
                elif query("SELECT id FROM rachna_users WHERE lower(email)=lower(%s) OR phone=%s LIMIT 1",(email,phone)):
                    st.error("This email or phone is already registered. Please sign in.")
                else:
                    otp=make_otp(); ok,msg=send_registration_otp(email,name,otp)
                    if ok:
                        st.session_state.registration_pending={"name":name,"email":email,"phone":phone,"otp_hash":password_hash(otp),"otp_expires_at":(datetime.now()+timedelta(minutes=5)).isoformat(),"otp_attempts":0}
                        st.success("6-digit OTP sent to your email."); st.rerun()
                    else: st.error(msg)
        else:
            st.markdown(f"<div class='profile-card'><h3>Verify your email</h3><p>OTP sent to <b>{html.escape(pending['email'])}</b></p></div>",unsafe_allow_html=True)
            with st.form("signup_verify",clear_on_submit=False):
                otp_entered=st.text_input("6-digit OTP",max_chars=6,placeholder="123456")
                verify=st.form_submit_button("Verify OTP & Create Account",type="primary",use_container_width=True)
            a,b=st.columns(2)
            with a:
                if st.button("Resend OTP",use_container_width=True):
                    if pending.get("otp_attempts",0)>=5: st.error("Too many OTP attempts. Please cancel and restart registration.")
                    else:
                        otp=make_otp(); ok,msg=send_registration_otp(pending["email"],pending["name"],otp)
                        if ok:
                            pending["otp_hash"]=password_hash(otp); pending["otp_expires_at"]=(datetime.now()+timedelta(minutes=5)).isoformat(); pending["otp_attempts"]=0
                            st.session_state.registration_pending=pending; st.success("New OTP sent."); st.rerun()
                        else: st.error(msg)
            with b:
                if st.button("Cancel",use_container_width=True): st.session_state.pop("registration_pending",None); st.rerun()
            if verify:
                if not otp_entered.isdigit() or len(otp_entered)!=6: st.error("Enter the 6-digit OTP.")
                else:
                    try: expiry=datetime.fromisoformat(pending["otp_expires_at"])
                    except Exception: expiry=datetime.min
                    if datetime.now()>expiry: st.error("OTP expired. Please resend OTP.")
                    elif pending.get("otp_attempts",0)>=5: st.error("Too many OTP attempts. Please cancel and restart registration.")
                    elif not hmac.compare_digest(password_hash(otp_entered),pending["otp_hash"]):
                        pending["otp_attempts"]=int(pending.get("otp_attempts",0))+1; st.session_state.registration_pending=pending; st.error("Incorrect OTP.")
                    else:
                        try:
                            # Final safety net: guarantee the auth migration before INSERT.
                            ensure_auth_schema()
                            row=query("INSERT INTO rachna_users(name,phone,email,password_hash,email_verified,updated_at) VALUES(%s,%s,%s,%s,TRUE,NOW()) RETURNING id",(pending["name"],pending["phone"],pending["email"],""))[0]
                            st.session_state.pop("registration_pending",None); st.session_state.pin_setup_user_id=int(row["id"]); st.success("Email verified and account created. Set your 4-digit PIN below."); st.rerun()
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
    page_header("COLLECTION","Rachna Collections" if master else "Collections","Admin product management" if master else "Browse furniture, plywood and hardware products.")
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
                if not master and st.session_state.get('user_id'):
                    if st.button('＋ Add to Bag',key=f'bag_add_{p["id"]}',use_container_width=True):
                        add_to_bag(p,1); st.success(f'{p["title"]} added to Your Bag.')
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
        page_header("MY SPACE","My Space","Profile, attendance and personal details")
        if not user:
            st.info("Please sign in first.")
            if st.button("Go to Login",type="primary"): st.session_state.page="Login"; st.rerun()
            return
        dp=user.get('dp_url') or ''
        if dp: st.markdown(f"<img class='dp' src='{html.escape(dp,quote=True)}'>",unsafe_allow_html=True)
        else: st.markdown("<div class='profile-card'>👤</div>",unsafe_allow_html=True)
        st.markdown(f"<div class='profile-card'><h2>{html.escape(user['name'])}</h2><div>{html.escape(user['email'])} · {html.escape(user['phone'])}</div></div>",unsafe_allow_html=True)
        tabs=st.tabs(["Profile","Attendance","Order History"])
        with tabs[0]:
            with st.form("profile_edit"):
                st.text_input("Name",user['name'],disabled=True); st.text_input("Phone",user['phone'],disabled=True); st.text_input("Email",user['email'],disabled=True); age=st.number_input("Age",1,120,int(user.get('age') or 18)); address=st.text_area("Address",user.get('address') or ''); pin=st.text_input("Pincode",value=user.get('pincode') or '',max_chars=6); new_dp=st.file_uploader("Change DP",type=['jpg','jpeg','png','webp']); save=st.form_submit_button("Save profile",type='primary')
            if save:
                auto=lookup_pincode(pin) if pin else ''
                final_addr=auto if auto and not address.strip() else address.strip()
                query("UPDATE rachna_users SET age=%s,address=%s,pincode=%s,updated_at=NOW() WHERE id=%s",(int(age),final_addr,pin.strip(),user['id']),fetch=False)
                if new_dp: save_user_dp(new_dp,user['id'])
                current_user_by_id.clear()
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
        with tabs[2]:
            user_order_history()
        return
    if not st.session_state.get('admin'):
        st.warning('Admin login required.'); return
    page_header("ACCOUNT CENTER","Account Center","Admin-only staff, attendance and ledger controls")
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
    query("CREATE TABLE IF NOT EXISTS rachna_orders(id BIGSERIAL PRIMARY KEY,user_id BIGINT REFERENCES rachna_users(id) ON DELETE SET NULL,customer_name TEXT NOT NULL,phone TEXT NOT NULL,address TEXT,delivery_date DATE NOT NULL,product_id BIGINT REFERENCES rachna_products(id) ON DELETE SET NULL,category TEXT,product_name TEXT NOT NULL,quantity NUMERIC(12,2) NOT NULL CHECK(quantity>0),unit_price NUMERIC(12,2),total_price NUMERIC(12,2),created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),order_number TEXT,customer_email TEXT,payment_method TEXT DEFAULT 'COD',payment_status TEXT DEFAULT 'Pending',order_status TEXT DEFAULT 'Order Placed',updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),tracking_token TEXT)",fetch=False)
    query("ALTER TABLE rachna_orders ADD COLUMN IF NOT EXISTS tracking_token TEXT",fetch=False)
    query("CREATE UNIQUE INDEX IF NOT EXISTS uq_rachna_order_tracking_token ON rachna_orders(tracking_token) WHERE tracking_token IS NOT NULL",fetch=False)
    query("CREATE TABLE IF NOT EXISTS rachna_order_status_history(id BIGSERIAL PRIMARY KEY,order_id BIGINT NOT NULL REFERENCES rachna_orders(id) ON DELETE CASCADE,status TEXT NOT NULL,note TEXT,changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW())",fetch=False)
    query("CREATE TABLE IF NOT EXISTS rachna_order_items(id BIGSERIAL PRIMARY KEY,order_id BIGINT NOT NULL REFERENCES rachna_orders(id) ON DELETE CASCADE,product_id BIGINT REFERENCES rachna_products(id) ON DELETE SET NULL,product_name TEXT NOT NULL,category TEXT,quantity NUMERIC(12,2) NOT NULL CHECK(quantity>0),unit_price NUMERIC(12,2),line_total NUMERIC(12,2),created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())",fetch=False)

def user_order_history():
    u=current_user(); page_header('ORDER HISTORY','Order History','Track every order and download your invoice')
    if not u: st.info('Please login first.'); return
    rows=query('SELECT * FROM rachna_orders WHERE user_id=%s ORDER BY created_at DESC',(u['id'],))
    if not rows: st.info('No orders yet.'); return
    for r in rows:
        with st.container(border=True):
            no=r.get('order_number') or r['id']
            st.markdown(f"**#{no}** · {html.escape(str(r['product_name']))} · **{money(r.get('total_price'))}**")
            st.caption(f"Status: {r.get('order_status') or 'Order Placed'} · Payment: {r.get('payment_method') or 'COD'} / {r.get('payment_status') or 'Pending'}")
            st.markdown(tracking_html(str(r.get('order_status') or 'Order Placed')),unsafe_allow_html=True)
            for h in query('SELECT status,note,changed_at FROM rachna_order_status_history WHERE order_id=%s ORDER BY changed_at',(r['id'],)):
                st.caption(f"✓ {h['status']} · {h['changed_at']} · {h.get('note') or ''}")
            c1,c2=st.columns(2)
            with c1:
                st.download_button('⬇ Download Invoice PDF',data=build_invoice_pdf(dict(r)),file_name=f'Rachna_Invoice_{no}.pdf',mime='application/pdf',key=f'uhpdf_{r["id"]}')
            with c2:
                if st.button('🗑 Delete this order',key=f'uhdel_{r["id"]}'):
                    query('DELETE FROM rachna_orders WHERE id=%s AND user_id=%s',(r['id'],u['id']),fetch=False)
                    st.success('Order deleted from your Order History.')
                    st.rerun()


def admin_orders_page():
    if not st.session_state.get('admin'): st.warning('Admin login required.'); return
    page_header('ORDER HISTORY','Order History','Admin order management · live tracking · delete controls')
    rows=query('SELECT * FROM rachna_orders ORDER BY created_at DESC LIMIT 1000')
    if not rows: st.info('No orders found.'); return
    statuses=order_status_steps()
    for r in rows:
        no=r.get('order_number') or str(r['id'])
        with st.expander(f"#{no} · {r.get('customer_name')} · {r.get('product_name')} · {money(r.get('total_price'))}"):
            st.markdown(tracking_html(str(r.get('order_status') or 'Order Placed')),unsafe_allow_html=True)
            st.write(f"Customer: {r.get('customer_name')} · Email: {r.get('customer_email')} · Phone: {r.get('phone')}")
            st.write(f"Product: {r.get('product_name')} · Qty: {r.get('quantity')} · Total: {money(r.get('total_price'))}")
            st.write(f"Payment: {r.get('payment_method')} · Payment status: {r.get('payment_status')} · Delivery: {r.get('delivery_date')}")
            cur=str(r.get('order_status') or 'Order Placed'); ns=st.selectbox('Order status',statuses,index=status_index(cur),key=f'os_{r["id"]}')
            opts=['Pending','Paid','Failed','Refunded']; cps=str(r.get('payment_status') or 'Pending'); ps=st.selectbox('Payment status',opts,index=opts.index(cps) if cps in opts else 0,key=f'ps_{r["id"]}')
            note=st.text_input('Tracking note',key=f'on_{r["id"]}')
            c1,c2=st.columns(2)
            with c1:
                if st.button('Save status update',type='primary',key=f'order_save_{r["id"]}'):
                    status_changed = ns != cur
                    payment_changed = ps != cps
                    query('UPDATE rachna_orders SET order_status=%s,payment_status=%s,updated_at=NOW() WHERE id=%s',(ns,ps,r['id']),fetch=False)
                    if status_changed or payment_changed or note.strip():
                        query('INSERT INTO rachna_order_status_history(order_id,status,note) VALUES(%s,%s,%s)',(r['id'],ns,note.strip()),fetch=False)
                    # No second email on status updates. The original confirmation email
                    # contains a live tracking link, so it always shows the latest status.
                    if status_changed or payment_changed:
                        st.success(f"Status updated to {ns}. No new email sent; the original email's live tracking link now shows the updated status.")
                    else:
                        st.success('Order details saved.')
                    st.rerun()
            with c2:
                if st.button('🗑 Delete order',key=f'order_del_{r["id"]}'):
                    query('DELETE FROM rachna_orders WHERE id=%s',(r['id'],),fetch=False)
                    st.success(f'Order #{no} deleted.')
                    st.rerun()
            st.download_button('⬇ Download Invoice PDF',data=build_invoice_pdf(dict(r)),file_name=f'Rachna_Invoice_{no}.pdf',mime='application/pdf',key=f'ahpdf_{r["id"]}')


def public_track_page():
    page_header('TRACK ORDER','Track Order','Track your orders live from one place.')
    token=str(st.query_params.get('track') or '').strip()
    if not token:
        st.info('Tracking link is missing or invalid.')
        return
    rows=query('SELECT * FROM rachna_orders WHERE tracking_token=%s LIMIT 1',(token,))
    if not rows:
        st.error('This tracking link is invalid or the order has been deleted.')
        return
    r=rows[0]
    st.markdown(f"<div class='hero'><h2>Order #{html.escape(str(r.get('order_number') or r['id']))}</h2><p>{html.escape(str(r.get('product_name') or ''))} · {money(r.get('total_price'))}</p></div>",unsafe_allow_html=True)
    st.markdown(tracking_html(str(r.get('order_status') or 'Order Placed')),unsafe_allow_html=True)
    st.success(f"Current status: {r.get('order_status') or 'Order Placed'}")
    st.write(f"Customer: {r.get('customer_name') or ''}")
    st.write(f"Delivery date: {r.get('delivery_date') or ''}")
    history=query('SELECT status,note,changed_at FROM rachna_order_status_history WHERE order_id=%s ORDER BY changed_at',(r['id'],))
    if history:
        st.subheader('Tracking history')
        for h in history:
            st.markdown(f"**✓ {html.escape(str(h['status']))}** · {html.escape(str(h['changed_at']))}  \n{html.escape(str(h.get('note') or ''))}")
    st.download_button('⬇ Download Invoice PDF',data=build_invoice_pdf(dict(r)),file_name=f"Rachna_Invoice_{r.get('order_number') or r['id']}.pdf",mime='application/pdf',key=f'trackpdf_{r["id"]}')

def user_track_order_page():
    """Logged-in user's live order tracker. Latest order is shown first, followed by older orders."""
    user=current_user()
    page_header('TRACK ORDER','Track Order','Your latest order, live status and order summary')
    if not user:
        st.info('Please login first.')
        return
    rows=query('SELECT * FROM rachna_orders WHERE user_id=%s ORDER BY created_at DESC LIMIT 100',(user['id'],))
    if not rows:
        st.info('You have not placed any orders yet.')
        if st.button('Start a New Order',type='primary'):
            st.session_state.page='Order'; st.rerun()
        return

    latest=rows[0]
    latest_status=str(latest.get('order_status') or 'Order Placed')
    no=str(latest.get('order_number') or latest.get('id') or '')
    # Compact order card first, as requested.
    st.markdown(f"""<div style='background:#102c50;border:1px solid #d6ae52;border-radius:14px;padding:12px 15px;margin-bottom:12px'>
      <div style='font-size:11px;color:#d6ae52;font-weight:800;letter-spacing:1.4px'>LATEST ORDER</div>
      <div style='display:flex;justify-content:space-between;gap:10px;align-items:center;margin-top:4px'>
        <div><b style='color:#fff'>#{html.escape(no)}</b><div style='font-size:12px;color:#cbd5e1'>{html.escape(str(latest.get('product_name') or ''))} · Qty {html.escape(str(latest.get('quantity') or ''))}</div></div>
        <div style='text-align:right;color:#d6ae52;font-weight:800'>{html.escape(money(latest.get('total_price')))}</div>
      </div></div>""",unsafe_allow_html=True)

    # Status immediately below the compact order card.
    st.markdown("<div style='font-size:13px;color:#d6ae52;font-weight:800;letter-spacing:1.2px;margin:8px 0'>ORDER STATUS</div>",unsafe_allow_html=True)
    st.markdown(tracking_html(latest_status),unsafe_allow_html=True)
    st.success(f'Current status: {latest_status}')

    # Order summary below status.
    st.markdown("<div style='font-size:13px;color:#d6ae52;font-weight:800;letter-spacing:1.2px;margin:16px 0 8px'>ORDER SUMMARY</div>",unsafe_allow_html=True)
    summary_rows=[
        ('Product',latest.get('product_name') or '—'),
        ('Category',latest.get('category') or '—'),
        ('Quantity',latest.get('quantity') or '—'),
        ('Payment',f"{latest.get('payment_method') or 'COD'} · {latest.get('payment_status') or 'Pending'}"),
        ('Delivery date',latest.get('delivery_date') or '—'),
        ('Total',money(latest.get('total_price'))),
    ]
    st.markdown("<div style='background:#fff;border-radius:14px;padding:4px 14px;color:#172033'>" + ''.join(f"<div style='display:flex;justify-content:space-between;gap:12px;padding:9px 0;border-bottom:1px solid #eee'><span style='color:#777'>{html.escape(str(k))}</span><b style='text-align:right'>{html.escape(str(v))}</b></div>" for k,v in summary_rows) + "</div>",unsafe_allow_html=True)
    st.download_button('⬇ Download Invoice PDF',data=build_invoice_pdf(dict(latest)),file_name=f'Rachna_Invoice_{no}.pdf',mime='application/pdf',key=f'user_track_pdf_{latest["id"]}')

    if len(rows)>1:
        st.markdown("<div style='font-size:13px;color:#d6ae52;font-weight:800;letter-spacing:1.2px;margin:18px 0 8px'>PREVIOUS ORDERS</div>",unsafe_allow_html=True)
        for r in rows[1:]:
            rn=str(r.get('order_number') or r.get('id') or '')
            with st.expander(f"#{rn} · {r.get('product_name') or ''} · {money(r.get('total_price'))}"):
                st.markdown(tracking_html(str(r.get('order_status') or 'Order Placed')),unsafe_allow_html=True)
                st.caption(f"Status: {r.get('order_status') or 'Order Placed'} · Delivery: {r.get('delivery_date') or '—'}")
                st.write(f"Quantity: {r.get('quantity') or '—'} · Payment: {r.get('payment_method') or 'COD'}")
                st.download_button('⬇ Invoice',data=build_invoice_pdf(dict(r)),file_name=f'Rachna_Invoice_{rn}.pdf',mime='application/pdf',key=f'user_prev_pdf_{r["id"]}')


def init_cart():
    if 'bag' not in st.session_state: st.session_state.bag={}

def add_to_bag(product, qty=1):
    init_cart(); pid=int(product['id']); old=st.session_state.bag.get(pid,{})
    st.session_state.bag[pid]={'product_id':pid,'title':product.get('title'),'category':product.get('category'),'price':float(product.get('price') or 0),'quantity':float(old.get('quantity',0))+float(qty)}

def bag_items():
    init_cart(); return list(st.session_state.bag.values())

def bag_total(): return sum(float(x['price'])*float(x['quantity']) for x in bag_items())

def your_bag_page():
    page_header('YOUR BAG','Your Bag','Add multiple products and place one combined order')
    init_cart(); items=bag_items()
    if not items: st.info('Your bag is empty. Open Collections and add products.'); return
    for item in items:
        c1,c2,c3,c4=st.columns([3,1,1,1]); c1.write(f"**{item['title']}**"); c1.caption(str(item.get('category') or ''))
        q=c2.number_input('Qty',min_value=1.0,value=float(item['quantity']),step=1.0,key=f"bag_qty_{item['product_id']}"); st.session_state.bag[int(item['product_id'])]['quantity']=float(q)
        c3.write(f"₹{item['price']:,.2f}"); c4.write(f"**₹{item['price']*q:,.2f}**")
        if c4.button('Remove',key=f"bag_remove_{item['product_id']}"): st.session_state.bag.pop(int(item['product_id']),None); st.rerun()
    total=bag_total(); st.markdown(f"<div class='hero'><h2>₹{total:,.2f}</h2><p>{len(st.session_state.bag)} products · one combined order</p></div>",unsafe_allow_html=True)
    if st.button('Proceed to Checkout',type='primary',use_container_width=True): st.session_state.page='Order'; st.rerun()

def order_page():
    page_header('NEW ORDER','New Order','Checkout your Your Bag')
    user=current_user();
    if not user: st.warning('Please login first.'); return
    init_cart(); items=bag_items()
    if not items: st.info('Your Bag is empty. Add products from Collections first.'); return
    total=bag_total()
    for x in items: st.write(f"**{x['title']}** × {x['quantity']:g} — ₹{x['price']*x['quantity']:,.2f}")
    with st.form('order_form'):
        name=st.text_input('Customer name',value=user['name']); phone=st.text_input('Phone',value=user['phone']); address=st.text_area('Delivery address',value=user.get('address') or ''); delivery=st.date_input('Delivery date',value=date.today()+timedelta(days=2),min_value=date.today()+timedelta(days=2)); payment=st.radio('Payment method',['COD','UPI','Credit / Debit Card','Online Payment'],horizontal=True); submit=st.form_submit_button(f'Place Order · ₹{total:,.2f}',type='primary',use_container_width=True)
    if submit:
        if not name.strip() or not phone.strip() or not address.strip(): st.error('Name, phone and delivery address are required.'); return
        ensure_orders_table(); no='RCH'+datetime.now().strftime('%Y%m%d%H%M%S')+str(user['id']).zfill(3); token=secrets.token_urlsafe(24); first=items[0]
        row=query('''INSERT INTO rachna_orders(user_id,customer_name,phone,address,delivery_date,product_id,category,product_name,quantity,unit_price,total_price,order_number,customer_email,payment_method,payment_status,order_status,updated_at,tracking_token) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),%s) RETURNING *''',(user['id'],name.strip(),phone.strip(),address.strip(),delivery,first['product_id'],first.get('category'),first['title'],first['quantity'],first['price'],total,no,str(user.get('email') or '').strip(),payment,'Pending','Order Placed',token))[0]
        for x in items: query('INSERT INTO rachna_order_items(order_id,product_id,product_name,category,quantity,unit_price,line_total) VALUES(%s,%s,%s,%s,%s,%s,%s)',(row['id'],x['product_id'],x['title'],x.get('category'),x['quantity'],x['price'],float(x['price'])*float(x['quantity'])),fetch=False)
        query('INSERT INTO rachna_order_status_history(order_id,status,note) VALUES(%s,%s,%s)',(row['id'],'Order Placed','Order created by customer'),fetch=False)
        ok,msg=send_order_email(dict(row),event_title='Order Placed'); st.session_state.bag={}; st.success(f"Order #{no} placed successfully. "+('Confirmation + invoice sent to your email.' if ok else ''))
        if not ok: st.warning('Email failed: '+msg)
        st.download_button('⬇ Download Invoice PDF',data=build_invoice_pdf(dict(row)),file_name=f'Rachna_Invoice_{no}.pdf',mime='application/pdf',key=f'newpdf_{row["id"]}')


@st.cache_resource(show_spinner=False)
def init_db_cached():
    # All schema work runs once per Streamlit server process. Running ALTER TABLE
    # on every widget interaction was a major source of slow page loads.
    init_db()
    ensure_auth_schema()
    return True


NAV_LABELS = {
    'Home':'Rachna Hub',
    'Gallery':'Collections',
    'Order':'New Order',
    'Account':'My Space',
    'Order History':'Order History',
    'Order Details':'Order History',
    'Emails':'Communications',
    'About':'About Rachna',
    'Contact Us':'Get In Touch',
    'Master Gallery':'Rachna Collections',
    'Master Account':'Account Center',
    'Admin Master':'Admin Console',
    'Track Order':'Track Order',
    'Your Bag':'Your Bag',
    'Login':'Login',
}

def nav_label(page):
    return NAV_LABELS.get(page, page)

def main():
    try:
        init_db_cached()
    except Exception as e:
        st.error('PostgreSQL connection or table setup failed.'); st.code(str(e)); st.stop()
    if 'admin' not in st.session_state: st.session_state.admin=False
    if 'user_id' not in st.session_state: st.session_state.user_id=None
    if 'page' not in st.session_state: st.session_state.page='Login'
    track_q=str(st.query_params.get('track') or '').strip()
    if track_q:
        st.session_state.page='Track Order'
    # Sidebar visibility is controlled by Streamlit's native, accessible hamburger toggle.
    if st.session_state.user_id and not st.session_state.admin:
        u=current_user(); dp=u.get('dp_url') if u else ''
        icon=(f"<img src='{html.escape(dp,quote=True)}' style='width:44px;height:44px;border-radius:50%;object-fit:cover;border:2px solid #d6ae52'>" if dp else "<div style='width:44px;height:44px;border-radius:50%;background:#071b33;border:2px solid #d6ae52;display:flex;align-items:center;justify-content:center;font-size:22px'>👤</div>")
        st.markdown(f"<a href='?page=Account' title='Open profile' style='position:fixed;top:.55rem;right:.75rem;z-index:999999;text-decoration:none'>{icon}</a>",unsafe_allow_html=True)
    qp=st.query_params.get('page')
    valid_pages={'Home','Gallery','Order','Order History','Account','Order Details','Track Order','Your Bag','About','Contact Us','Master Gallery','Master Account','Admin Master','Emails','Login'}
    # Consume a page deep-link only once. Previously ?page=Account stayed in
    # the browser URL, so every sidebar click was immediately forced back to
    # Account on the next Streamlit rerun.
    if qp in valid_pages and qp != st.session_state.get('_consumed_page_qp'):
        st.session_state.page=qp
        st.session_state._consumed_page_qp=qp
    # Keep the sidebar usable while replacing its visible Streamlit header control with the custom button.
    with st.sidebar:
        logo=get_setting('app_logo')
        if logo and image_row_source(logo): st.image(image_row_source(logo),use_container_width=True)
        st.markdown('<div style="text-align:center;color:#d6ae52;font-weight:800">RACHNA PLAYWOOD & HARDWARE</div>',unsafe_allow_html=True)
        st.divider()
        if st.session_state.admin:
            nav=['Home','Gallery','Order','Your Bag','Track Order','Account','Order Details','Emails','About','Contact Us','Master Gallery','Master Account','Admin Master']
        elif st.session_state.user_id:
            nav=['Home','Gallery','Order','Your Bag','Track Order','Order History','Account','About','Contact Us']
        else:
            nav=['Login']
        if st.session_state.user_id and not st.session_state.admin:
            visible=public_page_names(); nav=[x for x in nav if x in visible or x in ('Login','Track Order','Order History')]
        for p in nav:
            label=nav_label(p)
            if st.button(label,key='nav_'+p,use_container_width=True,type='primary' if st.session_state.page==p else 'secondary'):
                st.session_state.page=p
                st.session_state._consumed_page_qp=p
                st.rerun()
        st.divider()
        if st.session_state.admin or st.session_state.user_id:
            if st.button('Log out',use_container_width=True):
                st.session_state.admin=False; st.session_state.user_id=None; st.session_state.page='Login'; st.session_state._consumed_page_qp='Login'; st.rerun()
        st.caption('Created by MEET MEVADA')
    p=st.session_state.page
    if not st.session_state.admin and p not in ('Login','Track Order') and not st.session_state.user_id:
        p='Login'; st.session_state.page='Login'
    if not st.session_state.admin and p not in ('Login','Track Order'):
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
    elif p=='Your Bag': your_bag_page()
    elif p=='Order History': user_order_history()
    elif p=='Track Order': user_track_order_page() if st.session_state.user_id else public_track_page()
    elif p=='Order Details': admin_orders_page()
    elif p=='Emails': emails_page()
    elif p=='Account': account(False)
    elif p=='Master Account': account(True)
    elif p=='Admin Master': site_admin_page()
    elif p=='About':
        page_header('OUR STORY','About Rachna','Thoughtful materials. Reliable workmanship.')
        st.markdown(f'<div class="hero"><div class="brand-sub">PLAYWOOD · FURNITURE · HARDWARE</div><h2>{APP_NAME}</h2><p>A digital catalogue to showcase furniture, plywood and hardware products.</p></div>',unsafe_allow_html=True)
        rows=about_marquee_rows()
        if not rows:
            logo=get_setting('app_logo'); rows=[logo] if logo and image_row_source(logo) else []
        if rows:
            per_row=5; nrows=max(1,(len(rows)+per_row-1)//per_row); markup='<div class="marquee-wrap">'
            for i in range(nrows):
                group=rows[i*per_row:(i+1)*per_row] or rows; imgs=''.join(f"<div class='marquee-logo-box'><img src='{image_src_for_html(r)}' alt='Rachna logo'></div>" for r in group); track=imgs*2; direction='right' if i%2 else 'left'; markup+=f"<div class='marquee-row {direction}'><div class='marquee-track'>{track}</div></div>"
            st.markdown(markup+'</div>',unsafe_allow_html=True)
        real_mode=text_setting('about_real_stats','true').lower()=='true'
        if real_mode:
            customer_count=int((query('SELECT COUNT(*) AS n FROM rachna_users WHERE COALESCE(is_admin,FALSE)=FALSE AND COALESCE(active,TRUE)=TRUE')[0] or {}).get('n') or 0)
            product_count=len(products()); company_count=len(rows)
        else: customer_count=50000; product_count=5729; company_count=10000
        st.markdown(f'''<div style=\"display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:18px 0\"><div class=\"hero\"><div style=\"font-size:28px;font-weight:900\" data-count=\"{customer_count}\">+0</div><div>Customers</div></div><div class=\"hero\"><div style=\"font-size:28px;font-weight:900\" data-count=\"{product_count}\">+0</div><div>Products</div></div><div class=\"hero\"><div style=\"font-size:28px;font-weight:900\" data-count=\"{company_count}\">+0</div><div>Company Products Available</div></div></div><script>document.querySelectorAll('[data-count]').forEach(el=>{{let n=Number(el.dataset.count),i=0,step=Math.max(1,Math.ceil(n/45));let t=setInterval(()=>{{i=Math.min(n,i+step);el.textContent='+'+i.toLocaleString('en-IN');if(i>=n)clearInterval(t)}},22)}})</script>''',unsafe_allow_html=True)
        a,b,c=st.columns(3); a.markdown('### 🪵 Furniture\nMade-to-order furniture.'); b.markdown('### 🧰 Hardware\nFittings and hardware products.'); c.markdown('### 📐 Materials\nPlywood, sizes and colours.')
    elif p=='Contact Us':
        page_header('GET IN TOUCH','Get In Touch','Contact details will be added when provided.'); st.markdown('<div class="hero"><h2>We would love to hear from you.</h2><p>Contact information coming soon.</p></div>',unsafe_allow_html=True)

# st.markdown('<div style="margin-top:2rem;padding:1rem 0;border-top:1px solid #d6ae5255;text-align:center;color:#aab6c5;font-size:.8rem">© RACHNA PLAYWOO &amp; HARDWEAR · All rights reserved</div>', unsafe_allow_html=True)

if __name__=="__main__": main()

