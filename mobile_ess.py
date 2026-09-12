import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import hashlib
from streamlit_js_eval import get_geolocation

st.set_page_config(
    page_title="DAS SAGAR HRMS - ESS",
    page_icon="🏢",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom Styling matching OpportuneHR mobile theme
st.markdown("""
<style>
    .stApp {
        background-color: #F8F9FB;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .mobile-header {
        background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%);
        padding: 20px 18px;
        border-radius: 0px 0px 24px 24px;
        color: white;
        box-shadow: 0 4px 15px rgba(247, 147, 30, 0.25);
        margin-bottom: 20px;
    }
    .header-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .emp-tag {
        background: rgba(255, 255, 255, 0.2);
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .welcome-title {
        font-size: 24px;
        font-weight: 700;
        margin-top: 14px;
        margin-bottom: 2px;
    }
    .welcome-subtitle {
        font-size: 13px;
        opacity: 0.9;
    }
    .ui-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        margin-bottom: 16px;
        border: 1px solid #ECEEF2;
    }
    .section-heading {
        font-size: 15px;
        font-weight: 700;
        color: #2D3748;
        margin-bottom: 12px;
    }
    .att-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #F0F2F5;
        font-size: 13px;
    }
    .att-date { font-weight: 700; color: #FF6B35; }
    .att-time { color: #4A5568; }
    .att-badge-p { background: #E6F4EA; color: #137333; padding: 2px 8px; border-radius: 8px; font-weight: 600; }
    .att-badge-cl { background: #FEF7E0; color: #B06000; padding: 2px 8px; border-radius: 8px; font-weight: 600; }
    .loc-text {
        text-align: center;
        font-size: 12px;
        color: #718096;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

def get_db():
    conn = sqlite3.connect('khed_payroll.db')
    conn.row_factory = sqlite3.Row
    return conn

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['emp_code'] = None

# --- LOGIN SCREEN ---
if not st.session_state['logged_in']:
    st.markdown("""
        <div style="text-align: center; margin-top: 40px; margin-bottom: 25px;">
            <div style="font-size: 38px; color: #FF6B35;">❖</div>
            <h2 style="color: #2D3748; margin-bottom: 0;">DAS SAGAR ESS</h2>
            <p style="color: #718096; font-size: 14px;">Self Service Mobile Portal</p>
        </div>
    """, unsafe_allow_html=True)

    with st.container():
        emp_input = st.text_input("Employee Code", placeholder="e.g. 001, 002").strip().upper()
        pwd_input = st.text_input("Password", type="password", placeholder="EmpCode@123")
        
        if st.button("Sign In", use_container_width=True):
            conn = get_db()
            cur = conn.cursor()
            hashed = hashlib.sha256(pwd_input.encode()).hexdigest()
            cur.execute("SELECT emp_code, role FROM user_accounts WHERE emp_code = ? AND password_hash = ?", (emp_input, hashed))
            user = cur.fetchone()
            conn.close()

            if user:
                st.session_state['logged_in'] = True
                st.session_state['emp_code'] = user['emp_code']
                st.rerun()
            else:
                st.error("Invalid credentials. Default: YourEmpCode@123")
    st.stop()

# Load Employee Record
emp_code = st.session_state['emp_code']
conn = get_db()
cur = conn.cursor()
cur.execute("SELECT * FROM employees WHERE emp_code = ?", (emp_code,))
emp = cur.fetchone()

# Navigation Drawer
with st.sidebar:
    st.markdown(f"""
        <div style="padding: 10px 0; border-bottom: 1px solid #eee; margin-bottom: 15px;">
            <h3 style="color: #FF6B35; margin: 0;">❖ DAS SAGAR</h3>
            <p style="color: #666; font-size: 12px; margin: 0;">We Make HR Easy • Khed City</p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🏠 Home", use_container_width=True):
        st.session_state['page'] = "Home"

    with st.expander("🔗 My Links", expanded=False):
        sub_link = st.radio("My Links Menu", [
            "My Salary Slip", "My CTC", "Investment Declaration"
        ], label_visibility="collapsed")
        if st.button("Open Selected Link", key="btn_links"):
            st.session_state['page'] = sub_link

    with st.expander("👤 My Profile", expanded=False):
        sub_profile = st.radio("Profile Menu", [
            "Personal Info", "Bank Account Details"
        ], label_visibility="collapsed")
        if st.button("View Profile Detail", key="btn_profile"):
            st.session_state['page'] = sub_profile

    with st.expander("📅 My Attendance", expanded=False):
        sub_att = st.radio("Attendance Menu", [
            "Punch Clock", "Leave Ledger"
        ], label_visibility="collapsed")
        if st.button("View Attendance", key="btn_att"):
            st.session_state['page'] = sub_att

    with st.expander("📝 Request", expanded=False):
        sub_req = st.radio("Request Menu", [
            "Leave / WFH Request", "Bank Account Change"
        ], label_visibility="collapsed")
        if st.button("Go to Request", key="btn_req"):
            st.session_state['page'] = sub_req

    with st.expander("🧾 My Claims", expanded=False):
        sub_claim = st.radio("Claims Menu", [
            "Expense Claim"
        ], label_visibility="collapsed")
        if st.button("Open Claims", key="btn_claim"):
            st.session_state['page'] = sub_claim

    st.divider()
    if st.button("Log Out", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['emp_code'] = None
        st.rerun()

current_page = st.session_state.get('page', "Home")

# View: Home
if current_page == "Home":
    emp_name = emp['full_name'] if emp else "Employee"
    st.markdown(f"""
        <div class="mobile-header">
            <div class="header-top">
                <span class="emp-tag">{emp_code}</span>
                <span style="font-size: 18px;">🔔</span>
            </div>
            <div class="welcome-title">Hey, {emp_name.split()[0]}</div>
            <div class="welcome-subtitle">Hope you are doing Great.</div>
        </div>
    """, unsafe_allow_html=True)

    # Biometric Punch Card
    st.markdown('<div class="ui-card" style="text-align: center;">', unsafe_allow_html=True)
    today_str = str(date.today())
    now_time = datetime.now().strftime("%I:%M:%S %p")

    cur.execute("SELECT * FROM daily_punches WHERE emp_code = ? AND punch_date = ?", (emp_code, today_str))
    today_punch = cur.fetchone()

    status_tag = '<span style="color: #EA4335; font-weight: 600;">○ Not Punched In</span>'
    if today_punch:
        if today_punch['punch_out']:
            status_tag = '<span style="color: #34A853; font-weight: 600;">● Shift Completed</span>'
        elif today_punch['punch_in']:
            status_tag = '<span style="color: #34A853; font-weight: 600;">● Punched In</span>'

    st.markdown(f"<p style='color:#718096; font-size:13px; margin:0;'>Current Time</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:18px; font-weight:700; color:#2D3748; margin:4px 0;'>{now_time}</p>", unsafe_allow_html=True)
    st.markdown(status_tag, unsafe_allow_html=True)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("👆 Punch IN", use_container_width=True):
            if today_punch and today_punch['punch_in']:
                st.warning("Already punched in today.")
            else:
                cur.execute("INSERT OR REPLACE INTO daily_punches (emp_code, punch_date, punch_in) VALUES (?, ?, ?)", (emp_code, today_str, now_time))
                conn.commit()
                st.rerun()
    with col_btn2:
        if st.button("👋 Punch OUT", use_container_width=True):
            if not today_punch or not today_punch['punch_in']:
                st.error("Punch in first.")
            else:
                cur.execute("UPDATE daily_punches SET punch_out = ? WHERE emp_code = ? AND punch_date = ?", (now_time, emp_code, today_str))
                conn.commit()
                st.rerun()

    st.markdown('<p class="loc-text">📍 SEZ, Khed City, Maharashtra, 410505, India</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Attendance Snapshot
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-heading">My Attendance</div>', unsafe_allow_html=True)
    cur.execute("SELECT punch_date, punch_in, punch_out FROM daily_punches WHERE emp_code = ? ORDER BY punch_date DESC LIMIT 3", (emp_code,))
    recent_punches = cur.fetchall()
    if recent_punches:
        for p in recent_punches:
            st.markdown(f"""
                <div class="att-row">
                    <span class="att-date">{p['punch_date']}</span>
                    <span class="att-time">{p['punch_in'] or '--'} / {p['punch_out'] or '--'}</span>
                    <span class="att-badge-p">P</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No punch records yet.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Action Cards
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-heading">Self Service</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📄 Salary Slip", use_container_width=True):
            st.session_state['page'] = "My Salary Slip"
            st.rerun()
    with c2:
        if st.button("📝 Apply Leave", use_container_width=True):
            st.session_state['page'] = "Leave / WFH Request"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# View: My Salary Slip
elif current_page == "My Salary Slip":
    st.title("My Salary Slips")
    cur.execute("SELECT * FROM monthly_wages WHERE emp_code = ? ORDER BY year DESC, month DESC", (emp_code,))
    slips = cur.fetchall()

    if not slips:
        st.info("No wage records found.")
    else:
        for s in slips:
            with st.expander(f"Payslip: {s['month']:02d}/{s['year']} — Net: ₹{s['net_wages']:,.2f}", expanded=True):
                col_e, col_d = st.columns(2)
                with col_e:
                    st.write("**Earnings**")
                    st.write(f"Earned Basic: ₹{s['earned_basic']:,.2f}")
                    st.write(f"Earned DA: ₹{s['earned_da']:,.2f}")
                    st.write(f"Earned HRA: ₹{s['earned_hra']:,.2f}")
                    st.write(f"Overtime: ₹{s['earned_ot_amt']:,.2f}")
                    st.write(f"**Gross:** ₹{s['gross_amount']:,.2f}")
                with col_d:
                    st.write("**Deductions**")
                    st.write(f"PF (12%): ₹{s['ded_pf']:,.2f}")
                    st.write(f"ESIC (0.75%): ₹{s['ded_esic']:,.2f}")
                    st.write(f"Prof. Tax: ₹{s['ded_pt']:,.2f}")
                    st.write(f"Advance: ₹{s['ded_advance']:,.2f}")
                    st.write(f"**Total Ded:** ₹{s['total_deduction']:,.2f}")

# View: Profile
elif current_page in ["Personal Info", "Bank Account Details"]:
    st.title("My Profile")
    if emp:
        st.write(f"**Full Name:** {emp['full_name']}")
        st.write(f"**Father Name:** {emp['father_name']}")
        st.write(f"**Designation / Category:** {emp['category']}")
        st.write(f"**Aadhaar:** {emp['aadhaar_no'] or 'N/A'}")
        st.write(f"**PAN:** {emp['pan_no'] or 'N/A'}")
        st.divider()
        st.subheader("Bank Details")
        st.write(f"**Bank Name:** {emp['bank_name']}")
        st.write(f"**Account Number:** {emp['bank_account']}")
        st.write(f"**IFSC Code:** {emp['bank_ifsc']}")
    else:
        st.info("No profile information available.")

# View: Leave Request
elif current_page == "Leave / WFH Request":
    st.title("Apply Leave / WFH")
    l_type = st.selectbox("Type", ["Casual Leave (CL)", "Sick Leave (SL)", "Work From Home (WFH)"])
    d_from = st.date_input("From Date")
    d_to = st.date_input("To Date")
    reason = st.text_area("Reason")
    if st.button("Submit Request", use_container_width=True):
        cur.execute("INSERT INTO leave_requests (emp_code, leave_type, from_date, to_date, reason) VALUES (?, ?, ?, ?, ?)",
                    (emp_code, l_type, str(d_from), str(d_to), reason))
        conn.commit()
        st.success("Request submitted to HR successfully!")

conn.close()