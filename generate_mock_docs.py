"""
Generate realistic mock loan documents for underwriting POC testing.

Produces multiple scenario pairs in src/main/resources:
  - APP-2026-1001 : all fields consistent            -> expect APPROVE
  - APP-2026-1002 : stated income inflated           -> expect HOLD/REJECT
  - APP-2026-1003 : applicant name genuinely different -> expect MISMATCH
  - APP-2026-1004 : employer entity differs          -> expect MISMATCH
  - APP-2026-1005 : near-match name (case/punct)     -> expect MATCHED

Each scenario = loan application form + paystub earnings statement.
File naming: loan_application_<appid>.png / paystub_<empid>.png
"""

import os
from PIL import Image, ImageDraw, ImageFont

RESOURCE_DIR = os.path.join("src", "main", "resources")
os.makedirs(RESOURCE_DIR, exist_ok=True)

# Larger, readable font (falls back to default bitmap font if unavailable)
try:
    FONT = ImageFont.truetype("arial.ttf", 22)
    FONT_BOLD = ImageFont.truetype("arialbd.ttf", 24)
    FONT_SMALL = ImageFont.truetype("arial.ttf", 18)
except OSError:
    FONT = FONT_BOLD = FONT_SMALL = ImageFont.load_default()

IMG_W, IMG_H = 1000, 1400
MARGIN = 60


def draw_doc(filename, title, subtitle, sections):
    """sections: list of (heading, [(label, value), ...])"""
    img = Image.new("RGB", (IMG_W, IMG_H), "white")
    d = ImageDraw.Draw(img)

    y = MARGIN
    d.text((MARGIN, y), title, font=FONT_BOLD, fill="black")
    y += 40
    d.text((MARGIN, y), subtitle, font=FONT_SMALL, fill="gray")
    y += 60

    for heading, rows in sections:
        d.text((MARGIN, y), heading.upper(), font=FONT_BOLD, fill="black")
        d.line([(MARGIN, y + 32), (IMG_W - MARGIN, y + 32)], fill="black", width=2)
        y += 50

        for label, value in rows:
            d.text((MARGIN + 20, y), f"{label}:", font=FONT, fill="black")
            d.text((MARGIN + 340, y), str(value), font=FONT, fill="black")
            y += 38
        y += 25

    out = os.path.join(RESOURCE_DIR, filename)
    img.save(out)
    print(f"Generated: {out}")


def application_form(app_id, name, dob, ssn_last4, address, phone, email,
                     employer, job_title, monthly_income, loan_amount,
                     loan_purpose, employment_months):
    return draw_doc(
        f"loan_application_{app_id.lower()}.png",
        "DIGITAL LOAN APPLICATION FORM",
        f"Application ID: {app_id}    |    Date: November 12, 2026",
        [
            ("APPLICANT INFORMATION", [
                ("Full Legal Name", name),
                ("Date of Birth", dob),
                ("SSN (last 4)", ssn_last4),
                ("Current Address", address),
                ("Phone", phone),
                ("Email", email),
            ]),
            ("EMPLOYMENT & INCOME", [
                ("Current Employer", employer),
                ("Job Title", job_title),
                ("Months Employed", employment_months),
                ("Stated Monthly Gross Income", monthly_income),
            ]),
            ("LOAN REQUEST", [
                ("Requested Loan Amount", loan_amount),
                ("Loan Purpose", loan_purpose),
                ("Desired Term (months)", "36"),
            ]),
        ],
    )


def paystub(company, address, employee_name, employee_id, job_title,
            pay_period, pay_date, earnings, deductions, taxes, ytd,
            employee_address=None, ssn_last4=None):
    return draw_doc(
        f"paystub_{employee_id.lower()}.png",
        f"{company} — EARNINGS STATEMENT",
        f"{address}    |    Pay Date: {pay_date}",
        [
            ("EMPLOYEE INFORMATION", [
                ("Employee Name", employee_name),
                ("Employee ID", employee_id),
                ("Job Title", job_title),
                ("Pay Period", pay_period),
                ("Employee Address", employee_address or ""),
                ("SSN (last 4)", ssn_last4 or ""),
            ]),
            ("EARNINGS", earnings),
            ("DEDUCTIONS", deductions),
            ("TAXES WITHHELD", taxes),
            ("YEAR-TO-DATE", ytd),
        ],
    )


# ---------------------------------------------------------------------------
# Shared realistic values
# ---------------------------------------------------------------------------
NAME = "VenuGopal Rao"
EMPLOYER = "TechCorp Solutions LLC"
JOB_TITLE = "Senior Software Engineer"
ADDRESS = "4521 Maple Grove Ln, Austin, TX 78745"
PHONE = "(512) 555-0147"
EMAIL = "venu.rao@example.com"

BASE_EARNINGS = [
    ("Regular Hours (80.0)", "$6,100.00"),
    ("Overtime Hours (0.0)", "$0.00"),
    ("Bonus", "$0.00"),
    ("Gross Pay", "$6,100.00"),
    ("Net Pay", "$4,251.85"),
]

BASE_DEDUCTIONS = [
    ("401(k) Contribution (6%)", "$366.00"),
    ("Health Insurance Premium", "$245.50"),
    ("Dental / Vision", "$38.00"),
    ("Total Deductions", "$649.50"),
]

BASE_TAXES = [
    ("Federal Income Tax", "$732.00"),
    ("State Income Tax (TX)", "$0.00"),
    ("Social Security (6.2%)", "$378.20"),
    ("Medicare (1.45%)", "$88.45"),
    ("Total Taxes", "$1,198.65"),
]

BASE_YTD = [
    ("Gross YTD", "$73,200.00"),
    ("Net YTD", "$51,024.20"),
    ("Federal Tax YTD", "$8,784.00"),
]


def scenario(app_suffix, stated_income, loan_amount, loan_purpose,
              app_name=NAME, paystub_name=NAME, paystub_emp_id=None,
              paystub_company=EMPLOYER, paystub_title=JOB_TITLE,
              app_employer=EMPLOYER, earnings=None, deductions=None,
              taxes=None, ytd=None, paystub_address=ADDRESS, paystub_ssn="4821"):
    if paystub_emp_id is None:
        paystub_emp_id = f"EMP-{app_suffix}"
    application_form(
        app_id=f"APP-2026-{app_suffix}",
        name=app_name, dob="03/14/1988", ssn_last4="4821",
        address=ADDRESS, phone=PHONE, email=EMAIL,
        employer=app_employer, job_title=JOB_TITLE,
        monthly_income=stated_income, loan_amount=loan_amount,
        loan_purpose=loan_purpose, employment_months="54",
    )
    paystub(
        company=paystub_company, address="1200 Congress Ave, Austin, TX 78701",
        employee_name=paystub_name, employee_id=paystub_emp_id,
        job_title=paystub_title,
        pay_period="Oct 26 – Nov 08, 2026", pay_date="Nov 12, 2026",
        earnings=earnings or BASE_EARNINGS,
        deductions=deductions or BASE_DEDUCTIONS,
        taxes=taxes or BASE_TAXES,
        ytd=ytd or BASE_YTD,
        employee_address=paystub_address,
        ssn_last4=paystub_ssn,
    )


# Scenario 1: CLEAN — everything matches -> expect APPROVE
scenario("1001", "$6,100.00", "$25,000.00", "Debt consolidation")

# Scenario 2: INCOME INFLATION — stated $8,500 vs verified $6,100
scenario("1002", "$8,500.00", "$40,000.00", "Home improvement")

# Scenario 3: NAME MISMATCH — different person on paystub
scenario("1003", "$6,100.00", "$25,000.00", "Debt consolidation",
         paystub_name="Rajesh Kumar", paystub_emp_id="EMP-90117")

# Scenario 4: EMPLOYER MISMATCH — different company + lower pay
scenario("1004", "$6,100.00", "$25,000.00", "Debt consolidation",
         app_employer="TechCorp Solutions LLC",
         paystub_company="LoneStar Retail Group Inc",
         paystub_emp_id="EMP-55402", paystub_title="Store Operations Manager",
         earnings=[
             ("Regular Hours (80.0)", "$4,800.00"),
             ("Overtime Hours (6.5)", "$585.00"),
             ("Bonus", "$250.00"),
             ("Gross Pay", "$5,635.00"),
             ("Net Pay", "$3,912.47"),
         ],
         deductions=[
             ("401(k) Contribution (4%)", "$225.40"),
             ("Health Insurance Premium", "$198.00"),
             ("Dental / Vision", "$32.00"),
             ("Total Deductions", "$455.40"),
         ],
         taxes=[
             ("Federal Income Tax", "$676.20"),
             ("State Income Tax (TX)", "$0.00"),
             ("Social Security (6.2%)", "$349.37"),
             ("Medicare (1.45%)", "$81.71"),
             ("Total Taxes", "$1,107.28"),
         ],
         ytd=[
             ("Gross YTD", "$67,620.00"),
             ("Net YTD", "$46,890.15"),
             ("Federal Tax YTD", "$8,114.40"),
         ])

# Scenario 5: NEAR-MATCH NAME — capitalization/punctuation only -> MATCHED
scenario("1005", "$6,100.00", "$25,000.00", "Debt consolidation",
         app_name="Venugopal Rao", paystub_name="VenuGopal. Rao")

# Scenario 6: ADDRESS MISMATCH — paystub shows a different residence
scenario("1006", "$6,100.00", "$25,000.00", "Debt consolidation",
         paystub_address="789 Oak Hollow Dr, Dallas, TX 75201")

# Scenario 7: SSN MISMATCH — different last-4 on paystub
scenario("1007", "$6,100.00", "$25,000.00", "Debt consolidation",
         paystub_ssn="9034")

# Scenario 8: UNAFFORDABLE LOAN — $60k on $6.1k income (ratio ~9.8x)
scenario("1008", "$6,100.00", "$60,000.00", "Major purchase")

print("\nDone. Files written to:", os.path.abspath(RESOURCE_DIR))
