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
    page_title="APP",
    page_icon="🟠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Modern OpportuneHR Clean UI Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F8F9FB; }
    
    /* Top Bar Header */
    .top-brand {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: -35px;
        margin-bottom: 12px;
    }
    .brand-logo { font-size: 22px; color: #E85D04; font-weight: 800; }
    .brand-txt { font-size: 19px; font-weight: 700; color: #1E293B; letter-spacing: -0.5px; }

    /* Orange Profile Banner */
    .profile-banner {
        background: linear-gradient(135deg, #FF6B35 0%, #F58220 100%);
        padding: 16px 20px;
        border-radius: 16px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 14px rgba(245, 130, 32, 0.22);
    }
    .user-name-title { font-size: 20px; font-weight: 700; margin: 0; }
    .user-desig-sub { font-size: 12px; opacity: 0.92; margin-top: 2px; }

    /* Clean Card Container */
    .card-box {
        background: white;
        border-radius: 16px;
        padding: 16px 18px;
        border: 1px solid #ECEEF2;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        margin-bottom: 18px;
    }
    .card-title {
        font-size: 16px;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 14px;
    }

    /* Attendance Mini Grid */
    .att-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr 1fr 1fr;
        text-align: center;
        padding: 10px 0;
        border-top: 1px solid #F1F5F9;
        font-size: 13px;
    }
    .att-header { font-size: 11px; color: #64748B; font-weight: 600; margin-bottom: 4px; }
    .att-value { font-weight: 700; color: #0F172A; }

    /* Self Service Quick Action Icons */
    .self-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-top: 10px;
    }
    .action-button-tile {
        background: #FFFFFF;
        border-radius: 14px;
        padding: 16px 8px;
        text-align: center;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.02);
    }
    .tile-icon { font-size: 28px; margin-bottom: 6px; }
    .tile-label { font-size: 12px; font-weight: 600; color: #334155; }
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

def generate_detailed_payslip_pdf(comp_name, comp_addr, s, emp):
    buf = io.BytesIO()
    p = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    p.setFillColor(colors.HexColor("#FF6B35"))
    p.rect(0, h - 14, w, 14, stroke=0, fill=1)
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 15)
    p.drawCentredString(w / 2.0, h - 45, comp_name)
    p.setFont("Helvetica", 8)
    p.drawCentredString(w / 2.0, h - 58, comp_addr)
    p.setFont("Helvetica-Bold", 11)
    p.drawCentredString(w / 2.0, h - 75, f"PAYSLIP FOR THE MONTH OF: {int(s['month']):02d}/{int(s['year'])}")
    p.setStrokeColor(colors.HexColor("#CBD5E1"))
    p.line(35, h - 85, w - 35, h - 85)

    p.setFont("Helvetica-Bold", 9)
    p.drawString(40, h - 105, f"Employee Name: {emp.get('full_name', 'N/A')}")
    p.drawString(220, h - 105, f"Employee ID: {s['emp_code']}")
    p.drawString(400, h - 105, f"Designation: {emp.get('category', 'Technician')}")

    p.setFont("Helvetica", 9)
    p.drawString(40, h - 122, f"Bank Name: {emp.get('bank_name', 'N/A')}")
    p.drawString(220, h - 122, f"Account No: {emp.get('bank_account', 'N/A')}")
    p.drawString(400, h - 122, f"IFSC Code: {emp.get('bank_ifsc', 'N/A')}")

    p.drawString(40, h - 139, f"UAN No: {emp.get('uan_no', 'N/A')}")
    p.drawString(220, h - 139, f"ESIC No: {emp.get('esic_no', 'N/A')}")
    p.drawString(400, h - 139, f"PAN No: {emp.get('pan_no', 'N/A')}")

    p.drawString(40, h - 156, f"Worked Days: {s.get('days_worked', 0)}")
    p.drawString(220, h - 156, f"Total Days: {s.get('total_days', 31)}")
    p.drawString(400, h - 156, f"OT Hours: {s.get('ot_hours', 0)}")

    # Earnings & Deductions Box
    p.rect(35, h - 280, w - 70, 105)
    p.line(w / 2.0, h - 175, w / 2.0, h - 280)
    p.setFillColor(colors.HexColor("#F1F5F9"))
    p.rect(35, h - 190, w - 70, 15, fill=1, stroke=0)
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 9)
    p.drawString(45, h - 186, "EARNINGS")
    p.drawRightString(w / 2.0 - 15, h - 186, "AMOUNT (Rs.)")
    p.drawString(w / 2.0 + 15, h - 186, "DEDUCTIONS")
    p.drawRightString(w - 45, h - 186, "AMOUNT (Rs.)")

    p.setFont("Helvetica", 9)
    p.drawString(45, h - 205, "Basic:")
    p.drawRightString(w / 2.0 - 15, h - 205, f"{float(s.get('earned_basic') or 0):,.2f}")
    p.drawString(45, h - 220, "DA:")
    p.drawRightString(w / 2.0 - 15, h - 220, f"{float(s.get('earned_da') or 0):,.2f}")
    p.drawString(45, h - 235, "HRA:")
    p.drawRightString(w / 2.0 - 15, h - 235, f"{float(s.get('earned_hra') or 0):,.2f}")
    p.drawString(45, h - 250, "OT Amount:")
    p.drawRightString(w / 2.0 - 15, h - 250, f"{float(s.get('earned_ot_amt') or 0):,.2f}")

    p.drawString(w / 2.0 + 15, h - 205, "EPF:")
    p.drawRightString(w - 45, h - 205, f"{float(s.get('ded_pf') or 0):,.2f}")
    p.drawString(w / 2.0 + 15, h - 220, "ESIC:")
    p.drawRightString(w - 45, h - 220, f"{float(s.get('ded_esic') or 0):,.2f}")
    p.drawString(w / 2.0 + 15, h - 235, "PT:")
    p.drawRightString(w - 45, h - 235, f"{float(s.get('ded_pt') or 0):,.2f}")
    p.drawString(w / 2.0 + 15, h - 250, "Advance:")
    p.drawRightString(w - 45, h - 250, f"{float(s.get('ded_advance') or 0):,.2f}")

    p.line(35, h - 265, w - 35, h - 265)
    p.setFont("Helvetica-Bold", 9)
    p.drawString(45, h - 275, "GROSS EARNINGS:")
    p.drawRightString(w / 2.0 - 15, h - 275, f"Rs. {float(s.get('gross_amount') or 0):,.2f}")
    p.drawString(w / 2.0 + 15, h - 275, "TOTAL DEDUCTIONS:")
    p.drawRightString(w - 45, h - 275, f"Rs. {float(s.get('total_deduction') or 0):,.2f}")

    p.setFillColor(colors.HexColor("#059669"))
    p.rect(35, h - 320, w - 70, 26, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 11)
    p.drawCentredString(w / 2.0, h - 310, f"NET SALARY: Rs. {float(s.get('net_wages') or 0):,.2f}")

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
    st.session_state['current_page'] = "Home"

# ==========================================
# LOGIN SCREEN
# ==========================================
if not st.session_state['logged_in']:
    st.markdown("""
        <div style="text-align:center; margin-top:30px; margin-bottom:15px;">
            <div style="font-size:36px; color:#E85D04;">🟠</div>
            <h2 style="color:#0F172A; margin:0; font-weight:800;">ESS PORTAL</h2>
            <p style="color:#64748B; font-size:13px;">Workforce Self Service</p>
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
                st.session_state['current_page'] = "Home"
                st.rerun()
            else:
                st.error("Invalid credentials for this firm.")
    st.stop()

emp_code = st.session_state['emp_code']
company_id = st.session_state['company_id']
firm_info = FIRMS[company_id]
is_admin = (st.session_state['role'] == 'admin')

# Read accurate employee details
with engine.connect() as conn:
    res = conn.execute(
        text("SELECT * FROM employees WHERE company_id = :cid AND emp_code = :c"),
        {"cid": company_id, "c": emp_code}
    )
    row = res.mappings().fetchone()
    emp_data = dict(row) if row else {}

worker_name = emp_data.get("full_name", "Worker")

# ==========================================
# SIDEBAR DRAWER (Opportune Style Menu)
# ==========================================
with st.sidebar:
    st.markdown("""
        <div style="display:flex; align-items:center; gap:8px; padding-bottom:10px;">
            <span style="font-size:20px; color:#FF6B35;">🟠</span>
            <b style="font-size:18px; color:#1E293B;">APP</b>
        </div>
    """, unsafe_allow_html=True)
    st.caption(f"Tenant: **{firm_info['name']}** | ID: `{emp_code}`")
    st.divider()

    if st.button("🏠 Home", use_container_width=True):
        st.session_state['current_page'] = "Home"
        st.rerun()

    if not is_admin:
        if st.button("👤 My Profile", use_container_width=True):
            st.session_state['current_page'] = "Profile"
            st.rerun()
        if st.button("📅 My Attendance", use_container_width=True):
            st.session_state['current_page'] = "Attendance"
            st.rerun()
        if st.button("💵 Salary Slips", use_container_width=True):
            st.session_state['current_page'] = "Salary"
            st.rerun()
        if st.button("📂 My Documents", use_container_width=True):
            st.session_state['current_page'] = "Docs"
            st.rerun()
    else:
        if st.button("📋 Attendance Muster", use_container_width=True):
            st.session_state['current_page'] = "Muster"
            st.rerun()
        if st.button("📤 Upload Documents", use_container_width=True):
            st.session_state['current_page'] = "AdminDocs"
            st.rerun()

    st.divider()
    if st.button("Log Out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

page = st.session_state.get('current_page', "Home")

# ==========================================
# PAGE: HOME DASHBOARD
# ==========================================
if page == "Home":
    st.markdown("""
        <div class="top-brand">
            <span class="brand-logo">🟠</span>
            <span class="brand-txt">APP</span>
        </div>
    """, unsafe_allow_html=True)

    # Orange Profile Banner
    st.markdown(f"""
        <div class="profile-banner">
            <div class="user-name-title">{worker_name} ({emp_code})</div>
            <div class="user-desig-sub">{emp_data.get('category', 'Technician')} • {firm_info['name']}</div>
        </div>
    """, unsafe_allow_html=True)

    # Attendance Strip
    today_str = datetime.now(IST).strftime("%Y-%m-%d")
    with engine.connect() as conn:
        p_today = conn.execute(
            text("SELECT punch_in, punch_out, ot_hours FROM daily_punches WHERE company_id = :cid AND emp_code = :c AND punch_date = :d"),
            {"cid": company_id, "c": emp_code, "d": today_str}
        ).fetchone()

    in_t = p_today[0] if p_today and p_today[0] else "--:--"
    out_t = p_today[1] if p_today and p_today[1] else "--:--"
    ot_h = str(p_today[2]) if p_today and p_today[2] else "0"
    st_val = "P" if (p_today and p_today[0]) else "A"

    st.markdown(f"""
        <div class="card-box">
            <div class="card-title">My Attendance</div>
            <div class="att-grid">
                <div><div class="att-header">DATE</div><div class="att-value">{datetime.now(IST).strftime('%d %b')}</div></div>
                <div><div class="att-header">IN</div><div class="att-value">{in_t}</div></div>
                <div><div class="att-header">OUT</div><div class="att-value">{out_t}</div></div>
                <div><div class="att-header">OT</div><div class="att-value">{ot_h}</div></div>
                <div><div class="att-header">STATUS</div><div class="att-value" style="color:{'#10B981' if st_val=='P' else '#EF4444'}">{st_val}</div></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Punch Clock Action
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
            st.warning(f"⚠️ {round(dist, 1)}m away from workplace.")
    else:
        st.info("📡 Checking GPS location...")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("👆 Punch IN", use_container_width=True):
            if not user_in_range:
                st.error("Outside premises.")
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

    with col2:
        if st.button("👋 Punch OUT", use_container_width=True):
            if not user_in_range:
                st.error("Outside premises.")
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

    # Self Service Grid (No Leave Section)
    st.markdown('<div class="card-title" style="margin-top:10px;">Self Service</div>', unsafe_allow_html=True)
    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown('<div class="action-button-tile"><div class="tile-icon">👤</div><div class="tile-label">My Profile</div></div>', unsafe_allow_html=True)
        if st.button("Open Profile", use_container_width=True, key="btn_p"):
            st.session_state['current_page'] = "Profile"
            st.rerun()
    with g2:
        st.markdown('<div class="action-button-tile"><div class="tile-icon">📅</div><div class="tile-label">Attendance</div></div>', unsafe_allow_html=True)
        if st.button("Open Attendance", use_container_width=True, key="btn_a"):
            st.session_state['current_page'] = "Attendance"
            st.rerun()
    with g3:
        st.markdown('<div class="action-button-tile"><div class="tile-icon">💵</div><div class="tile-label">Salary Slip</div></div>', unsafe_allow_html=True)
        if st.button("Open Payslip", use_container_width=True, key="btn_s"):
            st.session_state['current_page'] = "Salary"
            st.rerun()

# ==========================================
# PAGE: MY PROFILE (Accurate Values)
# ==========================================
elif page == "Profile":
    if st.button("← Back to Home"):
        st.session_state['current_page'] = "Home"
        st.rerun()

    st.markdown('<div class="card-title">My Profile & Verified Records</div>', unsafe_allow_html=True)
    with st.container():
        c1, c2 = st.columns(2)
        c1.write(f"**Employee Name:** {emp_data.get('full_name', 'N/A')}")
        c1.write(f"**Employee ID:** `{emp_code}`")
        c1.write(f"**Designation / Category:** {emp_data.get('category', 'Technician')}")
        c1.write(f"**Father's Name:** {emp_data.get('father_name', 'N/A')}")

        c2.write(f"**Bank Name:** {emp_data.get('bank_name', 'N/A')}")
        c2.write(f"**Account Number:** {emp_data.get('bank_account', 'N/A')}")
        c2.write(f"**IFSC Code:** {emp_data.get('bank_ifsc', 'N/A')}")
        c2.write(f"**UAN (PF Number):** {emp_data.get('uan_no', 'N/A')}")

        st.divider()
        st.write(f"**ESIC Number:** {emp_data.get('esic_no', 'N/A')} | **PAN:** {emp_data.get('pan_no', 'N/A')}")

# ==========================================
# PAGE: ATTENDANCE HISTORY
# ==========================================
elif page == "Attendance":
    if st.button("← Back to Home"):
        st.session_state['current_page'] = "Home"
        st.rerun()

    st.title("Attendance Records")
    with engine.connect() as conn:
        df_att = pd.read_sql(text("""
            SELECT punch_date as "Date", punch_in as "In Time", punch_out as "Out Time",
                   COALESCE(ot_hours, 0) as "OT Hours", punch_status as "Status"
            FROM daily_punches 
            WHERE company_id = :cid AND emp_code = :c 
            ORDER BY punch_date DESC
        """), conn, params={"cid": company_id, "c": emp_code})
    st.dataframe(df_att, use_container_width=True)

# ==========================================
# PAGE: SALARY SLIPS
# ==========================================
elif page == "Salary":
    if st.button("← Back to Home"):
        st.session_state['current_page'] = "Home"
        st.rerun()

    st.title("Salary Slips")
    with engine.connect() as conn:
        slips = pd.read_sql(
            text("SELECT * FROM monthly_wages WHERE company_id = :cid AND emp_code = :c ORDER BY year DESC, month DESC"),
            conn,
            params={"cid": company_id, "c": emp_code}
        )

    if slips.empty:
        st.info("No salary slips found.")
    else:
        for _, s in slips.iterrows():
            with st.expander(f"Month: {int(s['month']):02d}/{int(s['year'])} — Net Salary: ₹{s['net_wages']:,.2f}", expanded=True):
                pdf_data = generate_detailed_payslip_pdf(firm_info['name'], firm_info['address'], s, emp_data)
                st.download_button(
                    "📥 Download Salary Slip (PDF)",
                    pdf_data,
                    f"Payslip_{int(s['month'])}_{int(s['year'])}_{emp_code}.pdf",
                    "application/pdf",
                    key=f"dl_{s['id']}"
                )

# ==========================================
# PAGE: MY DOCUMENTS
# ==========================================
elif page == "Docs":
    if st.button("← Back to Home"):
        st.session_state['current_page'] = "Home"
        st.rerun()

    st.title("Official Documents")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Offer Letter")
        if emp_data.get("doc_offer_letter_b64"):
            b = base64.b64decode(emp_data["doc_offer_letter_b64"])
            st.download_button("⬇️ Download Offer Letter", b, f"Offer_Letter_{emp_code}.pdf", "application/pdf")
        else:
            st.info("Offer letter will be uploaded by HR.")
    with col2:
        st.subheader("ESIC Card")
        if emp_data.get("doc_esic_b64"):
            b = base64.b64decode(emp_data["doc_esic_b64"])
            st.download_button("⬇️ Download ESIC Card", b, f"ESIC_Card_{emp_code}.pdf", "application/pdf")
        else:
            st.info("ESIC Card will be uploaded by HR.")