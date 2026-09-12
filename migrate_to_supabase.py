import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Passing credentials cleanly so special characters like '@' do not break the URL parser
db_url = URL.create(
    drivername="postgresql+pg8000",
    username="postgres.lsyfgompyfjborgxzxkx",
    password="Haveaniceday@2027",
    host="aws-0-ap-southeast-1.pooler.supabase.com",
    port=6543,
    database="postgres"
)

def migrate():
    print("Connecting to local SQLite database (khed_payroll.db)...")
    local_conn = sqlite3.connect("khed_payroll.db")

    print("Connecting to Supabase PostgreSQL...")
    cloud_engine = create_engine(db_url)

    with cloud_engine.connect() as conn:
        # 1. Company Tenant Master Record
        print("Ensuring GEMSHINE tenant exists in Supabase...")
        conn.execute(
            text("""
                INSERT INTO companies (id, company_name, address, contractor_name)
                VALUES ('GEMSHINE', 'GEMSHINE MULTISERVICES', 'SEZ, Khed City, Maharashtra', 'GEMSHINE MULTISERVICES')
                ON CONFLICT (id) DO NOTHING;
            """)
        )
        conn.commit()

        # 2. Migrate Employees
        print("\nReading employees from SQLite...")
        df_emp = pd.read_sql("SELECT * FROM employees", local_conn)
        df_emp["company_id"] = "GEMSHINE"
        df_emp = df_emp.where(pd.notnull(df_emp), None)

        print(f"Uploading {len(df_emp)} employee records to Supabase...")
        for _, row in df_emp.iterrows():
            conn.execute(
                text("""
                    INSERT INTO employees (
                        company_id, emp_code, full_name, father_name,
                        uan_no, esic_no, pan_no, aadhaar_no, gender,
                        bank_name, bank_account, bank_ifsc, mobile, category
                    ) VALUES (
                        :company_id, :emp_code, :full_name, :father_name,
                        :uan_no, :esic_no, :pan_no, :aadhaar_no, :gender,
                        :bank_name, :bank_account, :bank_ifsc, :mobile, :category
                    )
                    ON CONFLICT (company_id, emp_code) DO UPDATE SET
                        full_name = EXCLUDED.full_name,
                        father_name = EXCLUDED.father_name,
                        uan_no = EXCLUDED.uan_no,
                        esic_no = EXCLUDED.esic_no,
                        pan_no = EXCLUDED.pan_no,
                        aadhaar_no = EXCLUDED.aadhaar_no,
                        gender = EXCLUDED.gender,
                        bank_name = EXCLUDED.bank_name,
                        bank_account = EXCLUDED.bank_account,
                        bank_ifsc = EXCLUDED.bank_ifsc,
                        mobile = EXCLUDED.mobile,
                        category = EXCLUDED.category;
                """),
                row.to_dict(),
            )
        conn.commit()
        print(f"✓ Successfully synced {len(df_emp)} employees.")

        # 3. Migrate User Accounts (Passwords / Roles)
        print("\nReading user accounts from SQLite...")
        df_users = pd.read_sql("SELECT * FROM user_accounts", local_conn)
        df_users["company_id"] = "GEMSHINE"
        df_users = df_users.where(pd.notnull(df_users), None)

        print(f"Uploading {len(df_users)} user login accounts...")
        for _, row in df_users.iterrows():
            conn.execute(
                text("""
                    INSERT INTO user_accounts (company_id, emp_code, password_hash, role)
                    VALUES (:company_id, :emp_code, :password_hash, :role)
                    ON CONFLICT (company_id, emp_code) DO UPDATE SET
                        password_hash = EXCLUDED.password_hash,
                        role = EXCLUDED.role;
                """),
                row.to_dict(),
            )
        conn.commit()
        print(f"✓ Successfully synced {len(df_users)} user accounts.")

        # 4. Migrate Monthly Wages (Payslips)
        print("\nReading monthly wages from SQLite...")
        df_wages = pd.read_sql("SELECT * FROM monthly_wages", local_conn)
        if "id" in df_wages.columns:
            df_wages = df_wages.drop(columns=["id"])
        df_wages["company_id"] = "GEMSHINE"
        df_wages = df_wages.where(pd.notnull(df_wages), None)

        print(f"Uploading {len(df_wages)} wage records...")
        for _, row in df_wages.iterrows():
            conn.execute(
                text("""
                    INSERT INTO monthly_wages (
                        company_id, emp_code, month, year,
                        rate_basic, rate_da, rate_hra, rate_wages, rate_ot,
                        days_worked, paid_holidays, total_days, ot_hours,
                        earned_basic, earned_da, earned_hra, earned_wages, earned_ot_amt,
                        gross_amount, ded_pf, ded_esic, ded_pt, ded_mlwf, ded_advance,
                        total_deduction, net_wages, er_pf, er_esic, service_charge,
                        sub_total, gst_18, ctc_total
                    ) VALUES (
                        :company_id, :emp_code, :month, :year,
                        :rate_basic, :rate_da, :rate_hra, :rate_wages, :rate_ot,
                        :days_worked, :paid_holidays, :total_days, :ot_hours,
                        :earned_basic, :earned_da, :earned_hra, :earned_wages, :earned_ot_amt,
                        :gross_amount, :ded_pf, :ded_esic, :ded_pt, :ded_mlwf, :ded_advance,
                        :total_deduction, :net_wages, :er_pf, :er_esic, :service_charge,
                        :sub_total, :gst_18, :ctc_total
                    )
                    ON CONFLICT (company_id, emp_code, month, year) DO NOTHING;
                """),
                row.to_dict(),
            )
        conn.commit()
        print(f"✓ Successfully synced {len(df_wages)} wage slips.")

    local_conn.close()
    print("\n=======================================================")
    print("SUCCESS: All employee, account, and wage data is live in Supabase!")
    print("=======================================================\n")

if __name__ == "__main__":
    migrate()