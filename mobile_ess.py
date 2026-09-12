import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, time
import hashlib
import pytz
import math
from streamlit_js_eval import get_geolocation

IST = pytz.timezone('Asia/Kolkata')

st.set_page_config(
    page_title="GEMSHINE MULTISERVICES - HRMS",
    page_icon="🏢",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Helper: Haversine distance formula
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2.0)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

# Custom CSS
st.markdown("""
<style>
    .stApp { background-color: #F8F9FB; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .mobile-header {
        background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%);
        padding: 20px 18px;
        border-radius: 0px 0px 24px 24px;
        color: white;
        box-shadow: 0 4px 15px rgba(247, 147, 30, 0.25);
        margin-bottom: 20px;
    }
    .emp-tag { background: rgba(255, 255, 255, 0.2); padding: 4px 10px; border-radius: 12px; font-size: 13px; font-weight: 600; }
    .welcome-title { font-size: 22px; font-weight: 700; margin-top: 10px; margin-bottom: 2px; }
    .welcome-subtitle { font-size: 12px; opacity: 0.95; }
    .ui-card { background: #FFFFFF; border-radius: 16px; padding: 16px; box-shadow: 0 2px 10px rgba(0,0,0,0.04); margin-bottom: 16px; border: 1px solid #ECEEF2; }
    .section-heading { font-size: 15px; font-weight: 700; color: #2D3748; margin-bottom: 12px; }
    .att-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #F0F2F5; font-size: 13px; }
    .att-date { font-weight: 700; color: #FF6B35; }
    .loc-text { text-align: center; font-size: 12px; color: #718096; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

def get_db():
    conn = sqlite3.connect('khed_payroll.db')
    conn.row_factory = sqlite3.Row
    return conn

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['emp_code'] = None
    st.session_state['role'] = 'employee'

# --- LOGIN ---
if not st.session_state['logged_in']:
    st.markdown("""
        <div style="text-align: center; margin-top: 40px; margin-bottom: 25px;">
            <div style="font-size: 38px; color: #FF6B35;">❖</div>
            <h2 style="color: #2D3748; margin-bottom: 0;">GEMSHINE MULTISERVICES</h2>
            <p style="color: #718096; font-size: 14px;">Workforce Management & ESS Portal</p>
        </div>
    """, unsafe_allow_html=True)

    emp_input = st.text_input("Employee / Admin Code", placeholder="e.g. 001 or ADMIN").strip().upper()
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
            st.session_state['role'] = user['role']
            st.rerun()
        else:
            st.error("Invalid credentials.")
    st.stop()

emp_code = st.session_state['emp_code']
is_admin = (st.session_state['role'] == 'admin')

# Navigation
with st.sidebar:
    st.markdown("""
        <div style="padding: 10px 0; border-bottom: 1px solid #eee; margin-bottom: 15px;">
            <h3 style="color: #FF6B35; margin: 0;">❖ GEMSHINE</h3>
            <p style="color: #666; font-size: 12px; margin: 0;">Labour Contractor Management</p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🏠 Home / Punch Clock", use_container_width=True):
        st.session_state['page'] = "Home"

    if is_admin:
        st.markdown("**Admin Controls**")
        if st.button("📍 Manage Deployments & Shifts", use_container_width=True):
            st.session_state['page'] = "Deployments"
        if st.button("🏢 Add / Edit Client Sites", use_container_width=True):
            st.session_state['page'] = "Sites"

    with st.expander("👤 Employee Self Service", expanded=False):
        sub_page = st.radio("Menu", ["My Salary Slip", "My Profile", "Apply Leave"], label_visibility="collapsed")
        if st.button("Open Selected", key="btn_sub"):
            st.session_state['page'] = sub_page

    st.divider()
    if st.button("Log Out", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['emp_code'] = None
        st.rerun()

current_page = st.session_state.get('page', "Home")

# --- ADMIN VIEW 1: MANAGE EMPLOYEE DEPLOYMENTS ---
if current_page == "Deployments" and is_admin:
    st.title("Worker Site & Shift Deployment")
    conn = get_db()
    
    employees_df = pd.read_sql_query("SELECT emp_code, full_name FROM employees ORDER BY emp_code", conn)
    sites_df = pd.read_sql_query("SELECT site_id, client_name FROM client_sites", conn)
    shifts_df = pd.read_sql_query("SELECT shift_id, shift_name FROM shift_masters", conn)

    cur = conn.cursor()
    emp_options = [f"{r['emp_code']} - {r['full_name']}" for _, r in employees_df.iterrows()]
    selected_emp_raw = st.selectbox("Select Worker to Assign / Change", emp_options)
    target_emp_code = selected_emp_raw.split(" - ")[0]

    # Fetch current assignment
    cur.execute("""
        SELECT d.site_id, d.shift_id, s.client_name, sh.shift_name 
        FROM employee_deployments d
        LEFT JOIN client_sites s ON d.site_id = s.site_id
        LEFT JOIN shift_masters sh ON d.shift_id = sh.shift_id
        WHERE d.emp_code = ?
    """, (target_emp_code,))
    curr_deploy = cur.fetchone()

    if curr_deploy:
        st.info(f"**Current Site:** {curr_deploy['client_name']} | **Current Shift:** {curr_deploy['shift_name']}")

    with st.form("reassign_form"):
        site_choice = st.selectbox("Assign Client Company / Work Site", sites_df['client_name'].tolist())
        shift_choice = st.selectbox("Assign Shift", shifts_df['shift_name'].tolist())
        submit_reassign = st.form_submit_button("Update Worker Deployment", use_container_width=True)

        if submit_reassign:
            target_site_id = sites_df[sites_df['client_name'] == site_choice]['site_id'].values[0]
            target_shift_id = shifts_df[shifts_df['shift_name'] == shift_choice]['shift_id'].values[0]

            cur.execute("""
                INSERT OR REPLACE INTO employee_deployments (emp_code, site_id, shift_id, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (target_emp_code, target_site_id, target_shift_id))
            conn.commit()
            st.success(f"Updated {target_emp_code} to {site_choice} under {shift_choice}!")
            st.rerun()

    st.subheader("All Worker Allocations")
    all_deploy_df = pd.read_sql_query("""
        SELECT e.emp_code as [Code], e.full_name as [Worker Name], s.client_name as [Company / Site], sh.shift_name as [Shift]
        FROM employees e
        LEFT JOIN employee_deployments d ON e.emp_code = d.emp_code
        LEFT JOIN client_sites s ON d.site_id = s.site_id
        LEFT JOIN shift_masters sh ON d.shift_id = sh.shift_id
        ORDER BY e.emp_code
    """, conn)
    st.dataframe(all_deploy_df, use_container_width=True, hide_index=True)
    conn.close()

# --- ADMIN VIEW 2: ADD / EDIT CLIENT SITES & GEOFENCES ---
elif current_page == "Sites" and is_admin:
    st.title("Client Company Sites & Geofences")
    conn = get_db()
    cur = conn.cursor()

    with st.expander("➕ Register New Client Company / Work Site", expanded=True):
        with st.form("new_site_form"):
            c_name = st.text_input("Client / Company Name (e.g. Tata Motors Chakan)")
            c_id = "SITE_" + c_name.upper().replace(" ", "_")[:12]
            c_lat = st.number_input("Factory Latitude (e.g. 18.843600)", format="%.6f", value=18.843600)
            c_lon = st.number_input("Factory Longitude (e.g. 73.918900)", format="%.6f", value=73.918900)
            c_rad = st.slider("Geofence Radius (Meters)", min_value=25, max_value=250, value=75, step=5)
            if st.form_submit_button("Save Client Site"):
                if c_name:
                    cur.execute("INSERT OR REPLACE INTO client_sites (site_id, client_name, latitude, longitude, radius_meters) VALUES (?, ?, ?, ?, ?)",
                                (c_id, c_name, c_lat, c_lon, float(c_rad)))
                    conn.commit()
                    st.success(f"Site '{c_name}' registered!")
                    st.rerun()

    st.subheader("Existing Work Locations")
    sites_list = pd.read_sql_query("SELECT client_name, latitude, longitude, radius_meters FROM client_sites", conn)
    st.dataframe(sites_list, use_container_width=True, hide_index=True)
    conn.close()

# --- WORKER HOME: DYNAMIC GEOFENCING BASED ON ASSIGNED SITE ---
elif current_page == "Home":
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT e.full_name, s.client_name, s.latitude, s.longitude, s.radius_meters, sh.shift_name, sh.start_time, sh.end_time
        FROM employees e
        LEFT JOIN employee_deployments d ON e.emp_code = d.emp_code
        LEFT JOIN client_sites s ON d.site_id = s.site_id
        LEFT JOIN shift_masters sh ON d.shift_id = sh.shift_id
        WHERE e.emp_code = ?
    """, (emp_code,))
    info = cur.fetchone()

    worker_name = info['full_name'] if info else "Gemshine Worker"
    assigned_company = info['client_name'] if info and info['client_name'] else "Main Depot"
    target_lat = info['latitude'] if info and info['latitude'] else 18.843600
    target_lon = info['longitude'] if info and info['longitude'] else 73.918900
    allowed_radius = info['radius_meters'] if info and info['radius_meters'] else 75.0
    shift_label = info['shift_name'] if info and info['shift_name'] else "General Shift"

    st.markdown(f"""
        <div class="mobile-header">
            <div class="header-top">
                <span class="emp-tag">{emp_code}</span>
                <span style="font-size: 18px;">🔔</span>
            </div>
            <div class="welcome-title">Hey, {worker_name.split()[0]}</div>
            <div class="welcome-subtitle">📍 Deployed at: <b>{assigned_company}</b></div>
            <div class="welcome-subtitle">🕒 Shift: <b>{shift_label}</b></div>
        </div>
    """, unsafe_allow_html=True)

    loc = get_geolocation()
    st.markdown('<div class="ui-card" style="text-align: center;">', unsafe_allow_html=True)

    now_ist = datetime.now(IST)
    today_str = now_ist.strftime("%Y-%m-%d")
    now_time = now_ist.strftime("%I:%M:%S %p")

    cur.execute("SELECT * FROM daily_punches WHERE emp_code = ? AND punch_date = ?", (emp_code, today_str))
    today_punch = cur.fetchone()

    status_tag = '<span style="color: #EA4335; font-weight: 600;">○ Not Punched In</span>'
    if today_punch:
        if today_punch['punch_out']:
            status_tag = '<span style="color: #34A853; font-weight: 600;">● Shift Completed</span>'
        elif today_punch['punch_in']:
            status_tag = '<span style="color: #34A853; font-weight: 600;">● Punched In</span>'

    st.markdown("<p style='color:#718096; font-size:13px; margin:0;'>Live Clock (IST)</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:22px; font-weight:700; color:#2D3748; margin:4px 0;'>{now_time}</p>", unsafe_allow_html=True)
    st.markdown(status_tag, unsafe_allow_html=True)

    # Dynamic distance verification against the worker's specific assigned site
    user_in_range = False
    if loc and 'coords' in loc:
        u_lat = loc['coords']['latitude']
        u_lon = loc['coords']['longitude']
        dist_meters = calculate_distance(u_lat, u_lon, target_lat, target_lon)
        if dist_meters <= allowed_radius:
            user_in_range = True
            st.success(f"📍 Location Verified ({round(dist_meters, 1)}m from {assigned_company} gate)")
        else:
            st.warning(f"⚠️ You are {round(dist_meters, 1)}m away from {assigned_company}. Must be within {int(allowed_radius)}m.")
    else:
        st.info("📡 Fetching GPS... Please allow location access on your phone.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("👆 Punch IN", use_container_width=True):
            if not user_in_range:
                st.error(f"Cannot punch in: Outside {assigned_company} boundary.")
            elif today_punch and today_punch['punch_in']:
                st.warning("Already punched in today.")
            else:
                cur.execute("INSERT OR REPLACE INTO daily_punches (emp_code, punch_date, punch_in) VALUES (?, ?, ?)", (emp_code, today_str, now_time))
                conn.commit()
                st.success(f"Punched in at {now_time}")
                st.rerun()

    with col2:
        if st.button("👋 Punch OUT", use_container_width=True):
            if not user_in_range:
                st.error(f"Cannot punch out: Outside {assigned_company} boundary.")
            elif not today_punch or not today_punch['punch_in']:
                st.error("Punch in first.")
            else:
                cur.execute("UPDATE daily_punches SET punch_out = ? WHERE emp_code = ? AND punch_date = ?", (now_time, emp_code, today_str))
                conn.commit()
                st.success(f"Punched out at {now_time}")
                st.rerun()

    st.markdown(f'<p class="loc-text">Authorized Workplace: {assigned_company}</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    conn.close()

# --- OTHER PAGES ---
elif current_page == "My Salary Slip":
    st.title("My Salary Slips")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM monthly_wages WHERE emp_code = ? ORDER BY year DESC, month DESC", (emp_code,))
    slips = cur.fetchall()
    conn.close()
    if not slips:
        st.info("No wage records found.")
    else:
        for s in slips:
            with st.expander(f"Payslip: {s['month']:02d}/{s['year']} — Net: ₹{s['net_wages']:,.2f}", expanded=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"Earned Basic: ₹{s['earned_basic']:,.2f}")
                    st.write(f"Earned DA: ₹{s['earned_da']:,.2f}")
                    st.write(f"Earned HRA: ₹{s['earned_hra']:,.2f}")
                    st.write(f"**Gross:** ₹{s['gross_amount']:,.2f}")
                with c2:
                    st.write(f"PF: ₹{s['ded_pf']:,.2f}")
                    st.write(f"ESIC: ₹{s['ded_esic']:,.2f}")
                    st.write(f"Prof. Tax: ₹{s['ded_pt']:,.2f}")
                    st.write(f"**Net:** ₹{s['net_wages']:,.2f}")

elif current_page == "My Profile":
    st.title("My Profile")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM employees WHERE emp_code = ?", (emp_code,))
    emp = cur.fetchone()
    conn.close()
    if emp:
        st.write(f"**Worker Name:** {emp['full_name']}")
        st.write(f"**Father Name:** {emp['father_name']}")
        st.write(f"**Category:** {emp['category']}")
        st.write(f"**Bank:** {emp['bank_name']} ({emp['bank_account']})")
        st.write(f"**IFSC:** {emp['bank_ifsc']}")

elif current_page == "Apply Leave":
    st.title("Apply Leave / Time Off")
    l_type = st.selectbox("Leave Type", ["Casual Leave", "Sick Leave", "Emergency"])
    d_from = st.date_input("From Date")
    d_to = st.date_input("To Date")
    reason = st.text_area("Reason")
    if st.button("Submit to Admin", use_container_width=True):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO leave_requests (emp_code, leave_type, from_date, to_date, reason) VALUES (?, ?, ?, ?, ?)",
                    (emp_code, l_type, str(d_from), str(d_to), reason))
        conn.commit()
        conn.close()
        st.success("Leave submitted for approval.")