import sqlite3

def upgrade_schema():
    conn = sqlite3.connect('khed_payroll.db')
    cur = conn.cursor()

    # 1. Client Company Sites
    cur.execute('''
    CREATE TABLE IF NOT EXISTS client_sites (
        site_id TEXT PRIMARY KEY,
        client_name TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        radius_meters REAL DEFAULT 60.0
    )''')

    # 2. Shift Timings Master
    cur.execute('''
    CREATE TABLE IF NOT EXISTS shift_masters (
        shift_id TEXT PRIMARY KEY,
        shift_name TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL
    )''')

    # 3. Employee Deployment Mapping
    cur.execute('''
    CREATE TABLE IF NOT EXISTS employee_deployments (
        emp_code TEXT PRIMARY KEY,
        site_id TEXT REFERENCES client_sites(site_id),
        shift_id TEXT REFERENCES shift_masters(shift_id),
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Insert default client sites (replace coordinates with your real sites)
    cur.execute('''
    INSERT OR REPLACE INTO client_sites (site_id, client_name, latitude, longitude, radius_meters)
    VALUES 
        ('SITE_KHED_01', 'Khed City Industrial Plant', 18.843600, 73.918900, 75.0),
        ('SITE_CHAKAN_01', 'Chakan MIDC Facility', 18.760600, 73.863600, 75.0),
        ('SITE_HQ', 'Gemshine Multiservices Head Office', 18.850000, 73.920000, 50.0)
    ''')

    # Insert standard industrial shifts
    cur.execute('''
    INSERT OR REPLACE INTO shift_masters (shift_id, shift_name, start_time, end_time)
    VALUES 
        ('SHIFT_GEN', 'General Shift (09:00 AM - 06:00 PM)', '09:00', '18:00'),
        ('SHIFT_A', 'Shift A / Morning (06:00 AM - 02:30 PM)', '06:00', '14:30'),
        ('SHIFT_B', 'Shift B / Afternoon (02:30 PM - 11:00 PM)', '14:30', '23:00'),
        ('SHIFT_C', 'Shift C / Night (11:00 PM - 07:00 AM)', '23:00', '07:00')
    ''')

    # Assign all existing employees to default site & shift if unassigned
    cur.execute('''
    INSERT OR IGNORE INTO employee_deployments (emp_code, site_id, shift_id)
    SELECT emp_code, 'SITE_KHED_01', 'SHIFT_GEN' FROM employees
    ''')

    conn.commit()
    conn.close()
    print("Deployment schema and initial site data created successfully!")

if __name__ == '__main__':
    upgrade_schema()