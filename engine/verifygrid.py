#!/usr/bin/env python3
"""
VerifyGrid - Deterministic Institutional Verification Engine
Author: Yash Jain & VerifyGrid Team

Core Principle:
"Machines do the matching. Humans only judge the exceptions. Every decision leaves a trail."

Executes approved deterministic rules across multi-source institutional records.
Zero external dependencies required (uses standard library difflib, csv, json, datetime).
"""

import os
import sys
import csv
import json
import re
from datetime import datetime
from difflib import SequenceMatcher

def normalize_roll(val):
    if not val:
        return ""
    # Remove hyphens, slashes, spaces, lowercase
    return re.sub(r'[^a-zA-Z0-9]', '', str(val)).upper()

def parse_date(date_str):
    if not date_str:
        return None
    date_str = str(date_str).strip()
    formats = [
        "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y",
        "%d-%b-%Y", "%d %b %Y", "%Y/%m/%d"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

def normalize_name(name):
    if not name:
        return ""
    name = str(name).strip().lower()
    # Strip titles
    for title in ["mr.", "ms.", "mrs.", "dr.", "prof."]:
        if name.startswith(title):
            name = name[len(title):].strip()
    # Collapse whitespace
    name = re.sub(r'\s+', ' ', name)
    return name

def name_similarity(name1, name2):
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)
    if not n1 or not n2:
        return 0.0
    if n1 == n2:
        return 1.0
    return SequenceMatcher(None, n1, n2).ratio()

class VerifyGridEngine:
    def __init__(self, fuzzy_threshold_pass=0.92, fuzzy_threshold_review=0.75):
        self.fuzzy_pass = fuzzy_threshold_pass
        self.fuzzy_review = fuzzy_threshold_review

    def run_verification(self, applicants_file, admissions_file, fees_file):
        # 1. Load Applicants (Source A)
        with open(applicants_file, "r", encoding="utf-8") as f:
            applicants = list(csv.DictReader(f))

        # 2. Index Admissions (Source B) by normalized roll
        admissions_map = {}
        with open(admissions_file, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = normalize_roll(row.get("enrollment_number", ""))
                if key:
                    admissions_map[key] = row

        # 3. Index Fees (Source C) by normalized roll
        fees_map = {}
        with open(fees_file, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = normalize_roll(row.get("student_roll_no", ""))
                if key:
                    fees_map[key] = row

        verification_table = []
        stats = {
            "total_records": len(applicants),
            "verified": 0,
            "needs_review": 0,
            "mismatch": 0,
            "missing": 0,
            "rules_evaluated": 0
        }

        for app in applicants:
            raw_roll = app.get("student_roll_no", "")
            norm_roll = normalize_roll(raw_roll)
            app_id = app.get("application_id", "")
            app_name = app.get("candidate_name", "")
            app_dob = app.get("date_of_birth", "")
            app_claimed_amt = app.get("claimed_scholarship_inr", "0")

            adm_record = admissions_map.get(norm_roll)
            fee_record = fees_map.get(norm_roll)

            row_status = "VERIFIED"
            rule_evaluations = []
            flag_reasons = []

            # Rule 1: Existence in Admissions
            stats["rules_evaluated"] += 1
            if not adm_record:
                row_status = "MISSING"
                flag_reasons.append("Student roll number NOT found in official University Admissions register.")
                rule_evaluations.append({
                    "rule_id": "R1_ENROLLMENT_EXISTS",
                    "rule_name": "Enrollment Record Exists",
                    "status": "FAIL",
                    "details": f"Roll '{raw_roll}' missing in Source B"
                })
            else:
                rule_evaluations.append({
                    "rule_id": "R1_ENROLLMENT_EXISTS",
                    "rule_name": "Enrollment Record Exists",
                    "status": "PASS",
                    "details": f"Matched Enrollment '{adm_record.get('enrollment_number')}'"
                })

                # Rule 2: Name Cross-Check (Fuzzy)
                stats["rules_evaluated"] += 1
                adm_name = adm_record.get("student_full_name", "")
                sim = name_similarity(app_name, adm_name)
                sim_pct = round(sim * 100, 1)

                if sim >= self.fuzzy_pass:
                    rule_evaluations.append({
                        "rule_id": "R2_NAME_MATCH",
                        "rule_name": "Applicant Name Match",
                        "status": "PASS",
                        "details": f"Exact/High Match ({sim_pct}%): '{app_name}' ~ '{adm_name}'"
                    })
                elif sim >= self.fuzzy_review:
                    if row_status not in ["MISMATCH", "MISSING"]:
                        row_status = "NEEDS_REVIEW"
                    flag_reasons.append(f"Spelling variation detected ({sim_pct}% match): Portal '{app_name}' vs Admission '{adm_name}'.")
                    rule_evaluations.append({
                        "rule_id": "R2_NAME_MATCH",
                        "rule_name": "Applicant Name Match",
                        "status": "NEEDS_REVIEW",
                        "details": f"Spelling variance ({sim_pct}%): '{app_name}' vs '{adm_name}'"
                    })
                else:
                    row_status = "MISMATCH"
                    flag_reasons.append(f"Significant Name Mismatch ({sim_pct}%): '{app_name}' does not match '{adm_name}'.")
                    rule_evaluations.append({
                        "rule_id": "R2_NAME_MATCH",
                        "rule_name": "Applicant Name Match",
                        "status": "FAIL",
                        "details": f"Name mismatch ({sim_pct}%): '{app_name}' != '{adm_name}'"
                    })

                # Rule 3: DOB Normalization & Equality Check
                stats["rules_evaluated"] += 1
                norm_app_dob = parse_date(app_dob)
                adm_raw_dob = adm_record.get("registered_dob", "")
                norm_adm_dob = parse_date(adm_raw_dob)

                if norm_app_dob and norm_adm_dob:
                    if norm_app_dob == norm_adm_dob:
                        rule_evaluations.append({
                            "rule_id": "R3_DOB_MATCH",
                            "rule_name": "Date of Birth Verification",
                            "status": "PASS",
                            "details": f"DOB matched ({norm_app_dob})"
                        })
                    else:
                        row_status = "MISMATCH"
                        flag_reasons.append(f"DOB Mismatch: Portal specifies '{app_dob}' ({norm_app_dob}) but University records have '{adm_raw_dob}' ({norm_adm_dob}).")
                        rule_evaluations.append({
                            "rule_id": "R3_DOB_MATCH",
                            "rule_name": "Date of Birth Verification",
                            "status": "FAIL",
                            "details": f"Mismatch: {norm_app_dob} != {norm_adm_dob}"
                        })
                else:
                    if row_status not in ["MISMATCH", "MISSING"]:
                        row_status = "NEEDS_REVIEW"
                    flag_reasons.append(f"Unparseable date format: Portal '{app_dob}', Admission '{adm_raw_dob}'.")
                    rule_evaluations.append({
                        "rule_id": "R3_DOB_MATCH",
                        "rule_name": "Date of Birth Verification",
                        "status": "NEEDS_REVIEW",
                        "details": f"Invalid date string format"
                    })

            # Rule 4: Fee Payment & Clearance Check
            stats["rules_evaluated"] += 1
            if not fee_record:
                if row_status not in ["MISSING"]:
                    row_status = "NEEDS_REVIEW"
                flag_reasons.append("No fee clearance receipt found in Accounts Ledger (Source C).")
                rule_evaluations.append({
                    "rule_id": "R4_FEE_CLEARANCE",
                    "rule_name": "Tuition Fee Clearance Check",
                    "status": "FAIL",
                    "details": "Receipt record missing in Accounts"
                })
            else:
                fee_status = fee_record.get("accounts_clearance_status", "")
                paid_amt = float(fee_record.get("amount_paid_inr", 0))
                due_amt = float(fee_record.get("total_tuition_due_inr", 0))

                if fee_status == "CLEARED" and paid_amt >= due_amt:
                    rule_evaluations.append({
                        "rule_id": "R4_FEE_CLEARANCE",
                        "rule_name": "Tuition Fee Clearance Check",
                        "status": "PASS",
                        "details": f"Cleared ₹{paid_amt:,.0f} (Receipt #{fee_record.get('receipt_number')})"
                    })
                elif paid_amt < due_amt or fee_status == "PARTIAL_BALANCE":
                    if row_status not in ["MISMATCH"]:
                        row_status = "NEEDS_REVIEW"
                    balance = due_amt - paid_amt
                    flag_reasons.append(f"Outstanding tuition balance: Paid ₹{paid_amt:,.0f} of ₹{due_amt:,.0f} (Due: ₹{balance:,.0f}).")
                    rule_evaluations.append({
                        "rule_id": "R4_FEE_CLEARANCE",
                        "rule_name": "Tuition Fee Clearance Check",
                        "status": "NEEDS_REVIEW",
                        "details": f"Partial balance pending: ₹{balance:,.0f}"
                    })
                else:
                    rule_evaluations.append({
                        "rule_id": "R4_FEE_CLEARANCE",
                        "rule_name": "Tuition Fee Clearance Check",
                        "status": "PASS",
                        "details": f"Status: {fee_status}"
                    })

            # Tally stats
            if row_status == "VERIFIED":
                stats["verified"] += 1
            elif row_status == "NEEDS_REVIEW":
                stats["needs_review"] += 1
            elif row_status == "MISMATCH":
                stats["mismatch"] += 1
            elif row_status == "MISSING":
                stats["missing"] += 1

            verification_table.append({
                "application_id": app_id,
                "roll_number": raw_roll,
                "normalized_roll": norm_roll,
                "overall_status": row_status,
                "flag_reasons": flag_reasons,
                "rules": rule_evaluations,
                "source_applicant": {
                    "name": app_name,
                    "dob": app_dob,
                    "dept": app.get("academic_program"),
                    "claimed_amount": app_claimed_amt
                },
                "source_admissions": {
                    "name": adm_record.get("student_full_name") if adm_record else "NOT FOUND",
                    "dob": adm_record.get("registered_dob") if adm_record else "NOT FOUND",
                    "dept": adm_record.get("enrolled_department") if adm_record else "NOT FOUND",
                    "status": adm_record.get("enrollment_status") if adm_record else "NOT FOUND"
                },
                "source_fees": {
                    "receipt_no": fee_record.get("receipt_number") if fee_record else "NOT FOUND",
                    "paid_inr": fee_record.get("amount_paid_inr") if fee_record else 0,
                    "due_inr": fee_record.get("total_tuition_due_inr") if fee_record else 0,
                    "status": fee_record.get("accounts_clearance_status") if fee_record else "NOT FOUND"
                }
            })

        return {
            "stats": stats,
            "verification_table": verification_table,
            "exceptions": [r for r in verification_table if r["overall_status"] != "VERIFIED"]
        }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="VerifyGrid Deterministic Verification Engine")
    parser.add_argument("--applicants", default="data/samples/scholarship_applicants.csv", help="Source A: Applicants")
    parser.add_argument("--admissions", default="data/samples/university_admissions.csv", help="Source B: Admissions")
    parser.add_argument("--fees", default="data/samples/fee_receipts.csv", help="Source C: Fee Receipts")
    parser.add_argument("--output", default="data/verification_results.json", help="Output JSON path")
    args = parser.parse_args()

    engine = VerifyGridEngine()
    print("=" * 70)
    print("  VERIFYGRID: DETERMINISTIC INSTITUTIONAL RECONCILIATION ENGINE")
    print("=" * 70)
    print(f"Loading Source A (Applicants):  {args.applicants}")
    print(f"Loading Source B (Admissions):  {args.admissions}")
    print(f"Loading Source C (Fees):        {args.fees}")

    results = engine.run_verification(args.applicants, args.admissions, args.fees)
    stats = results["stats"]

    total = stats["total_records"]
    auto_v = stats["verified"]
    pct_v = (auto_v / total * 100) if total > 0 else 0
    exc_count = len(results["exceptions"])

    print("\n" + "-" * 70)
    print("  VERIFICATION RUN COMPLETE — SUMMARY KPI")
    print("-" * 70)
    print(f"Total Source Records:          {total:,}")
    print(f"Auto-Verified (100% Match):    {auto_v:,} ({pct_v:.1f}%)")
    print(f"Needs Review (Review Band):    {stats['needs_review']:,}")
    print(f"Hard Mismatches (Failed Rule): {stats['mismatch']:,}")
    print(f"Missing Source Records:        {stats['missing']:,}")
    print(f"TOTAL EXCEPTIONS FOR HUMAN:    {exc_count} ({(exc_count/total*100):.1f}% exception queue)")
    print("-" * 70)

    # Save output
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Detailed verification results saved to: {args.output}\n")

if __name__ == "__main__":
    main()
