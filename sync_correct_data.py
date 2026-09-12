import openpyxl
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

db_url = URL.create(
    drivername="postgresql+pg8000",
    username="postgres.lsyfgompyfjborgxzxkx",
    password="Haveaniceday@2027",
    host="aws-0-ap-southeast-1.pooler.supabase.com",
    port=6543,
    database="postgres"
)

def fix_data():
    engine = create_engine(db_url)
    wb = openpyxl.load_workbook("wages_aug_2026.xlsx", data_only=True)
    ws = wb.active

    print("Re-aligning columns for SAGAR ENTERPRISES...")
    with engine.connect() as conn:
        for r in range(6, 150):
            emp_val = ws.cell(row=r, column=2).value
            if not emp_val or "total" in str(emp_val).lower():
                continue
            
            emp_code = str(emp_val).strip()

            def c_str(c):
                v = ws.cell(row=r, column=c).value
                return "" if v is None or str(v).strip() == "0" else str(v).strip()

            params = {
                "cid": "SAGAR",
                "c": emp_code,
                "name": c_str(3),
                "father": c_str(4),
                "uan": c_str(5),
                "esic": c_str(6),
                "pan": c_str(7),
                "adh": c_str(8),
                "gender": c_str(9) or "M",
                "doj": c_str(10),
                "dob": c_str(11),
                "bank": c_str(12),
                "ac": c_str(13),
                "ifsc": c_str(14),
                "mob": c_str(15),
                "cat": c_str(16)
            }

            conn.execute(text("""
                UPDATE employees 
                SET full_name = :name,
                    father_name = :father,
                    uan_no = :uan,
                    esic_no = :esic,
                    pan_no = :pan,
                    aadhaar_no = :adh,
                    gender = :gender,
                    bank_name = :bank,
                    bank_account = :ac,
                    bank_ifsc = :ifsc,
                    mobile = :mob,
                    category = :cat
                WHERE company_id = :cid AND emp_code = :c
            """), params)

        conn.commit()
    print("✓ Successfully corrected all column mappings in Supabase!")

if __name__ == "__main__":
    fix_data()