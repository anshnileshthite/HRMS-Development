import streamlit as st
import pandas as pd
from datetime import datetime, date
import hashlib
import pytz
import math
import io
import base64
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from streamlit_js_eval import get_geolocation
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

IST = pytz.timezone('Asia/Kolkata')

FIRMS = {
    "SAGAR": {
        "name": "SAGAR ENTERPRISES",
        "address": "A/P Nimgaon, Tal-Khed, Dist-Pune - 410505",
        "lat": 18.843600,
        "lon": 73.918900,
        "radius": 150.0
    },
    "GEMSHINE": {
        "name": "GEMSHINE MULTISERVICES",
        "address": "SEZ, Khed City, Pune, Maharashtra - 410505",
        "lat": 18.843600,
        "lon": 73.918900,
        "radius": 150.0
    },
    "ELITE": {
        "name": "ELITE MULTISERVICES",
        "address": "Chakan MIDC Phase II, Pune - 410501",
        "lat": 18.760600,
        "lon": 73.863600,
        "radius": 150.0
    }
}

st.set_page_config(
    page_title="ESS PORTAL",
    page_icon="📱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom Styling matching OpportuneHR mobile theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F8F9FB; }
    
    /* Mobile Top App Bar */
    .app-header-bar {
        background: linear-gradient(135deg, #FF6B35 0%, #F58220 100%);
        padding: 16px 18px;
        border-radius: 0 0 20px 20px;
        color: white;
        margin: -4rem -1rem 1rem -1rem;
        box-shadow: 0 4px 12px rgba(245, 130, 32, 0.25);
    }
    .user-greeting { font-size: 19px; font-weight: 700; margin: 4px 0 0 0; }
    .firm-sub { font-size: 11px; opacity: 0.9; text-transform: uppercase; letter-spacing: 0.5px; }

    /* Attendance Mini Card */
    .att-card {
        background: white;
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        border: 1px solid #ECEEF2;
        margin-bottom: 18px;
    }
    .att-title { font-size: 15px; font-weight: 700; color: #1E293B; margin-bottom: 10px; }
    .att-row {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr 1fr;
        text-align: center;
        padding: 8px 0;
        border-top: 1px solid #F1F5F9;
        font-size: 13px;
    }
    .att-val { font-weight: 600; color: #0F172A; }
    .att-lbl { font-size: 10px; color: #64748B; margin-bottom: 2px; }

    /* Action Tiles Grid */
    .action-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-bottom: 20px;
    }
    .action-tile {
        background: white;
        border-radius: 14px;
        padding: 14px 8px;
        text-align: center;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    }
    .action-icon { font-size: 26px; margin-bottom: 4px; }
    .action-lbl { font-size: 11px; font-weight: 600; color: #334155; }
</style>
""", unsafe_allow_html=True)

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

def generate_payslip_pdf(comp_name, comp_addr, s, emp_name):
    buf = io.BytesIO()
    p = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(w / 2.0, h - 50, comp_name)
    p.setFont("Helvetica", 9)
    p.drawCentredString(w / 2.0, h - 65, comp_addr)
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(w / 2.0, h - 85, f"SALARY SLIP - {int(s['month']):02d}/{int(s['year'])}")
    p.line(40, h - 95, w - 40, h - 95)
    p.setFont("Helvetica", 10)
    p.drawString(40, h - 115, f"Emp Code: {s['emp_code']}")
    p.drawString(220, h - 115, f"Name: {emp_name}")
    p.drawString(420, h - 115, f"Worked Days: {s['days_worked']}")
    p.rect(40, h - 230, w - 80, 100)
    p.line(w / 2.0, h - 130, w / 2.0, h - 230)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, h - 145, "EARNINGS")
    p.drawString(w / 2.0 + 10, h - 145, "DEDUCTIONS")
    p.setFont("Helvetica", 9)
    p.drawString(50, h - 165, f"Basic: Rs. {s['earned_basic']:,.2f}")
    p.drawString(50, h - 180, f"DA: Rs. {s['earned_da']:,.2f}")
    p.drawString(50, h - 195, f"HRA: Rs. {s['earned_hra']:,.2f}")
    p.drawString(50, h - 210, f"OT: Rs. {s['earned_ot_amt']:,.2f}")
    p.drawString(w / 2.0 + 10, h - 165, f"EPF: Rs. {s['ded_pf']:,.2f}")
    p.drawString(w / 2.0 + 10, h - 180, f"ESIC: Rs. {s['ded_esic']:,.2f}")
    p.drawString(w / 2.0 + 10, h - 195, f"PT: Rs. {s['ded_pt']:,.2f}")
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, h - 250, f"Gross: Rs. {s['gross_amount']:,.2f}")
    p.drawString(w / 2.0 + 10, h - 250, f"Net Pay: Rs. {s['net_wages']:,.2f}")
    p.showPage()
    p.save()
    buf.seek(0)
    return buf.getvalue()

# Session State
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['emp_code'] = None
    st.session_state['company_id'] = None
    st.session_state['role'] = 'employee'
    st.session_state['current_view'] = 'Home'

# ==========================================
# LOGIN SCREEN
# ==========================================
if not st.session_state['logged_in']:
    st.markdown("""
        <div style="text-align:center; margin-top:25px; margin-bottom:15px;">
            <div style="font-size:38px; color:#FF6B35;">❖</div>
            <h2 style="color:#0F172A; margin:0;">ESS PORTAL</h2>
            <p style="color:#64748B; font-size:13px;">Mobile Workforce Management System</p>
        </div>
    """, unsafe_allow_html=True)

    firm_choices = {v["name"]: k for k, v in FIRMS.items()}
    sel_name = st.selectbox("Select Your Firm", list(firm_choices.keys()))
    sel_id = firm_choices[sel_name]

    emp_inp = st.text_input("Employee Code / Admin ID", placeholder="e.g. 001 or ADMIN").strip().upper()
    pwd_inp = st.text_input("Password", type="password", placeholder="EmpCode@123 or Admin@123")

    if st.button("Sign In", use_container_width=True):
        hashed = hashlib.sha256(pwd_inp.encode()).hexdigest()
        with engine.connect() as conn:
            u = conn.execute(
                text("SELECT emp_code, role FROM user_accounts WHERE company_id = :cid AND emp_code = :c AND password_hash = :p"),
                {"cid": sel_id, "c": emp_inp, "p": hashed}
            ).fetchone()

            if u:
                st.session_state['logged_in'] = True
                st.session_state['emp_code'] = u[0]
                st.session_state['role'] = u[1]
                st.session_state['company_id'] = sel_id
                st.session_state['current_view'] = "Home"
                st.rerun()
            else:
                st.error("Invalid credentials for this firm.")
    st.stop()

emp_code = st.session_state['emp_code']
company_id = st.session_state['company_id']
firm_info = FIRMS[company_id]
is_admin = (st.session_state['role'] == 'admin')

# Fetch Employee Info safely
with engine.connect() as conn:
    res = conn.execute(
        text("SELECT * FROM employees WHERE company_id = :cid AND emp_code = :c"),
        {"cid": company_id, "c": emp_code}
    )
    row = res.mappings().fetchone()
    emp_data = dict(row) if row else {}

worker_name = emp_data.get("full_name", "Employee")

# ==========================================
# APP DRAWER / SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown(f"""
        <div style="padding:10px 0;">
            <div style="font-size:18px; font-weight:700; color:#FF6B35;">❖ {firm_info['name']}</div>
            <div style="font-size:12px; color:#64748B;">ID: {emp_code} • {st.session_state['role'].upper()}</div>
        </div>
    """, unsafe_allow_html=True)
    st.divider()

    if st.button("🏠 Home Dashboard", use_container_width=True):
        st.session_state['current_view'] = 'Home'
        st.rerun()

    if not is_admin:
        if st.button("👤 My Profile", use_container_width=True):
            st.session_state['current_view'] = 'Profile'
            st.rerun()
        if st.button("💵 Salary Slips", use_container_width=True):
            st.session_state['current_view'] = 'Salary'
            st.rerun()
        if st.button("📅 Leave Request", use_container_width=True):
            st.session_state['current_view'] = 'Leave'
            st.rerun()
    else:
        if st.button("📋 Biometric Muster", use_container_width=True):
            st.session_state['current_view'] = 'AdminMuster'
            st.rerun()
        if st.button("⏱️ OT Approvals", use_container_width=True):
            st.session_state['current_view'] = 'AdminOT'
            st.rerun()

    st.divider()
    if st.button("Log Out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

view = st.session_state.get('current_view', 'Home')

# ==========================================
# VIEW: HOME DASHBOARD (OPPORTUNE-STYLE)
# ==========================================
if view == "Home":
    # 1. Orange App Bar
    st.markdown(f"""
        <div class="app-header-bar">
            <div class="firm-sub">{firm_info['name']}</div>
            <div class="user-greeting">{worker_name} ({emp_code})</div>
        </div>
    """, unsafe_allow_html=True)

    # 2. My Attendance Mini-strip
    today_str = datetime.now(IST).strftime("%Y-%m-%d")
    with engine.connect() as conn:
        p_today = conn.execute(
            text("SELECT punch_in, punch_out, ot_hours FROM daily_punches WHERE company_id = :cid AND emp_code = :c AND punch_date = :d"),
            {"cid": company_id, "c": emp_code, "d": today_str}
        ).fetchone()

    in_time = p_today[0] if p_today and p_today[0] else "--:--"
    out_time = p_today[1] if p_today and p_today[1] else "--:--"
    status_disp = "P" if (p_today and p_today[0]) else "A"

    st.markdown(f"""
        <div class="att-card">
            <div class="att-title">My Attendance</div>
            <div class="att-row">
                <div><div class="att-lbl">DATE</div><div class="att-val">{datetime.now(IST).strftime('%d %b')}</div></div>
                <div><div class="att-lbl">IN</div><div class="att-val">{in_time}</div></div>
                <div><div class="att-lbl">OUT</div><div class="att-val">{out_time}</div></div>
                <div><div class="att-lbl">STATUS</div><div class="att-val" style="color:{'#10B981' if status_disp=='P' else '#EF4444'}">{status_disp}</div></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 3. Punch In / Out Action Bar
    loc = get_geolocation()
    user_in_range = False
    u_lat, u_lon = None, None
    if loc and 'coords' in loc:
        u_lat = loc['coords']['latitude']
        u_lon = loc['coords']['longitude']
        dist = calculate_distance(u_lat, u_lon, firm_info['lat'], firm_info['lon'])
        if dist <= firm_info['radius']:
            user_in_range = True
            st.success(f"📍 Workplace Verified ({round(dist, 1)}m)")
        else:
            st.warning(f"⚠️ {round(dist, 1)}m away from workplace gate.")
    else:
        st.info("📡 Acquiring GPS coordinates... Please allow location access.")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("👆 Punch IN", use_container_width=True):
            if not user_in_range:
                st.error("Outside authorized premises.")
            elif p_today and p_today[0]:
                st.warning("Already punched in today.")
            else:
                now_str = datetime.now(IST).strftime("%I:%M %p")
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO daily_punches (company_id, emp_code, punch_date, punch_in, in_lat, in_lon)
                        VALUES (:cid, :c, :d, :tm, :lat, :lon)
                        ON CONFLICT (company_id, emp_code, punch_date) DO UPDATE SET punch_in = EXCLUDED.punch_in, in_lat = EXCLUDED.in_lat, in_lon = EXCLUDED.in_lon
                    """), {"cid": company_id, "c": emp_code, "d": today_str, "tm": now_str, "lat": u_lat, "lon": u_lon})
                    conn.commit()
                st.success("Punched In successfully!")
                st.rerun()

    with c2:
        if st.button("👋 Punch OUT", use_container_width=True):
            if not user_in_range:
                st.error("Outside authorized premises.")
            elif not p_today or not p_today[0]:
                st.error("Punch In first.")
            else:
                now_str = datetime.now(IST).strftime("%I:%M %p")
                with engine.connect() as conn:
                    conn.execute(text("""
                        UPDATE daily_punches SET punch_out = :tm, out_lat = :lat, out_lon = :lon
                        WHERE company_id = :cid AND emp_code = :c AND punch_date = :d
                    """), {"tm": now_str, "lat": u_lat, "lon": u_lon, "cid": company_id, "c": emp_code, "d": today_str})
                    conn.commit()
                st.success("Punched Out successfully!")
                st.rerun()

    st.write("---")

    # 4. Self Service Quick Action Tiles
    st.markdown('<div class="att-title">Self Service</div>', unsafe_allow_html=True)
    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown('<div class="action-tile"><div class="action-icon">👤</div><div class="action-lbl">My Profile</div></div>', unsafe_allow_html=True)
        if st.button("Open Profile", use_container_width=True, key="btn_prof"):
            st.session_state['current_view'] = 'Profile'
            st.rerun()
    with g2:
        st.markdown('<div class="action-tile"><div class="action-icon">📝</div><div class="action-lbl">Leave Request</div></div>', unsafe_allow_html=True)
        if st.button("Open Leave", use_container_width=True, key="btn_lv"):
            st.session_state['current_view'] = 'Leave'
            st.rerun()
    with g3:
        st.markdown('<div class="action-tile"><div class="action-icon">💵</div><div class="action-lbl">Salary Slip</div></div>', unsafe_allow_html=True)
        if st.button("Open Payslip", use_container_width=True, key="btn_pay"):
            st.session_state['current_view'] = 'Salary'
            st.rerun()

# ==========================================
# VIEW: MY DETAILED PROFILE (SAFE LOOKUPS)
# ==========================================
elif view == "Profile":
    if st.button("← Back to Home"):
        st.session_state['current_view'] = 'Home'
        st.rerun()

    st.title("My Profile & KYC")
    t1, t2, t3 = st.tabs(["Personal & Bank", "Experience & Skills", "Documents & Photo"])

    with t1:
        st.write(f"**Name:** {emp_data.get('full_name', '')}")
        st.write(f"**Father's Name:** {emp_data.get('father_name', 'N/A')}")
        bg = st.text_input("Blood Group", value=str(emp_data.get("blood_group") or ""))
        ms = st.selectbox("Marital Status", ["Single", "Married", "Other"], index=0)
        em = st.text_input("Emergency Contact", value=str(emp_data.get("emergency_contact") or ""))
        st.divider()
        st.write(f"**Bank:** {emp_data.get('bank_name', 'N/A')} | **A/C:** {emp_data.get('bank_account', 'N/A')}")
        st.write(f"**IFSC:** {emp_data.get('bank_ifsc', 'N/A')}")
        st.write(f"**UAN:** {emp_data.get('uan_no', 'N/A')} | **ESIC:** {emp_data.get('esic_no', 'N/A')}")
        if st.button("Save Personal Data", use_container_width=True):
            with engine.connect() as conn:
                conn.execute(
                    text("UPDATE employees SET blood_group=:b, marital_status=:m, emergency_contact=:e WHERE company_id=:cid AND emp_code=:c"),
                    {"b": bg, "m": ms, "e": em, "cid": company_id, "c": emp_code}
                )
                conn.commit()
            st.success("Updated successfully.")

    with t2:
        qual = st.text_area("Educational Qualification", value=str(emp_data.get("qualifications") or ""))
        exp = st.text_area("Prior Experience", value=str(emp_data.get("work_experience") or ""))
        sk = st.text_input("Key Skills", value=str(emp_data.get("skills") or ""))
        if st.button("Save Skills & Experience", use_container_width=True):
            with engine.connect() as conn:
                conn.execute(
                    text("UPDATE employees SET qualifications=:q, work_experience=:w, skills=:s WHERE company_id=:cid AND emp_code=:c"),
                    {"q": qual, "w": exp, "s": sk, "cid": company_id, "c": emp_code}
                )
                conn.commit()
            st.success("Skills updated successfully.")

    with t3:
        st.subheader("Upload Documents")
        photo = st.file_uploader("Upload Profile Photo", type=["jpg", "png", "jpeg"])
        if photo and st.button("Save Photo", use_container_width=True):
            b64_img = base64.b64encode(photo.read()).decode()
            with engine.connect() as conn:
                conn.execute(text("UPDATE employees SET photo_b64=:p WHERE company_id=:cid AND emp_code=:c"), {"p": b64_img, "cid": company_id, "c": emp_code})
                conn.commit()
            st.success("Photo uploaded successfully.")

# ==========================================
# VIEW: SALARY SLIPS
# ==========================================
elif view == "Salary":
    if st.button("← Back to Home"):
        st.session_state['current_view'] = 'Home'
        st.rerun()

    st.title("My Salary Slips")
    with engine.connect() as conn:
        slips = pd.read_sql(
            text("SELECT * FROM monthly_wages WHERE company_id = :cid AND emp_code = :c ORDER BY year DESC, month DESC"),
            conn,
            params={"cid": company_id, "c": emp_code}
        )

    if slips.empty:
        st.info("No payslips found.")
    else:
        for _, s in slips.iterrows():
            with st.expander(f"Month: {int(s['month']):02d}/{int(s['year'])} — Net: ₹{s['net_wages']:,.2f}", expanded=True):
                pdf = generate_payslip_pdf(firm_info['name'], firm_info['address'], s, worker_name)
                st.download_button("📥 Download PDF Slip", pdf, f"Payslip_{int(s['month'])}_{int(s['year'])}.pdf", "application/pdf", key=f"dl_{s['id']}")

# ==========================================
# VIEW: LEAVE REQUEST
# ==========================================
elif view == "Leave":
    if st.button("← Back to Home"):
        st.session_state['current_view'] = 'Home'
        st.rerun()

    st.title("Apply for Leave")
    l_type = st.selectbox("Leave Type", ["Casual Leave", "Sick Leave", "Paid Leave", "Comp Off"])
    d_from = st.date_input("From Date")
    d_to = st.date_input("To Date")
    reason = st.text_area("Reason")

    if st.button("Submit Leave", use_container_width=True):
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO leave_requests (company_id, emp_code, leave_type, from_date, to_date, reason) VALUES (:cid, :c, :l, :f, :t, :r)"),
                {"cid": company_id, "c": emp_code, "l": l_type, "f": str(d_from), "t": str(d_to), "r": reason}
            )
            conn.commit()
        st.success("Leave submitted for HR approval.")