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
        "radius": 100.0
    },
    "GEMSHINE": {
        "name": "GEMSHINE MULTISERVICES",
        "address": "SEZ, Khed City, Pune, Maharashtra - 410505",
        "lat": 18.843600,
        "lon": 73.918900,
        "radius": 100.0
    },
    "ELITE": {
        "name": "ELITE MULTISERVICES",
        "address": "Chakan MIDC Phase II, Pune - 410501",
        "lat": 18.760600,
        "lon": 73.863600,
        "radius": 100.0
    }
}

st.set_page_config(
    page_title="ESS PORTAL",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .stApp { background-color: #F8F9FB; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .portal-banner {
        background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%);
        padding: 20px;
        border-radius: 14px;
        color: white;
        margin-bottom: 20px;
    }
    .stat-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #E2E8F0;
        text-align: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .stat-num { font-size: 26px; font-weight: 700; color: #FF6B35; }
    .stat-desc { font-size: 12px; color: #718096; text-transform: uppercase; }
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

# --- PDF GENERATOR (OFFER / APPOINTMENT / PAYSLIP) ---
def generate_official_letter(letter_type, comp_name, comp_addr, emp_name, emp_code, designation, joining_date, ctc):
    buf = io.BytesIO()
    p = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    p.setFillColor(colors.HexColor("#FF6B35"))
    p.rect(0, h - 14, w, 14, stroke=0, fill=1)
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, h - 55, comp_name)
    p.setFont("Helvetica", 9)
    p.drawString(40, h - 70, comp_addr)
    p.setStrokeColor(colors.HexColor("#CBD5E1"))
    p.line(40, h - 80, w - 40, h - 80)

    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(w / 2.0, h - 115, letter_type.upper())

    p.setFont("Helvetica", 10)
    p.drawString(40, h - 145, f"Date: {joining_date}")
    p.drawString(40, h - 162, f"To: {emp_name} (Emp ID: {emp_code})")

    lines = [
        f"Dear {emp_name},",
        f"",
        f"We are pleased to offer/appoint you for the role of '{designation}' at {comp_name}.",
        f"Your employment is effective from {joining_date} under the following statutory conditions:",
        f"",
        f"1. Total Monthly Gross CTC: Rs. {ctc:,.2f}/- inclusive of statutory Basic, DA, and HRA.",
        f"2. Statutory Compliance: Subject to deductions and employer deposits towards EPF, ESIC, and PT.",
        f"3. Workplace Deployment: Authorized client plants and premises in Pune/Khed industrial zone.",
        f"4. Working Hours: Shift timing shall conform with statutory roster guidelines (General/A/B/C).",
        f"5. Verification: This letter is subject to submission and approval of required KYC documents.",
        f"",
        f"Please sign and accept the terms outlined above.",
        f"",
        f"For {comp_name}",
        f"Authorized HR Signatory"
    ]
    y = h - 195
    for l in lines:
        p.drawString(40, y, l)
        y -= 17

    p.drawString(w - 230, h - 490, "Candidate Signature: ________________")
    p.showPage()
    p.save()
    buf.seek(0)
    return buf.getvalue()

def generate_payslip_pdf(comp_name, comp_addr, s, emp_name):
    buf = io.BytesIO()
    p = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    p.setFillColor(colors.HexColor("#1E293B"))
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(w / 2.0, h - 50, comp_name)
    p.setFont("Helvetica", 9)
    p.drawCentredString(w / 2.0, h - 65, comp_addr)
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(w / 2.0, h - 85, f"SALARY SLIP - {int(s['month']):02d}/{int(s['year'])}")
    p.line(40, h - 95, w - 40, h - 95)

    p.setFont("Helvetica", 10)
    p.drawString(40, h - 115, f"Emp Code: {s['emp_code']}")
    p.drawString(200, h - 115, f"Name: {emp_name}")
    p.drawString(400, h - 115, f"Worked Days: {s['days_worked']}")

    # Earnings & Deductions Table Box
    p.rect(40, h - 250, w - 80, 120)
    p.line(w / 2.0, h - 130, w / 2.0, h - 250)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, h - 145, "EARNINGS")
    p.drawString(w / 2.0 + 10, h - 145, "DEDUCTIONS")

    p.setFont("Helvetica", 9)
    p.drawString(50, h - 165, f"Basic: Rs. {s['earned_basic']:,.2f}")
    p.drawString(50, h - 180, f"DA: Rs. {s['earned_da']:,.2f}")
    p.drawString(50, h - 195, f"HRA: Rs. {s['earned_hra']:,.2f}")
    p.drawString(50, h - 210, f"OT Amount: Rs. {s['earned_ot_amt']:,.2f}")

    p.drawString(w / 2.0 + 10, h - 165, f"EPF: Rs. {s['ded_pf']:,.2f}")
    p.drawString(w / 2.0 + 10, h - 180, f"ESIC: Rs. {s['ded_esic']:,.2f}")
    p.drawString(w / 2.0 + 10, h - 195, f"PT: Rs. {s['ded_pt']:,.2f}")
    p.drawString(w / 2.0 + 10, h - 210, f"Advance: Rs. {s['ded_advance']:,.2f}")

    p.line(40, h - 225, w - 40, h - 225)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, h - 240, f"Gross Wages: Rs. {s['gross_amount']:,.2f}")
    p.drawString(w / 2.0 + 10, h - 240, f"Total Deductions: Rs. {s['total_deduction']:,.2f}")

    p.setFillColor(colors.HexColor("#059669"))
    p.rect(40, h - 290, w - 80, 30, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(w / 2.0, h - 278, f"NET TAKE HOME PAY: Rs. {s['net_wages']:,.2f}")

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

# ==========================================
# LOGIN SCREEN
# ==========================================
if not st.session_state['logged_in']:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("""
            <div style="text-align:center; margin-top:35px; margin-bottom:20px;">
                <div style="font-size:42px; color:#FF6B35;">❖</div>
                <h1 style="color:#1E293B; margin:0;">ESS PORTAL</h1>
                <p style="color:#64748B; font-size:14px;">Multi-Firm Cloud HRMS & Workforce Platform</p>
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
                    st.session_state['page'] = "Dashboard" if u[1] == 'admin' else "Punch Clock"
                    st.rerun()
                else:
                    st.error("Invalid credentials for this firm.")
    st.stop()

emp_code = st.session_state['emp_code']
company_id = st.session_state['company_id']
firm_info = FIRMS[company_id]
is_admin = (st.session_state['role'] == 'admin')

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown(f"### ❖ {firm_info['name']}")
    st.caption(f"Tenant: `{company_id}` | User: `{emp_code}` ({st.session_state['role'].upper()})")
    st.divider()

    if is_admin:
        menu = st.radio("HR Administration", [
            "📊 Executive Dashboard",
            "📋 Live Biometric Muster",
            "⏱️ OT & Hours Approval",
            "📜 Appointment & Offer Letters",
            "👥 Workforce & KYC Directory",
            "🏖️ Leave & Holiday Approvals",
            "💰 Monthly Wage Register"
        ])
    else:
        menu = st.radio("Self Service Menu", [
            "📍 Punch Clock",
            "👤 My Detailed Profile",
            "💵 My Salary Slips",
            "📝 Apply Leave & Comp-Off",
            "📜 My Official Letters"
        ])

    st.divider()
    if st.button("Log Out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# =====================================================================
# EMPLOYER / HR ADMIN PORTAL
# =====================================================================
if is_admin:
    if menu == "📊 Executive Dashboard":
        st.title(f"HR Command Center — {firm_info['name']}")
        today_str = datetime.now(IST).strftime("%Y-%m-%d")

        with engine.connect() as conn:
            tot_emp = conn.execute(text("SELECT count(*) FROM employees WHERE company_id = :cid"), {"cid": company_id}).fetchone()[0]
            punches_today = conn.execute(text("SELECT count(*) FROM daily_punches WHERE company_id = :cid AND punch_date = :dt"), {"cid": company_id, "dt": today_str}).fetchone()[0]
            punch_out_today = conn.execute(text("SELECT count(*) FROM daily_punches WHERE company_id = :cid AND punch_date = :dt AND punch_out IS NOT NULL"), {"cid": company_id, "dt": today_str}).fetchone()[0]
            pending_lv = conn.execute(text("SELECT count(*) FROM leave_requests WHERE company_id = :cid AND status = 'PENDING'"), {"cid": company_id}).fetchone()[0]

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="stat-card"><div class="stat-num">{tot_emp}</div><div class="stat-desc">Total Active Workers</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-card"><div class="stat-num">{punches_today}</div><div class="stat-desc">Present Today</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="stat-card"><div class="stat-num">{punches_today - punch_out_today}</div><div class="stat-desc">Currently On-Site</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="stat-card"><div class="stat-num">{pending_lv}</div><div class="stat-desc">Pending Leaves</div></div>', unsafe_allow_html=True)

    elif menu == "📋 Live Biometric Muster":
        st.title("Live Attendance & Geofenced Location Muster")
        dt_val = st.date_input("Muster Date", datetime.now(IST).date())
        dt_str = dt_val.strftime("%Y-%m-%d")

        with engine.connect() as conn:
            df_m = pd.read_sql(text("""
                SELECT e.emp_code as "Code", e.full_name as "Name", e.category as "Category",
                       p.punch_in as "In Time", p.punch_out as "Out Time",
                       p.in_lat as "In Lat", p.in_lon as "In Lon",
                       COALESCE(p.ot_hours, 0) as "OT (Hrs)",
                       CASE WHEN p.punch_out IS NOT NULL THEN 'COMPLETED'
                            WHEN p.punch_in IS NOT NULL THEN 'ACTIVE ON SITE'
                            ELSE 'ABSENT' END as "Status"
                FROM employees e
                LEFT JOIN daily_punches p ON e.emp_code = p.emp_code AND e.company_id = p.company_id AND p.punch_date = :dt
                WHERE e.company_id = :cid ORDER BY p.punch_in DESC NULLS LAST, e.emp_code ASC
            """), conn, params={"cid": company_id, "dt": dt_str})

        st.dataframe(df_m, use_container_width=True)
        st.download_button("📥 Export Muster (CSV)", df_m.to_csv(index=False).encode('utf-8'), f"muster_{company_id}_{dt_str}.csv", "text/csv")

    elif menu == "⏱️ OT & Hours Approval":
        st.title("Overtime (OT) Verification & Approval Engine")
        ot_dt = st.date_input("Shift Date", datetime.now(IST).date())
        ot_str = ot_dt.strftime("%Y-%m-%d")

        with engine.connect() as conn:
            df_ot = pd.read_sql(text("""
                SELECT p.id, e.emp_code, e.full_name, p.punch_in, p.punch_out, COALESCE(p.ot_hours, 0) as ot_hours
                FROM daily_punches p
                JOIN employees e ON e.emp_code = p.emp_code AND e.company_id = p.company_id
                WHERE p.company_id = :cid AND p.punch_date = :dt AND p.punch_out IS NOT NULL
            """), conn, params={"cid": company_id, "dt": ot_str})

        if df_ot.empty:
            st.info("No completed shifts on file for this date.")
        else:
            for _, r in df_ot.iterrows():
                c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
                c1.write(f"**{r['emp_code']}** - {r['full_name']}")
                c2.write(f"In: {r['punch_in']} | Out: {r['punch_out']}")
                new_ot = c3.number_input("OT Hours", 0.0, 8.0, float(r['ot_hours']), step=0.5, key=f"ot_{r['id']}")
                if c4.button("Approve OT", key=f"btn_ot_{r['id']}"):
                    with engine.connect() as conn:
                        conn.execute(text("UPDATE daily_punches SET ot_hours = :ot WHERE id = :pid"), {"ot": new_ot, "pid": r['id']})
                        conn.commit()
                    st.success(f"Updated OT for {r['emp_code']}")
                    st.rerun()

    elif menu == "📜 Appointment & Offer Letters":
        st.title("Statutory Letters & Documentation")
        with engine.connect() as conn:
            emps = conn.execute(text("SELECT emp_code, full_name, category FROM employees WHERE company_id = :cid ORDER BY emp_code"), {"cid": company_id}).fetchall()

        if emps:
            emp_map = {f"{e[0]} - {e[1]}": e for e in emps}
            sel_e = st.selectbox("Select Candidate / Employee", list(emp_map.keys()))
            ed = emp_map[sel_e]

            c1, c2 = st.columns(2)
            l_type = c1.selectbox("Document Type", ["Appointment Letter", "Offer Letter"])
            j_date = c1.date_input("Date of Joining", datetime.now(IST).date())
            desig = c2.text_input("Designation", value=ed[2] or "Technician")
            ctc_val = c2.number_input("Gross Monthly CTC (₹)", 5000.0, 300000.0, 20288.0, 500.0)

            if st.button("Generate & Download PDF", use_container_width=True):
                pdf_bytes = generate_official_letter(l_type, firm_info['name'], firm_info['address'], ed[1], ed[0], desig, str(j_date), ctc_val)
                st.download_button(f"⬇️ Download {l_type}", pdf_bytes, f"{l_type}_{ed[0]}.pdf", "application/pdf")

    elif menu == "👥 Workforce & KYC Directory":
        st.title("Workforce KYC, Bank & Profile Master")
        with engine.connect() as conn:
            df_kyc = pd.read_sql(text("""
                SELECT emp_code, full_name, mobile, uan_no, esic_no, pan_no, aadhaar_no,
                       bank_name, bank_account, bank_ifsc, blood_group, marital_status, emergency_contact
                FROM employees WHERE company_id = :cid ORDER BY emp_code ASC
            """), conn, params={"cid": company_id})
        st.dataframe(df_kyc, use_container_width=True)

    elif menu == "🏖️ Leave & Holiday Approvals":
        st.title("Leave & Comp-Off Management")
        t1, t2 = st.tabs(["Leave Requests", "Add Paid Holiday"])
        with t1:
            with engine.connect() as conn:
                df_lv = pd.read_sql(text("SELECT id, emp_code, leave_type, from_date, to_date, reason, status FROM leave_requests WHERE company_id = :cid ORDER BY id DESC"), conn, params={"cid": company_id})
            if df_lv.empty:
                st.info("No leave requests submitted.")
            else:
                for _, r in df_lv.iterrows():
                    c1, c2, c3 = st.columns([4, 2, 2])
                    c1.write(f"**{r['emp_code']}** | {r['leave_type']} ({r['from_date']} to {r['to_date']}) - Reason: {r['reason']}")
                    c1.caption(f"Status: {r['status']}")
                    if r['status'] == 'PENDING':
                        if c2.button("Approve", key=f"app_{r['id']}"):
                            with engine.connect() as conn:
                                conn.execute(text("UPDATE leave_requests SET status = 'APPROVED' WHERE id = :i"), {"i": r['id']})
                                conn.commit()
                            st.rerun()
                        if c3.button("Reject", key=f"rej_{r['id']}"):
                            with engine.connect() as conn:
                                conn.execute(text("UPDATE leave_requests SET status = 'REJECTED' WHERE id = :i"), {"i": r['id']})
                                conn.commit()
                            st.rerun()
        with t2:
            h_date = st.date_input("Holiday Date")
            h_name = st.text_input("Holiday Name", placeholder="e.g. Independence Day / Diwali")
            if st.button("Save Paid Holiday"):
                with engine.connect() as conn:
                    conn.execute(text("INSERT INTO paid_holidays (company_id, holiday_date, holiday_name) VALUES (:c, :d, :n)"), {"c": company_id, "d": str(h_date), "n": h_name})
                    conn.commit()
                st.success("Holiday registered.")

    elif menu == "💰 Monthly Wage Register":
        st.title("Wage Register (Form II) & Compliance")
        with engine.connect() as conn:
            df_w = pd.read_sql(text("""
                SELECT emp_code, month, year, rate_wages, days_worked, paid_holidays, ot_hours,
                       earned_wages, earned_ot_amt, gross_amount, ded_pf, ded_esic, ded_pt, net_wages
                FROM monthly_wages WHERE company_id = :cid ORDER BY year DESC, month DESC, emp_code ASC
            """), conn, params={"cid": company_id})
        st.dataframe(df_w, use_container_width=True)

# =====================================================================
# EMPLOYEE SELF-SERVICE VIEW
# =====================================================================
else:
    with engine.connect() as conn:
        emp_record = conn.execute(text("SELECT full_name FROM employees WHERE company_id = :cid AND emp_code = :c"), {"cid": company_id, "c": emp_code}).fetchone()
    worker_name = emp_record[0] if emp_record else "Worker"

    if menu == "📍 Punch Clock":
        st.markdown(f"""
            <div class="portal-banner">
                <span style="background:rgba(255,255,255,0.25); padding:4px 10px; border-radius:12px; font-size:12px; font-weight:700;">{firm_info['name']}</span>
                <h2 style="margin:8px 0 2px 0;">Hello, {worker_name.split()[0]}</h2>
                <p style="margin:0; font-size:13px; opacity:0.95;">Employee Code: {emp_code} | Site: Khed / Chakan</p>
            </div>
        """, unsafe_allow_html=True)

        loc = get_geolocation()
        now_ist = datetime.now(IST)
        today_str = now_ist.strftime("%Y-%m-%d")
        now_time = now_ist.strftime("%I:%M:%S %p")

        with engine.connect() as conn:
            punch = conn.execute(text("SELECT punch_in, punch_out FROM daily_punches WHERE company_id = :cid AND emp_code = :c AND punch_date = :d"), {"cid": company_id, "c": emp_code, "d": today_str}).fetchone()

        st.markdown(f"**Current IST Clock:** `{now_time}`")

        user_in_range = False
        u_lat, u_lon = None, None
        if loc and 'coords' in loc:
            u_lat = loc['coords']['latitude']
            u_lon = loc['coords']['longitude']
            dist = calculate_distance(u_lat, u_lon, firm_info['lat'], firm_info['lon'])
            if dist <= firm_info['radius']:
                user_in_range = True
                st.success(f"📍 Location Verified ({round(dist, 1)}m from site gate)")
            else:
                st.warning(f"⚠️ {round(dist, 1)}m away from workplace geofence perimeter.")
        else:
            st.info("📡 Acquiring GPS location... Please ensure GPS permission is enabled.")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("👆 Punch IN", use_container_width=True):
                if not user_in_range:
                    st.error("Cannot punch: You are outside authorized premises.")
                elif punch and punch[0]:
                    st.warning("Already punched in today.")
                else:
                    with engine.connect() as conn:
                        conn.execute(text("""
                            INSERT INTO daily_punches (company_id, emp_code, punch_date, punch_in, in_lat, in_lon)
                            VALUES (:cid, :c, :d, :tm, :lat, :lon)
                            ON CONFLICT (company_id, emp_code, punch_date) DO UPDATE SET punch_in = EXCLUDED.punch_in, in_lat = EXCLUDED.in_lat, in_lon = EXCLUDED.in_lon
                        """), {"cid": company_id, "c": emp_code, "d": today_str, "tm": now_time, "lat": u_lat, "lon": u_lon})
                        conn.commit()
                    st.success(f"Punched in successfully at {now_time}")
                    st.rerun()

        with c2:
            if st.button("👋 Punch OUT", use_container_width=True):
                if not user_in_range:
                    st.error("Cannot punch: You are outside authorized premises.")
                elif not punch or not punch[0]:
                    st.error("You must punch in first.")
                else:
                    with engine.connect() as conn:
                        conn.execute(text("""
                            UPDATE daily_punches SET punch_out = :tm, out_lat = :lat, out_lon = :lon
                            WHERE company_id = :cid AND emp_code = :c AND punch_date = :d
                        """), {"tm": now_time, "lat": u_lat, "lon": u_lon, "cid": company_id, "c": emp_code, "d": today_str})
                        conn.commit()
                    st.success(f"Punched out successfully at {now_time}")
                    st.rerun()

    elif menu == "👤 My Detailed Profile":
        st.title("My Profile & KYC Documents")
        with engine.connect() as conn:
            p = conn.execute(text("SELECT * FROM employees WHERE company_id = :cid AND emp_code = :c"), {"cid": company_id, "c": emp_code}).mappings().fetchone()

        tab_pers, tab_comp, tab_kyc, tab_docs = st.tabs(["Personal & Family", "Company & Bank", "Experience & Skills", "Upload Documents & Photo"])

        with tab_pers:
            st.write(f"**Full Name:** {p['full_name']}")
            st.write(f"**Father's / Spouse Name:** {p['father_name'] or 'N/A'}")
            st.write(f"**Gender:** {p['gender'] or 'M'}")
            bg = st.text_input("Blood Group", value=p['blood_group'] or "")
            ms = st.selectbox("Marital Status", ["Single", "Married", "Other"], index=0 if not p['marital_status'] else ["Single", "Married", "Other"].index(p['marital_status']))
            em = st.text_input("Emergency Contact Number", value=p['emergency_contact'] or "")
            fam = st.text_area("Family Details", value=p['family_details'] or "", placeholder="e.g. Spouse: Radha (9876543210), Son: Aarav")
            if st.button("Save Personal Info"):
                with engine.connect() as conn:
                    conn.execute(text("UPDATE employees SET blood_group=:bg, marital_status=:ms, emergency_contact=:em, family_details=:fam WHERE company_id=:cid AND emp_code=:c"),
                                 {"bg": bg, "ms": ms, "em": em, "fam": fam, "cid": company_id, "c": emp_code})
                    conn.commit()
                st.success("Personal profile updated.")

        with tab_comp:
            st.write(f"**Firm:** {firm_info['name']}")
            st.write(f"**Category / Designation:** {p['category'] or 'Semi-Skilled'}")
            st.write(f"**Mobile Number:** {p['mobile'] or 'N/A'}")
            st.divider()
            st.subheader("Bank & Statutory Compliance")
            st.write(f"**Bank:** {p['bank_name']} | **A/C No:** {p['bank_account']}")
            st.write(f"**IFSC:** {p['bank_ifsc']}")
            st.write(f"**UAN (EPF):** {p['uan_no'] or 'N/A'} | **ESIC No:** {p['esic_no'] or 'N/A'}")
            st.write(f"**PAN:** {p['pan_no'] or 'N/A'} | **Aadhaar:** {p['aadhaar_no'] or 'N/A'}")

        with tab_kyc:
            qual = st.text_area("Qualifications & Education", value=p['qualifications'] or "", placeholder="e.g. 10th Pass, ITI Fitter, Diploma")
            exp = st.text_area("Work Experience", value=p['work_experience'] or "", placeholder="e.g. 2 Years at Bosch Chakan as Machine Operator")
            sk = st.text_input("Skills", value=p['skills'] or "", placeholder="e.g. CNC Machine Operation, Quality Inspection, Welding")
            if st.button("Save Qualifications & Experience"):
                with engine.connect() as conn:
                    conn.execute(text("UPDATE employees SET qualifications=:q, work_experience=:w, skills=:s WHERE company_id=:cid AND emp_code=:c"),
                                 {"q": qual, "w": exp, "s": sk, "cid": company_id, "c": emp_code})
                    conn.commit()
                st.success("Experience updated.")

        with tab_docs:
            st.subheader("Document Upload (Zero Server Cost Direct Storage)")
            photo_file = st.file_uploader("Upload Profile Photo", type=["jpg", "png", "jpeg"])
            adh_file = st.file_uploader("Upload Aadhaar Card (PDF / Image)", type=["jpg", "png", "pdf"])
            pan_file = st.file_uploader("Upload PAN Card", type=["jpg", "png", "pdf"])

            if st.button("Save Uploaded Documents"):
                updates = {}
                if photo_file: updates["photo_b64"] = base64.b64encode(photo_file.read()).decode()
                if adh_file: updates["doc_aadhaar_b64"] = base64.b64encode(adh_file.read()).decode()
                if pan_file: updates["doc_pan_b64"] = base64.b64encode(pan_file.read()).decode()

                if updates:
                    set_clauses = ", ".join([f"{k} = :{k}" for k in updates.keys()])
                    updates["cid"] = company_id
                    updates["c"] = emp_code
                    with engine.connect() as conn:
                        conn.execute(text(f"UPDATE employees SET {set_clauses} WHERE company_id=:cid AND emp_code=:c"), updates)
                        conn.commit()
                    st.success("Documents securely saved.")
                else:
                    st.info("Select a file to upload.")

    elif menu == "💵 My Salary Slips":
        st.title("My Monthly Salary Slips")
        with engine.connect() as conn:
            slips = pd.read_sql(text("SELECT * FROM monthly_wages WHERE company_id = :cid AND emp_code = :c ORDER BY year DESC, month DESC"), conn, params={"cid": company_id, "c": emp_code})

        if slips.empty:
            st.info("No wage records found for your account.")
        else:
            for _, s in slips.iterrows():
                with st.expander(f"Payslip: {int(s['month']):02d}/{int(s['year'])} — Net Take Home: ₹{s['net_wages']:,.2f}", expanded=True):
                    pdf_data = generate_payslip_pdf(firm_info['name'], firm_info['address'], s, worker_name)
                    st.download_button(f"⬇️ Download Payslip ({int(s['month']):02d}/{int(s['year'])})", pdf_data, f"Payslip_{int(s['month'])}_{int(s['year'])}_{emp_code}.pdf", "application/pdf")

    elif menu == "📝 Apply Leave & Comp-Off":
        st.title("Leave & Compensatory Off Portal")
        ltype = st.selectbox("Leave Type", ["Paid Leave", "Casual Leave", "Sick Leave", "Compensatory Off"])
        c1, c2 = st.columns(2)
        d_from = c1.date_input("From Date")
        d_to = c2.date_input("To Date")
        reason = st.text_area("Reason for Leave")

        if st.button("Submit Leave Request", use_container_width=True):
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO leave_requests (company_id, emp_code, leave_type, from_date, to_date, reason)
                    VALUES (:cid, :c, :lt, :df, :dt, :r)
                """), {"cid": company_id, "c": emp_code, "lt": ltype, "df": str(d_from), "dt": str(d_to), "r": reason})
                conn.commit()
            st.success("Leave submitted for HR approval.")

    elif menu == "📜 My Official Letters":
        st.title("Appointment & Offer Documents")
        with engine.connect() as conn:
            e_cat = conn.execute(text("SELECT category FROM employees WHERE company_id = :cid AND emp_code = :c"), {"cid": company_id, "c": emp_code}).fetchone()
        desig = e_cat[0] if e_cat and e_cat[0] else "Associate"

        st.write("Download your official statutory employment letters:")
        pdf_bytes = generate_official_letter("Appointment Letter", firm_info['name'], firm_info['address'], worker_name, emp_code, desig, "2026-08-01", 20288.0)
        st.download_button("⬇️ Download Official Appointment Letter (PDF)", pdf_bytes, f"Appointment_Letter_{emp_code}.pdf", "application/pdf")