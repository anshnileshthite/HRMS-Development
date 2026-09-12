import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
import pytz
import math
from streamlit_js_eval import get_geolocation
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

IST = pytz.timezone('Asia/Kolkata')

FIRMS = {
    "SAGAR": "SAGAR ENTERPRISES",
    "GEMSHINE": "GEMSHINE MULTISERVICES",
    "ELITE": "ELITE MULTISERVICES"
}

st.set_page_config(
    page_title="Workforce Portal - Sagar | Gemshine | Elite",
    page_icon="🏢",
    layout="centered",
    initial_sidebar_state="collapsed"
)

@st.cache_resource
def get_db():
    db_url = URL.create(
        drivername="postgresql+pg8000",
        username="postgres.lsyfgompyfjborgxzxkx",
        password="Haveaniceday@2027",
        host="aws-0-ap-southeast-1.pooler.supabase.com",
        port=6543,
        database="postgres"
    )
    return create_engine(db_url, pool_pre_ping=True)

engine = get_db()

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['emp_code'] = None
    st.session_state['company_id'] = None
    st.session_state['role'] = 'employee'

# --- LOGIN SCREEN ---
if not st.session_state['logged_in']:
    st.markdown("""
        <div style="text-align:center; margin-top:30px; margin-bottom:20px;">
            <div style="font-size:36px; color:#FF6B35;">❖</div>
            <h2 style="color:#2D3748; margin:0;">Contract Labour ESS Portal</h2>
            <p style="color:#718096; font-size:13px;">Sagar • Gemshine • Elite</p>
        </div>
    """, unsafe_allow_html=True)

    selected_firm_name = st.selectbox("Select Your Firm", list(FIRMS.values()))
    selected_firm_id = [k for k, v in FIRMS.items() if v == selected_firm_name][0]

    emp_input = st.text_input("Employee Code", placeholder="e.g. 001 or ADMIN").strip().upper()
    pwd_input = st.text_input("Password", type="password", placeholder="EmpCode@123")

    if st.button("Sign In", use_container_width=True):
        hashed = hashlib.sha256(pwd_input.encode()).hexdigest()
        with engine.connect() as conn:
            res = conn.execute(
                text("SELECT emp_code, role FROM user_accounts WHERE company_id = :cid AND emp_code = :code AND password_hash = :pwd"),
                {"cid": selected_firm_id, "code": emp_input, "pwd": hashed}
            ).fetchone()

            if res:
                st.session_state['logged_in'] = True
                st.session_state['emp_code'] = res[0]
                st.session_state['role'] = res[1]
                st.session_state['company_id'] = selected_firm_id
                st.rerun()
            else:
                st.error("Invalid credentials for this firm.")
    st.stop()

emp_code = st.session_state['emp_code']
company_id = st.session_state['company_id']
firm_name = FIRMS[company_id]
is_admin = (st.session_state['role'] == 'admin')

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"### ❖ {firm_name}")
    st.caption(f"Tenant ID: `{company_id}` | User: `{emp_code}`")
    st.divider()
    if st.button("Log Out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- PUNCH SCREEN ---
with engine.connect() as conn:
    emp = conn.execute(
        text("SELECT full_name FROM employees WHERE company_id = :cid AND emp_code = :code"),
        {"cid": company_id, "code": emp_code}
    ).fetchone()

worker_name = emp[0] if emp else "Worker"

st.markdown(f"""
    <div style="background:linear-gradient(135deg,#FF6B35,#F7931E); padding:18px; border-radius:18px; color:white; margin-bottom:15px;">
        <div style="font-size:12px; font-weight:600; background:rgba(255,255,255,0.2); display:inline-block; padding:3px 8px; border-radius:10px;">{firm_name}</div>
        <h3 style="margin:8px 0 2px 0;">Welcome, {worker_name.split()[0]}</h3>
        <p style="margin:0; font-size:12px; opacity:0.9;">Code: {emp_code}</p>
    </div>
""", unsafe_allow_html=True)

loc = get_geolocation()
now_ist = datetime.now(IST)
today_str = now_ist.strftime("%Y-%m-%d")
now_time = now_ist.strftime("%I:%M:%S %p")

# Site coordinates (SEZ Khed City default)
site_lat, site_lon, allowed_radius = 18.843600, 73.918900, 75.0

with engine.connect() as conn:
    punch = conn.execute(
        text("SELECT punch_in, punch_out FROM daily_punches WHERE company_id = :cid AND emp_code = :code AND punch_date = :dt"),
        {"cid": company_id, "code": emp_code, "dt": today_str}
    ).fetchone()

st.markdown(f"**IST Time:** `{now_time}`")

user_in_range = False
if loc and 'coords' in loc:
    dist = calculate_distance(loc['coords']['latitude'], loc['coords']['longitude'], site_lat, site_lon)
    if dist <= allowed_radius:
        user_in_range = True
        st.success(f"📍 Location OK ({round(dist, 1)}m)")
    else:
        st.warning(f"⚠️ {round(dist, 1)}m away from workplace.")
else:
    st.info("📡 Acquiring GPS...")

col1, col2 = st.columns(2)
with col1:
    if st.button("👆 Punch IN", use_container_width=True):
        if not user_in_range:
            st.error("Outside premises.")
        elif punch and punch[0]:
            st.warning("Already punched in.")
        else:
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO daily_punches (company_id, emp_code, punch_date, punch_in)
                    VALUES (:cid, :code, :dt, :tm)
                    ON CONFLICT (company_id, emp_code, punch_date) DO UPDATE SET punch_in = EXCLUDED.punch_in
                """), {"cid": company_id, "code": emp_code, "dt": today_str, "tm": now_time})
                conn.commit()
            st.success("Punched in successfully!")
            st.rerun()

with col2:
    if st.button("👋 Punch OUT", use_container_width=True):
        if not user_in_range:
            st.error("Outside premises.")
        elif not punch or not punch[0]:
            st.error("Punch in first.")
        else:
            with engine.connect() as conn:
                conn.execute(text("""
                    UPDATE daily_punches SET punch_out = :tm
                    WHERE company_id = :cid AND emp_code = :code AND punch_date = :dt
                """), {"tm": now_time, "cid": company_id, "code": emp_code, "dt": today_str})
                conn.commit()
            st.success("Punched out successfully!")
            st.rerun()