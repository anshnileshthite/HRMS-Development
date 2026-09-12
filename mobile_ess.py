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
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern OpportuneHR theme styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #F8F9FB; }
    .portal-banner {
        background: linear-gradient(135deg, #FF6B35 0%, #F58220 100%);
        padding: 20px;
        border-radius: 16px;
        color: white;
        margin-bottom: 20px;
    }
    .stat-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #ECEEF2;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }
    .stat-num { font-size: 26px; font-weight: 700; color: #FF6B35; }
    .stat-desc { font-size: 11px; color: #64748B; text-transform: uppercase; font-weight: 600; }
    .att-table { background: white; border-radius: 12px; padding: 14px; border: 1px solid #ECEEF2; }
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

# --- DETAILED STATUTORY PAYSLIP GENERATOR ---
def generate_detailed_payslip_pdf(comp_name, comp_addr, s, emp):
    buf = io.BytesIO()
    p = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    # Header
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

    # Employee Metadata Box
    p.setFont("Helvetica-Bold", 9)
    p.drawString(40, h - 105, f"Employee Name: {emp.get('full_name', 'N/A')}")
    p.drawString(220, h - 105, f"Employee ID: {s['emp_code']}")
    p.drawString(400, h - 105, f"Designation: {emp.get('category', 'Technician')}")

    p.setFont("Helvetica", 9)
    doj_str = str(emp.get('date_of_joining', '2026-08-01'))
    p.drawString(40, h - 122, f"Date of Joining: {doj_str}")
    p.drawString(220, h - 122, f"Total Month Days: {s.get('total_days', 31)}")
    p.drawString(400, h - 122, f"Present Days: {s.get('days_worked', 0)}")

    p.drawString(40, h - 139, f"Bank Name: {emp.get('bank_name', 'N/A')}")
    p.drawString(220, h - 139, f"Account No: {emp.get('bank_account', 'N/A')}")
    p.drawString(400, h - 139, f"IFSC Code: {emp.get('bank_ifsc', 'N/A')}")

    p.drawString(40, h - 156, f"UAN No: {emp.get('uan_no', 'N/A')}")
    p.drawString(220, h - 156, f"PAN No: {emp.get('pan_no', 'N/A')}")
    p.drawString(400, h - 156, f"Aadhaar: {emp.get('aadhaar_no', 'N/A')}")

    p.drawString(40, h - 173, f"OT Hours Worked: {s.get('ot_hours', 0)}")

    # Earnings & Deductions Grid
    p.rect(35, h - 295, w - 70, 110)
    p.line(w / 2.0, h - 185, w / 2.0, h - 295)
    p.setFillColor(colors.HexColor("#F1F5F9"))
    p.rect(35, h - 200, w - 70, 15, fill=1, stroke=0)
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 9)
    p.drawString(45, h - 196, "EARNINGS")
    p.drawRightString(w / 2.0 - 15, h - 196, "AMOUNT (Rs.)")
    p.drawString(w / 2.0 + 15, h - 196, "DEDUCTIONS")
    p.drawRightString(w - 45, h - 196, "AMOUNT (Rs.)")

    p.setFont("Helvetica", 9)
    # Earnings items
    p.drawString(45, h - 215, "Basic Wages:")
    p.drawRightString(w / 2.0 - 15, h - 215, f"{float(s.get('earned_basic') or 0):,.2f}")
    p.drawString(45, h - 230, "Dearness Allowance (DA):")
    p.drawRightString(w / 2.0 - 15, h - 230, f"{float(s.get('earned_da') or 0):,.2f}")
    p.drawString(45, h - 245, "House Rent Allowance (HRA):")
    p.drawRightString(w / 2.0 - 15, h - 245, f"{float(s.get('earned_hra') or 0):,.2f}")
    p.drawString(45, h - 260, "Overtime Amount:")
    p.drawRightString(w / 2.0 - 15, h - 260, f"{float(s.get('earned_ot_amt') or 0):,.2f}")

    # Deductions items
    p.drawString(w / 2.0 + 15, h - 215, "Provident Fund (EPF):")
    p.drawRightString(w - 45, h - 215, f"{float(s.get('ded_pf') or 0):,.2f}")
    p.drawString(w / 2.0 + 15, h - 230, "ESIC Deduction:")
    p.drawRightString(w - 45, h - 230, f"{float(s.get('ded_esic') or 0):,.2f}")
    p.drawString(w / 2.0 + 15, h - 245, "Professional Tax (PT):")
    p.drawRightString(w - 45, h - 245, f"{float(s.get('ded_pt') or 0):,.2f}")
    p.drawString(w / 2.0 + 15, h - 260, "Salary Advance / Other:")
    p.drawRightString(w - 45, h - 260, f"{float(s.get('ded_advance') or 0):,.2f}")

    # Subtotals line
    p.line(35, h - 275, w - 35, h - 275)
    p.setFont("Helvetica-Bold", 9)
    p.drawString(45, h - 288, "GROSS EARNINGS:")
    p.drawRightString(w / 2.0 - 15, h - 288, f"Rs. {float(s.get('gross_amount') or 0):,.2f}")
    p.drawString(w / 2.0 + 15, h - 288, "TOTAL DEDUCTIONS:")
    p.drawRightString(w - 45, h - 288, f"Rs. {float(s.get('total_deduction') or 0):,.2f}")

    # Net Salary Banner
    p.setFillColor(colors.HexColor("#059669"))
    p.rect(35, h - 335, w - 70, 30, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(w / 2.0, h - 323, f"NET TAKE HOME PAYABLE: Rs. {float(s.get('net_wages') or 0):,.2f}")

    # Footer note
    p.setFillColor(colors.HexColor("#64748B"))
    p.setFont("Helvetica-Oblique", 8)
    p.drawCentredString(w / 2.0, h - 355, "This is a computer-generated salary slip and does not require a physical signature.")

    p.showPage()
    p.save()
    buf.seek(0)
    return buf.getvalue()

# --- OFFER LETTER GENERATOR ---
def generate_offer_letter_pdf(comp_name, comp_addr, emp_name, emp_code, designation, doj, ctc):
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
    p.drawCentredString(w / 2.0, h - 110, "OFFICIAL OFFER OF EMPLOYMENT")

    p.setFont("Helvetica", 10)
    p.drawString(40, h - 140, f"Date: {doj}")
    p.drawString(40, h - 158, f"To: {emp_name} (Candidate ID: {emp_code})")

    lines = [
        f"Dear {emp_name},",
        f"",
        f"We are pleased to offer you employment with {comp_name} as '{designation}'.",
        f"Your employment begins on {doj}. Below are the primary terms of your engagement:",
        f"",
        f"1. Position: {designation}",
        f"2. Gross Monthly CTC: Rs. {ctc:,.2f}/- subject to statutory PF, ESIC, and PT deductions.",
        f"3. Work Location: Industrial manufacturing premises (SEZ Khed / Chakan MIDC).",
        f"4. Shift Operations: Industrial roster rotation (General / A / B / C shifts).",
        f"5. Statutory Benefits: Full coverage under Employees' Provident Fund and ESIC Act.",
        f"",
        f"This offer letter is generated once at the time of joining.",
        f"Welcome aboard!",
        f"",
        f"For {comp_name}",
        f"Authorized HR Signatory"
    ]
    y = h - 190
    for l in lines:
        p.drawString(40, y, l)
        y -= 17

    p.drawString(w - 230, h - 490, "Candidate Signature: ________________")
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
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("""
            <div style="text-align:center; margin-top:35px; margin-bottom:20px;">
                <div style="font-size:42px; color:#FF6B35;">❖</div>
                <h1 style="color:#1E293B; margin:0;">ESS PORTAL</h1>
                <p style="color:#64748B; font-size:14px;">Multi-Firm Workforce Management</p>
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

# Safe Employee Lookup
with engine.connect() as conn:
    res = conn.execute(
        text("SELECT * FROM employees WHERE company_id = :cid AND emp_code = :c"),
        {"cid": company_id, "c": emp_code}
    )
    r = res.mappings().fetchone()
    emp_data = dict(r) if r else {}

worker_name = emp_data.get("full_name", "Employee")

# ==========================================
# SIDEBAR DRAWER NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown(f"### ❖ {firm_info['name']}")
    st.caption(f"Tenant: `{company_id}` | User: `{emp_code}` ({st.session_state['role'].upper()})")
    st.divider()

    if is_admin:
        menu = st.radio("HR Administration", [
            "📊 Dashboard",
            "📋 Live Attendance Muster",
            "⏱️ OT & Hours Approval",
            "📤 Upload Offer Letter & ESIC",
            "👥 Employee Directory & Edit",
            "💰 Wage Register"
        ])
    else:
        menu = st.radio("Self Service Menu", [
            "🏠 Home Dashboard",
            "👤 My Profile",
            "💵 Salary Slips",
            "📅 Full Attendance History",
            "📂 My Documents (ESIC & Offer Letter)",
            "📝 Leave Request"
        ])

    st.divider()
    if st.button("Log Out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# =====================================================================
# EMPLOYER / ADMIN PORTAL
# =====================================================================
if is_admin:
    if menu == "📊 Dashboard":
        st.title(f"HR Command Center — {firm_info['name']}")
        today_str = datetime.now(IST).strftime("%Y-%m-%d")

        with engine.connect() as conn:
            tot_emp = conn.execute(text("SELECT count(*) FROM employees WHERE company_id = :cid"), {"cid": company_id}).fetchone()[0]
            punches_today = conn.execute(text("SELECT count(*) FROM daily_punches WHERE company_id = :cid AND punch_date = :dt"), {"cid": company_id, "dt": today_str}).fetchone()[0]
            punch_out_today = conn.execute(text("SELECT count(*) FROM daily_punches WHERE company_id = :cid AND punch_date = :dt AND punch_out IS NOT NULL"), {"cid": company_id, "dt": today_str}).fetchone()[0]

        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="stat-card"><div class="stat-num">{tot_emp}</div><div class="stat-desc">Total Workers</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="stat-card"><div class="stat-num">{punches_today}</div><div class="stat-desc">Present Today</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="stat-card"><div class="stat-num">{punches_today - punch_out_today}</div><div class="stat-desc">Currently On-Site</div></div>', unsafe_allow_html=True)

    elif menu == "📋 Live Attendance Muster":
        st.title("Attendance Muster")
        dt_val = st.date_input("Muster Date", datetime.now(IST).date())
        dt_str = dt_val.strftime("%Y-%m-%d")

        with engine.connect() as conn:
            df_m = pd.read_sql(text("""
                SELECT e.emp_code as "Code", e.full_name as "Name", e.category as "Category",
                       p.punch_in as "In Time", p.punch_out as "Out Time",
                       COALESCE(p.ot_hours, 0) as "OT (Hrs)",
                       CASE WHEN p.punch_out IS NOT NULL THEN 'COMPLETED'
                            WHEN p.punch_in IS NOT NULL THEN 'ON SITE'
                            ELSE 'ABSENT' END as "Status"
                FROM employees e
                LEFT JOIN daily_punches p ON e.emp_code = p.emp_code AND e.company_id = p.company_id AND p.punch_date = :dt
                WHERE e.company_id = :cid ORDER BY p.punch_in DESC NULLS LAST, e.emp_code ASC
            """), conn, params={"cid": company_id, "dt": dt_str})

        st.dataframe(df_m, use_container_width=True)
        st.download_button("📥 Export Muster (CSV)", df_m.to_csv(index=False).encode('utf-8'), f"muster_{company_id}_{dt_str}.csv", "text/csv")

    elif menu == "⏱️ OT & Hours Approval":
        st.title("Overtime (OT) Approval Engine")
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

    elif menu == "📤 Upload Offer Letter & ESIC":
        st.title("Admin Document Upload (Offer Letters & ESIC Cards)")
        st.caption("Upload signed Offer Letters or statutory ESIC Cards directly to employee profiles.")

        with engine.connect() as conn:
            emp_list = conn.execute(text("SELECT emp_code, full_name FROM employees WHERE company_id = :cid ORDER BY emp_code"), {"cid": company_id}).fetchall()

        if not emp_list:
            st.warning("No employees available.")
        else:
            emp_options = {f"{e[0]} - {e[1]}": e[0] for e in emp_list}
            chosen_label = st.selectbox("Select Employee", list(emp_options.keys()))
            chosen_code = emp_options[chosen_label]

            tab_up_offer, tab_up_esic, tab_gen = st.tabs(["Upload Signed Offer Letter", "Upload ESIC Card", "Generate Joining Offer Letter (Once)"])

            with tab_up_offer:
                offer_file = st.file_uploader("Upload Signed Offer Letter (PDF / Image)", type=["pdf", "png", "jpg"], key="up_offer")
                if offer_file and st.button("Save Offer Letter to Portal"):
                    b64_str = base64.b64encode(offer_file.read()).decode()
                    with engine.connect() as conn:
                        conn.execute(text("UPDATE employees SET doc_offer_letter_b64 = :b WHERE company_id = :cid AND emp_code = :c"), {"b": b64_str, "cid": company_id, "c": chosen_code})
                        conn.commit()
                    st.success(f"Offer Letter uploaded for {chosen_code}!")

            with tab_up_esic:
                esic_file = st.file_uploader("Upload ESIC Pehchan Card (PDF / Image)", type=["pdf", "png", "jpg"], key="up_esic")
                if esic_file and st.button("Save ESIC Card to Portal"):
                    b64_str = base64.b64encode(esic_file.read()).decode()
                    with engine.connect() as conn:
                        conn.execute(text("UPDATE employees SET doc_esic_b64 = :b WHERE company_id = :cid AND emp_code = :c"), {"b": b64_str, "cid": company_id, "c": chosen_code})
                        conn.commit()
                    st.success(f"ESIC Card uploaded for {chosen_code}!")

            with tab_gen:
                with engine.connect() as conn:
                    chk = conn.execute(text("SELECT offer_letter_generated, full_name, category, date_of_joining FROM employees WHERE company_id = :cid AND emp_code = :c"),
                                       {"cid": company_id, "c": chosen_code}).fetchone()
                if chk and chk[0]:
                    st.warning("⚠️ Offer Letter has ALREADY been generated once for this employee upon joining. Regeneration is locked.")
                else:
                    st.write(f"Candidate: **{chk[1]}** | Joining Date: **{chk[3]}**")
                    ctc_input = st.number_input("Gross Monthly CTC (₹)", 5000.0, 200000.0, 20288.0, 500.0)
                    if st.button("Generate & Issue Official Offer Letter", use_container_width=True):
                        pdf_data = generate_offer_letter_pdf(firm_info['name'], firm_info['address'], chk[1], chosen_code, chk[2] or "Technician", str(chk[3]), ctc_input)
                        b64_pdf = base64.b64encode(pdf_data).decode()
                        with engine.connect() as conn:
                            conn.execute(text("""
                                UPDATE employees 
                                SET doc_offer_letter_b64 = :b, offer_letter_generated = TRUE 
                                WHERE company_id = :cid AND emp_code = :c
                            """), {"b": b64_pdf, "cid": company_id, "c": chosen_code})
                            conn.commit()
                        st.success("Offer Letter successfully generated and locked!")
                        st.rerun()

    elif menu == "👥 Employee Directory & Edit":
        st.title("Workforce Master (Replace & Update Details)")
        with engine.connect() as conn:
            df_dir = pd.read_sql(text("""
                SELECT emp_code, full_name, category, date_of_joining, mobile,
                       bank_name, bank_account, bank_ifsc, uan_no, esic_no, pan_no, aadhaar_no
                FROM employees WHERE company_id = :cid ORDER BY emp_code ASC
            """), conn, params={"cid": company_id})

        st.dataframe(df_dir, use_container_width=True)

        st.subheader("Edit / Replace Details for an Employee")
        e_edit = st.selectbox("Select Employee to Edit", df_dir['emp_code'].tolist())
        curr = df_dir[df_dir['emp_code'] == e_edit].iloc[0]

        c1, c2 = st.columns(2)
        n_name = c1.text_input("Full Name", value=curr['full_name'])
        n_desig = c2.text_input("Designation / Category", value=curr['category'] or "Semi-Skilled")
        n_bank = c1.text_input("Bank Name", value=curr['bank_name'] or "")
        n_ac = c2.text_input("Bank Account Number", value=curr['bank_account'] or "")
        n_ifsc = c1.text_input("IFSC Code", value=curr['bank_ifsc'] or "")
        n_uan = c2.text_input("UAN Number", value=curr['uan_no'] or "")
        n_pan = c1.text_input("PAN Number", value=curr['pan_no'] or "")
        n_adh = c2.text_input("Aadhaar Number", value=curr['aadhaar_no'] or "")

        if st.button("Save Updated Details", use_container_width=True):
            with engine.connect() as conn:
                conn.execute(text("""
                    UPDATE employees 
                    SET full_name = :nm, category = :cat, bank_name = :bnk, bank_account = :ac,
                        bank_ifsc = :ifsc, uan_no = :uan, pan_no = :pan, aadhaar_no = :adh
                    WHERE company_id = :cid AND emp_code = :c
                """), {"nm": n_name, "cat": n_desig, "bnk": n_bank, "ac": n_ac, "ifsc": n_ifsc, "uan": n_uan, "pan": n_pan, "adh": n_adh, "cid": company_id, "c": e_edit})
                conn.commit()
            st.success(f"Profile records updated for {e_edit}!")
            st.rerun()

    elif menu == "💰 Wage Register":
        st.title("Wage Register (Form II)")
        with engine.connect() as conn:
            df_w = pd.read_sql(text("""
                SELECT emp_code, month, year, rate_wages, days_worked, ot_hours,
                       earned_wages, gross_amount, ded_pf, ded_esic, ded_pt, net_wages
                FROM monthly_wages WHERE company_id = :cid ORDER BY year DESC, month DESC, emp_code ASC
            """), conn, params={"cid": company_id})
        st.dataframe(df_w, use_container_width=True)

# =====================================================================
# EMPLOYEE PORTAL
# =====================================================================
else:
    # 1. HOME DASHBOARD
    if menu == "🏠 Home Dashboard":
        st.markdown(f"""
            <div class="portal-banner">
                <div style="font-size:11px; font-weight:700; background:rgba(255,255,255,0.25); display:inline-block; padding:3px 8px; border-radius:8px;">{firm_info['name']}</div>
                <h2 style="margin:8px 0 2px 0;">{worker_name} ({emp_code})</h2>
                <p style="margin:0; font-size:13px; opacity:0.95;">Designation: {emp_data.get('category', 'Technician')}</p>
            </div>
        """, unsafe_allow_html=True)

        today_str = datetime.now(IST).strftime("%Y-%m-%d")
        with engine.connect() as conn:
            p_today = conn.execute(
                text("SELECT punch_in, punch_out, ot_hours FROM daily_punches WHERE company_id = :cid AND emp_code = :c AND punch_date = :d"),
                {"cid": company_id, "c": emp_code, "d": today_str}
            ).fetchone()

        in_t = p_today[0] if p_today and p_today[0] else "--:--"
        out_t = p_today[1] if p_today and p_today[1] else "--:--"
        st_txt = "P" if (p_today and p_today[0]) else "A"

        st.markdown(f"""
            <div class="att-table">
                <div style="font-size:15px; font-weight:700; color:#1E293B; margin-bottom:8px;">Today's Attendance</div>
                <div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; text-align:center;">
                    <div><div style="font-size:10px; color:#64748B;">DATE</div><b>{datetime.now(IST).strftime('%d %b')}</b></div>
                    <div><div style="font-size:10px; color:#64748B;">IN</div><b>{in_t}</b></div>
                    <div><div style="font-size:10px; color:#64748B;">OUT</div><b>{out_t}</b></div>
                    <div><div style="font-size:10px; color:#64748B;">STATUS</div><b style="color:{'#10B981' if st_txt=='P' else '#EF4444'}">{st_txt}</b></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        loc = get_geolocation()
        user_in_range = False
        u_lat, u_lon = None, None
        if loc and 'coords' in loc:
            u_lat = loc['coords']['latitude']
            u_lon = loc['coords']['longitude']
            dist = calculate_distance(u_lat, u_lon, firm_info['lat'], firm_info['lon'])
            if dist <= firm_info['radius']:
                user_in_range = True
                st.success(f"📍 Location Verified ({round(dist, 1)}m from site)")
            else:
                st.warning(f"⚠️ {round(dist, 1)}m away from workplace.")
        else:
            st.info("📡 Acquiring GPS location...")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("👆 Punch IN", use_container_width=True):
                if not user_in_range:
                    st.error("Outside premises.")
                elif p_today and p_today[0]:
                    st.warning("Already punched in.")
                else:
                    now_str = datetime.now(IST).strftime("%I:%M %p")
                    with engine.connect() as conn:
                        conn.execute(text("""
                            INSERT INTO daily_punches (company_id, emp_code, punch_date, punch_in, in_lat, in_lon)
                            VALUES (:cid, :c, :d, :tm, :lat, :lon)
                            ON CONFLICT (company_id, emp_code, punch_date) DO UPDATE SET punch_in = EXCLUDED.punch_in, in_lat = EXCLUDED.in_lat, in_lon = EXCLUDED.in_lon
                        """), {"cid": company_id, "c": emp_code, "d": today_str, "tm": now_str, "lat": u_lat, "lon": u_lon})
                        conn.commit()
                    st.success("Punched in successfully!")
                    st.rerun()

        with c2:
            if st.button("👋 Punch OUT", use_container_width=True):
                if not user_in_range:
                    st.error("Outside premises.")
                elif not p_today or not p_today[0]:
                    st.error("Punch in first.")
                else:
                    now_str = datetime.now(IST).strftime("%I:%M %p")
                    with engine.connect() as conn:
                        conn.execute(text("""
                            UPDATE daily_punches SET punch_out = :tm, out_lat = :lat, out_lon = :lon
                            WHERE company_id = :cid AND emp_code = :c AND punch_date = :d
                        """), {"tm": now_str, "lat": u_lat, "lon": u_lon, "cid": company_id, "c": emp_code, "d": today_str})
                        conn.commit()
                    st.success("Punched out successfully!")
                    st.rerun()

    # 2. MY PROFILE
    elif menu == "👤 My Profile":
        st.title("My Profile & Employment Details")
        st.write("Below are your verified records in the organization:")

        c1, c2 = st.columns(2)
        c1.markdown(f"**Employee Name:** {emp_data.get('full_name', 'N/A')}")
        c1.markdown(f"**Employee ID:** `{emp_code}`")
        c1.markdown(f"**Designation / Category:** {emp_data.get('category', 'Technician')}")
        c1.markdown(f"**Date of Joining:** {emp_data.get('date_of_joining', '2026-08-01')}")

        c2.markdown(f"**Bank Name:** {emp_data.get('bank_name', 'N/A')}")
        c2.markdown(f"**Bank Account Number:** {emp_data.get('bank_account', 'N/A')}")
        c2.markdown(f"**IFSC Code:** {emp_data.get('bank_ifsc', 'N/A')}")
        c2.markdown(f"**UAN (PF Number):** {emp_data.get('uan_no', 'N/A')}")

        st.divider()
        st.markdown(f"**PAN Number:** {emp_data.get('pan_no', 'N/A')} | **Aadhaar Number:** {emp_data.get('aadhaar_no', 'N/A')}")

    # 3. SALARY SLIPS (AUTOMATIC 15th OF THE MONTH VISIBILITY)
    elif menu == "💵 Salary Slips":
        st.title("My Salary Slips")
        current_now = datetime.now(IST)

        with engine.connect() as conn:
            all_slips = pd.read_sql(
                text("SELECT * FROM monthly_wages WHERE company_id = :cid AND emp_code = :c ORDER BY year DESC, month DESC"),
                conn,
                params={"cid": company_id, "c": emp_code}
            )

        if all_slips.empty:
            st.info("No salary slips found.")
        else:
            visible_slips = []
            for _, s in all_slips.iterrows():
                # Automatic 15th rule: Slip of Month M / Year Y is released on the 15th of Month M+1
                slip_m = int(s['month'])
                slip_y = int(s['year'])
                release_m = 1 if slip_m == 12 else slip_m + 1
                release_y = slip_y + 1 if slip_m == 12 else slip_y
                release_date = date(release_y, release_m, 15)

                if current_now.date() >= release_date:
                    visible_slips.append(s)

            if not visible_slips:
                st.info("Your upcoming salary slip will automatically reflect in your app on the 15th of the month.")
            else:
                for s in visible_slips:
                    with st.expander(f"Payslip: {int(s['month']):02d}/{int(s['year'])} — Net Take Home: ₹{s['net_wages']:,.2f}", expanded=True):
                        c1, c2 = st.columns(2)
                        c1.write(f"**Gross Salary:** ₹{s['gross_amount']:,.2f}")
                        c1.write(f"Days Worked: {s['days_worked']} | OT Hours: {s.get('ot_hours', 0)}")
                        c2.write(f"**Total Deductions:** ₹{s['total_deduction']:,.2f}")
                        c2.write(f"**Net Wages:** ₹{s['net_wages']:,.2f}")

                        pdf_data = generate_detailed_payslip_pdf(firm_info['name'], firm_info['address'], s, emp_data)
                        st.download_button(
                            label=f"📥 Download Payslip ({int(s['month']):02d}/{int(s['year'])})",
                            data=pdf_data,
                            file_name=f"Payslip_{int(s['month'])}_{int(s['year'])}_{emp_code}.pdf",
                            mime="application/pdf",
                            key=f"btn_dl_{s['id']}"
                        )

    # 4. FULL ATTENDANCE HISTORY (DAILY, MONTHLY, YEARLY)
    elif menu == "📅 Full Attendance History":
        st.title("My Complete Attendance History")
        t_daily, t_monthly, t_yearly = st.tabs(["Daily History", "Monthly Summary", "Yearly Attendance"])

        with t_daily:
            with engine.connect() as conn:
                df_daily = pd.read_sql(text("""
                    SELECT punch_date as "Date", punch_in as "In Time", punch_out as "Out Time",
                           ot_hours as "OT (Hrs)", punch_status as "Status"
                    FROM daily_punches 
                    WHERE company_id = :cid AND emp_code = :c 
                    ORDER BY punch_date DESC
                """), conn, params={"cid": company_id, "c": emp_code})
            st.dataframe(df_daily, use_container_width=True)

        with t_monthly:
            with engine.connect() as conn:
                df_m_sum = pd.read_sql(text("""
                    SELECT SUBSTRING(punch_date, 1, 7) as "Month",
                           count(*) as "Total Punches",
                           SUM(COALESCE(ot_hours, 0)) as "Total OT Hours"
                    FROM daily_punches 
                    WHERE company_id = :cid AND emp_code = :c 
                    GROUP BY SUBSTRING(punch_date, 1, 7)
                    ORDER BY "Month" DESC
                """), conn, params={"cid": company_id, "c": emp_code})
            st.dataframe(df_m_sum, use_container_width=True)

        with t_yearly:
            with engine.connect() as conn:
                df_y_sum = pd.read_sql(text("""
                    SELECT SUBSTRING(punch_date, 1, 4) as "Year",
                           count(*) as "Total Present Days",
                           SUM(COALESCE(ot_hours, 0)) as "Total OT Hours"
                    FROM daily_punches 
                    WHERE company_id = :cid AND emp_code = :c 
                    GROUP BY SUBSTRING(punch_date, 1, 4)
                    ORDER BY "Year" DESC
                """), conn, params={"cid": company_id, "c": emp_code})
            st.dataframe(df_y_sum, use_container_width=True)

    # 5. MY DOCUMENTS (OFFER LETTER & ESIC CARD)
    elif menu == "📂 My Documents (ESIC & Offer Letter)":
        st.title("My Official Documents")
        st.caption("Access and download official documents uploaded or issued by HR.")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Official Offer Letter")
            if emp_data.get("doc_offer_letter_b64"):
                offer_bytes = base64.b64decode(emp_data["doc_offer_letter_b64"])
                st.success("✓ Offer Letter issued and verified.")
                st.download_button("⬇️ Download Offer Letter", offer_bytes, f"Offer_Letter_{emp_code}.pdf", "application/pdf")
            else:
                st.info("Offer letter has not been uploaded or issued yet.")

        with col2:
            st.subheader("ESIC Pehchan Card")
            if emp_data.get("doc_esic_b64"):
                esic_bytes = base64.b64decode(emp_data["doc_esic_b64"])
                st.success("✓ ESIC Card available.")
                st.download_button("⬇️ Download ESIC Card", esic_bytes, f"ESIC_Card_{emp_code}.pdf", "application/pdf")
            else:
                st.info("ESIC Card will be available once uploaded by HR.")

    # 6. LEAVE REQUEST
    elif menu == "📝 Leave Request":
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