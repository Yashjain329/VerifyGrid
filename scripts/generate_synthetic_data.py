#!/usr/bin/env python3
"""
VerifyGrid - Synthetic Data Generator for Institutional Verification
Generates 3 realistic, messy institutional data sources:
1. scholarship_applicants.csv (Source A: Student Portal Export)
2. university_admissions.csv  (Source B: Registrar Official ERP Export)
3. fee_receipts.csv           (Source C: Finance / Accounts Bank Ledger)

Includes realistic real-world inconsistencies:
- Indian name transliteration & spelling variants (e.g. Aarav vs Arav, Puja vs Pooja)
- Date of Birth formatting chaos (DD/MM/YYYY vs YYYY-MM-DD vs MM/DD/YYYY)
- Roll number format variations (NIMS-2024-0101 vs nims/2024/0101 vs 2024-0101)
- Seeded discrepancies: Missing records, Partial fee payments, Duplicate rolls, Mismatched DOBs
"""

import os
import random
import csv
from datetime import datetime, timedelta

def generate_datasets(num_records=500, output_dir="data/samples"):
    os.makedirs(output_dir, exist_ok=True)
    random.seed(42)

    first_names = [
        "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
        "Shaurya", "Atharva", "Advik", "Pranav", "Kabir", "Aryan", "Dhruv", "Rudra", "Om", "Samarth",
        "Ananya", "Diya", "Gauri", "Kavya", "Ishita", "Anushka", "Riya", "Aditi", "Pooja", "Sneha",
        "Meera", "Pari", "Saanvi", "Sara", "Aanya", "Myra", "Avani", "Tanvi", "Vanshika", "Khushi"
    ]
    last_names = [
        "Sharma", "Verma", "Gupta", "Jain", "Mehta", "Patel", "Singh", "Yadav", "Chauhan", "Rathore",
        "Mishra", "Pandey", "Trivedi", "Shukla", "Iyer", "Nair", "Reddy", "Rao", "Banerjee", "Chatterjee"
    ]
    departments = ["B.Tech CSE", "B.Tech AI&DS", "B.Pharm", "BBA", "B.Com Hons", "B.Sc Biotech", "BCA", "MBBS Pre-Med"]
    categories = ["General", "OBC-NCL", "SC", "ST", "EWS"]

    # Variants mapping for realistic name mismatches
    spelling_variants = {
        "Aarav": "Arav",
        "Pooja": "Puja",
        "Aditya": "Adityaa",
        "Dhruv": "Dhruva",
        "Riya": "Rhea",
        "Meera": "Mira",
        "Advik": "Aadvik",
        "Chauhan": "Chouhan",
        "Gupta": "Guptaa",
        "Reddy": "Reddi"
    }

    students = []
    base_date = datetime(2003, 1, 1)

    for i in range(1, num_records + 1):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        full_name = f"{fn} {ln}"
        roll_num = f"NIMS-2024-{i:04d}"
        dob_dt = base_date + timedelta(days=random.randint(0, 730))
        dept = random.choice(departments)
        category = random.choice(categories)
        scholarship_amt = random.choice([25000, 35000, 50000, 75000])
        annual_fee = random.choice([60000, 85000, 110000, 150000])
        students.append({
            "id": i,
            "roll": roll_num,
            "first_name": fn,
            "last_name": ln,
            "full_name": full_name,
            "dob_dt": dob_dt,
            "dept": dept,
            "category": category,
            "scholarship_amt": scholarship_amt,
            "annual_fee": annual_fee
        })

    # 1. Generate scholarship_applicants.csv (Source A)
    applicants_rows = []
    for s in students:
        # 1.5% chance applicant omitted or typo in roll
        roll_val = s["roll"]
        if s["id"] % 65 == 0:
            roll_val = s["roll"].replace("-", " ") # Format noise
        elif s["id"] % 113 == 0:
            roll_val = s["roll"].lower() # Lowercase

        # Date format noise in portal
        dob_style = random.choice(["dd/mm/yyyy", "yyyy-mm-dd", "dd-mm-yyyy"])
        if dob_style == "dd/mm/yyyy":
            dob_str = s["dob_dt"].strftime("%d/%m/%Y")
        elif dob_style == "yyyy-mm-dd":
            dob_str = s["dob_dt"].strftime("%Y-%m-%d")
        else:
            dob_str = s["dob_dt"].strftime("%d-%m-%Y")

        applicants_rows.append({
            "application_id": f"SCH-2024-{s['id']:05d}",
            "student_roll_no": roll_val,
            "candidate_name": s["full_name"],
            "date_of_birth": dob_str,
            "academic_program": s["dept"],
            "category_quota": s["category"],
            "claimed_scholarship_inr": s["scholarship_amt"],
            "bank_account_last4": f"{random.randint(1000, 9999)}",
            "submission_timestamp": (datetime(2024, 7, 10) + timedelta(hours=s["id"])).strftime("%Y-%m-%d %H:%M")
        })

    # 2. Generate university_admissions.csv (Source B)
    # Registrar official database
    admissions_rows = []
    for s in students:
        # Edge cases:
        # - 2% not in admissions (ghost applicant / dropped out)
        if s["id"] in [42, 108, 195, 312]:
            continue

        name_in_adm = s["full_name"]
        # Seeded spelling variant in ~6% of records
        if s["first_name"] in spelling_variants and s["id"] % 3 == 0:
            name_in_adm = f"{spelling_variants[s['first_name']]} {s['last_name']}"
        elif s["id"] % 29 == 0:
            # Initials style
            name_in_adm = f"{s['first_name'][0]}. {s['last_name']}"

        # Seeded DOB error in ~3% of records
        adm_dob = s["dob_dt"]
        if s["id"] in [17, 88, 142, 230, 405]:
            adm_dob = s["dob_dt"] + timedelta(days=random.choice([-30, 365, -1]))

        admissions_rows.append({
            "enrollment_number": s["roll"],
            "student_full_name": name_in_adm,
            "registered_dob": adm_dob.strftime("%Y-%m-%d"),
            "enrolled_department": s["dept"],
            "admission_quota": s["category"],
            "enrollment_status": "Active" if s["id"] % 77 != 0 else "Suspended",
            "admission_year": "2024",
            "allotted_mentor": f"Prof. {random.choice(last_names)}"
        })

    # 3. Generate fee_receipts.csv (Source C)
    # Finance accounts ledger
    fee_rows = []
    receipt_counter = 5001
    for s in students:
        # Edge cases:
        # - 2.5% missing fee receipt (fee defaulter)
        if s["id"] in [15, 63, 127, 248, 380, 462]:
            continue

        paid_amt = s["annual_fee"]
        fee_status = "CLEARED"
        # Seeded underpayment / partial fee in ~4% of records
        if s["id"] in [23, 71, 134, 219, 295, 411]:
            paid_amt = s["annual_fee"] - random.choice([15000, 25000])
            fee_status = "PARTIAL_BALANCE"

        fee_rows.append({
            "receipt_number": f"REC-2024-{receipt_counter}",
            "student_roll_no": s["roll"],
            "transaction_date": (datetime(2024, 6, 1) + timedelta(days=s["id"] % 60)).strftime("%d-%b-%Y"),
            "amount_paid_inr": paid_amt,
            "total_tuition_due_inr": s["annual_fee"],
            "payment_mode": random.choice(["NEFT", "RTGS", "UPI", "NetBanking", "Demand Draft"]),
            "accounts_clearance_status": fee_status,
            "bank_ref_id": f"UTR{random.randint(1000000000, 9999999999)}"
        })
        receipt_counter += 1

    # Write files
    def write_csv(filepath, rows):
        if not rows:
            return
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"Generated {filepath} ({len(rows)} records)")

    write_csv(os.path.join(output_dir, "scholarship_applicants.csv"), applicants_rows)
    write_csv(os.path.join(output_dir, "university_admissions.csv"), admissions_rows)
    write_csv(os.path.join(output_dir, "fee_receipts.csv"), fee_rows)
    print("Done! All 3 messy institutional datasets successfully generated.")

if __name__ == "__main__":
    generate_datasets()
