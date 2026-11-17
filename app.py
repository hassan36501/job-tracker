import json
import re

from flask import Flask, render_template, request, redirect, url_for
from database import get_db_connection

app = Flask(__name__)


# =====================================
# HELPER FUNCTIONS
# =====================================

def clean_skills(text):
    """Convert comma-separated skills into a clean list."""
    return list(dict.fromkeys(
        skill.strip().lower()
        for skill in text.split(",")
        if skill.strip()
    ))


def read_requirements(value):
    """Read skills from the MySQL JSON column safely."""

    if value is None:
        return []

    if isinstance(value, bytes):
        value = value.decode("utf-8")

    # If MySQL returns a list, clean its items.
    if isinstance(value, list):
        result = []

        for item in value:
            if isinstance(item, str):
                # Handle older records containing JSON inside JSON.
                item = item.strip()

                if item.startswith("[") or item.startswith('"'):
                    nested = read_requirements(item)
                    result.extend(nested)
                elif item:
                    result.append(item.lower())

        return list(dict.fromkeys(result))

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return []

        # Decode JSON strings and arrays.
        if value.startswith("[") or value.startswith('"'):
            try:
                decoded = json.loads(value)

                if decoded != value:
                    return read_requirements(decoded)

            except (json.JSONDecodeError, TypeError):
                # An old malformed JSON value cannot be trusted.
                return []

        # Also support plain comma-separated text.
        return clean_skills(value)

    return []


def get_connection():
    """Create a database connection."""
    return get_db_connection()


# =====================================
# DASHBOARD
# =====================================

@app.route("/")
def dashboard():

    connection = get_connection()

    if not connection:
        return "Database connection failed!"

    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM companies")
    total_companies = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_jobs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications")
    total_applications = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM contacts")
    total_contacts = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return render_template(
        "dashboard.html",
        total_companies=total_companies,
        total_jobs=total_jobs,
        total_applications=total_applications,
        total_contacts=total_contacts
    )


# =====================================
# COMPANIES - ADD AND VIEW
# =====================================

@app.route("/companies", methods=["GET", "POST"])
def companies():

    connection = get_connection()

    if not connection:
        return "Database connection failed!"

    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":

        company_name = request.form["company_name"]
        industry = request.form.get("industry") or None
        website = request.form.get("website") or None
        city = request.form.get("city") or None
        state = request.form.get("state") or None
        notes = request.form.get("notes") or None

        cursor.execute("""
            INSERT INTO companies
            (company_name, industry, website, city, state, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            company_name, industry, website,
            city, state, notes
        ))

        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for("companies"))

    cursor.execute(
        "SELECT * FROM companies ORDER BY company_id DESC"
    )
    company_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "companies.html",
        companies=company_list
    )


# =====================================
# COMPANIES - EDIT
# =====================================

@app.route("/edit-company/<int:company_id>", methods=["GET", "POST"])
def edit_company(company_id):

    connection = get_connection()

    if not connection:
        return "Database connection failed!"

    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":

        company_name = request.form["company_name"]
        industry = request.form.get("industry") or None
        website = request.form.get("website") or None
        city = request.form.get("city") or None
        state = request.form.get("state") or None
        notes = request.form.get("notes") or None

        cursor.execute("""
            UPDATE companies
            SET company_name=%s,
                industry=%s,
                website=%s,
                city=%s,
                state=%s,
                notes=%s
            WHERE company_id=%s
        """, (
            company_name, industry, website,
            city, state, notes, company_id
        ))

        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for("companies"))

    cursor.execute(
        "SELECT * FROM companies WHERE company_id=%s",
        (company_id,)
    )
    company = cursor.fetchone()

    cursor.close()
    connection.close()

    if not company:
        return "Company not found!", 404

    return render_template(
        "edit_company.html",
        company=company
    )


# =====================================
# COMPANIES - DELETE
# =====================================

@app.route("/delete-company/<int:company_id>", methods=["POST"])
def delete_company(company_id):

    connection = get_connection()

    if not connection:
        return "Database connection failed!"

    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM companies WHERE company_id=%s",
        (company_id,)
    )

    connection.commit()
    cursor.close()
    connection.close()

    return redirect(url_for("companies"))


# =====================================
# JOBS - ADD AND VIEW
# =====================================

@app.route("/jobs", methods=["GET", "POST"])
def jobs():

    connection = get_connection()

    if not connection:
        return "Database connection failed!"

    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":

        company_id = request.form["company_id"]
        job_title = request.form["job_title"]
        job_type = request.form["job_type"]

        salary_min = request.form.get("salary_min") or None
        salary_max = request.form.get("salary_max") or None
        job_url = request.form.get("job_url") or None
        date_posted = request.form.get("date_posted") or None

        # Convert entered skills into a proper list.
        requirements_text = request.form.get("requirements", "")
        requirements = [
            item.strip()
            for item in requirements_text.split(",")
            if item.strip()
        ]

        # Encode the list only once for MySQL JSON.
        requirements_json = json.dumps(requirements)

        cursor.execute("""
            INSERT INTO jobs
            (company_id, job_title, job_type, salary_min,
             salary_max, job_url, date_posted, requirements)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            company_id, job_title, job_type,
            salary_min, salary_max, job_url,
            date_posted, requirements_json
        ))

        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for("jobs"))

    cursor.execute("""
        SELECT jobs.*, companies.company_name
        FROM jobs
        JOIN companies
        ON jobs.company_id = companies.company_id
        ORDER BY jobs.job_id DESC
    """)

    all_jobs = cursor.fetchall()

    cursor.execute(
        "SELECT company_id, company_name FROM companies"
    )
    all_companies = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "jobs.html",
        jobs=all_jobs,
        companies=all_companies
    )


# =====================================
# JOBS - EDIT
# =====================================

@app.route("/edit-job/<int:job_id>", methods=["GET", "POST"])
def edit_job(job_id):

    connection = get_connection()

    if not connection:
        return "Database connection failed!"

    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":

        company_id = request.form["company_id"]
        job_title = request.form["job_title"]
        job_type = request.form["job_type"]

        salary_min = request.form.get("salary_min") or None
        salary_max = request.form.get("salary_max") or None
        job_url = request.form.get("job_url") or None
        date_posted = request.form.get("date_posted") or None

        requirements_text = request.form.get("requirements", "")
        requirements = [
            item.strip()
            for item in requirements_text.split(",")
            if item.strip()
        ]

        requirements_json = json.dumps(requirements)

        cursor.execute("""
            UPDATE jobs
            SET company_id=%s,
                job_title=%s,
                job_type=%s,
                salary_min=%s,
                salary_max=%s,
                job_url=%s,
                date_posted=%s,
                requirements=%s
            WHERE job_id=%s
        """, (
            company_id, job_title, job_type,
            salary_min, salary_max, job_url,
            date_posted, requirements_json, job_id
        ))

        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for("jobs"))

    cursor.execute(
        "SELECT * FROM jobs WHERE job_id=%s",
        (job_id,)
    )
    job = cursor.fetchone()

    cursor.execute(
        "SELECT company_id, company_name FROM companies"
    )
    companies_list = cursor.fetchall()

    cursor.close()
    connection.close()

    if job is None:
        return "Job not found!", 404

    job["requirements_list"] = read_requirements(job["requirements"])

    return render_template(
        "edit_job.html",
        job=job,
        companies=companies_list
    )


# =====================================
# JOBS - DELETE
# =====================================

@app.route("/delete-job/<int:job_id>", methods=["POST"])
def delete_job(job_id):

    connection = get_connection()

    if not connection:
        return "Database connection failed!"

    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM jobs WHERE job_id=%s",
        (job_id,)
    )

    connection.commit()
    cursor.close()
    connection.close()

    return redirect(url_for("jobs"))


# =====================================
# APPLICATIONS - ADD AND VIEW
# =====================================

@app.route("/applications", methods=["GET", "POST"])
def applications():

    connection = get_connection()

    if not connection:
        return "Database connection failed!"

    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":

        job_id = request.form["job_id"]
        application_date = request.form["application_date"]
        status = request.form["status"]

        resume_version = request.form.get("resume_version") or None
        cover_letter_sent = (
            1 if request.form.get("cover_letter_sent") else 0
        )

        interview_notes = request.form.get("interview_data", "")
        interview_json = json.dumps(interview_notes)

        cursor.execute("""
            INSERT INTO applications
            (job_id, application_date, status, resume_version,
             cover_letter_sent, interview_data)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            job_id, application_date, status,
            resume_version, cover_letter_sent, interview_json
        ))

        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for("applications"))

    cursor.execute("""
        SELECT applications.*, jobs.job_title, companies.company_name
        FROM applications
        JOIN jobs ON applications.job_id = jobs.job_id
        JOIN companies ON jobs.company_id = companies.company_id
        ORDER BY applications.application_id DESC
    """)
    all_applications = cursor.fetchall()

    cursor.execute("""
        SELECT jobs.job_id, jobs.job_title, companies.company_name
        FROM jobs
        JOIN companies ON jobs.company_id = companies.company_id
    """)
    all_jobs = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "applications.html",
        applications=all_applications,
        jobs=all_jobs
    )


# =====================================
# APPLICATIONS - EDIT
# =====================================

@app.route(
    "/edit-application/<int:application_id>",
    methods=["GET", "POST"]
)
def edit_application(application_id):

    connection = get_connection()

    if not connection:
        return "Database connection failed!"

    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":

        job_id = request.form["job_id"]
        application_date = request.form["application_date"]
        status = request.form["status"]

        resume_version = request.form.get("resume_version") or None
        cover_letter_sent = (
            1 if request.form.get("cover_letter_sent") else 0
        )

        interview_notes = request.form.get("interview_data", "")
        interview_json = json.dumps(interview_notes)

        cursor.execute("""
            UPDATE applications
            SET job_id=%s,
                application_date=%s,
                status=%s,
                resume_version=%s,
                cover_letter_sent=%s,
                interview_data=%s
            WHERE application_id=%s
        """, (
            job_id, application_date, status,
            resume_version, cover_letter_sent,
            interview_json, application_id
        ))

        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for("applications"))

    cursor.execute(
        "SELECT * FROM applications WHERE application_id=%s",
        (application_id,)
    )
    application = cursor.fetchone()

    cursor.execute("""
        SELECT jobs.job_id, jobs.job_title, companies.company_name
        FROM jobs
        JOIN companies ON jobs.company_id = companies.company_id
    """)
    jobs_list = cursor.fetchall()

    cursor.close()
    connection.close()

    if application is None:
        return "Application not found!", 404

    return render_template(
        "edit_application.html",
        application=application,
        jobs=jobs_list
    )


# =====================================
# APPLICATIONS - DELETE
# =====================================

@app.route(
    "/delete-application/<int:application_id>",
    methods=["POST"]
)
def delete_application(application_id):

    connection = get_connection()

    if not connection:
        return "Database connection failed!"

    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM applications WHERE application_id=%s",
        (application_id,)
    )

    connection.commit()
    cursor.close()
    connection.close()

    return redirect(url_for("applications"))


# =====================================
# CONTACTS - ADD AND VIEW
# =====================================

@app.route("/contacts", methods=["GET", "POST"])
def contacts():

    connection = get_connection()

    if not connection:
        return "Database connection failed!"

    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":

        company_id = request.form["company_id"]
        contact_name = request.form["contact_name"]

        title = request.form.get("title") or None
        email = request.form.get("email") or None
        phone = request.form.get("phone") or None
        linkedin_url = request.form.get("linkedin_url") or None
        notes = request.form.get("notes") or None

        cursor.execute("""
            INSERT INTO contacts
            (company_id, contact_name, title, email,
             phone, linkedin_url, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            company_id, contact_name, title,
            email, phone, linkedin_url, notes
        ))

        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for("contacts"))

    cursor.execute("""
        SELECT contacts.*, companies.company_name
        FROM contacts
        JOIN companies
        ON contacts.company_id = companies.company_id
        ORDER BY contacts.contact_id DESC
    """)
    all_contacts = cursor.fetchall()

    cursor.execute(
        "SELECT company_id, company_name FROM companies"
    )
    all_companies = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "contacts.html",
        contacts=all_contacts,
        companies=all_companies
    )


# =====================================
# CONTACTS - EDIT
# =====================================

@app.route("/edit-contact/<int:contact_id>", methods=["GET", "POST"])
def edit_contact(contact_id):

    connection = get_connection()

    if not connection:
        return "Database connection failed!"

    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":

        company_id = request.form["company_id"]
        contact_name = request.form["contact_name"]

        title = request.form.get("title") or None
        email = request.form.get("email") or None
        phone = request.form.get("phone") or None
        linkedin_url = request.form.get("linkedin_url") or None
        notes = request.form.get("notes") or None

        cursor.execute("""
            UPDATE contacts
            SET company_id=%s,
                contact_name=%s,
                title=%s,
                email=%s,
                phone=%s,
                linkedin_url=%s,
                notes=%s
            WHERE contact_id=%s
        """, (
            company_id, contact_name, title,
            email, phone, linkedin_url, notes, contact_id
        ))

        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for("contacts"))

    cursor.execute(
        "SELECT * FROM contacts WHERE contact_id=%s",
        (contact_id,)
    )
    contact = cursor.fetchone()

    cursor.execute(
        "SELECT company_id, company_name FROM companies"
    )
    companies_list = cursor.fetchall()

    cursor.close()
    connection.close()

    if contact is None:
        return "Contact not found!", 404

    return render_template(
        "edit_contact.html",
        contact=contact,
        companies=companies_list
    )


# =====================================
# CONTACTS - DELETE
# =====================================

@app.route("/delete-contact/<int:contact_id>", methods=["POST"])
def delete_contact(contact_id):

    connection = get_connection()

    if not connection:
        return "Database connection failed!"

    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM contacts WHERE contact_id=%s",
        (contact_id,)
    )

    connection.commit()
    cursor.close()
    connection.close()

    return redirect(url_for("contacts"))


# =====================================
# JOB MATCH FINDER
# =====================================

@app.route("/job-match", methods=["GET", "POST"])
def job_match():

    matched_jobs = []
    user_skills = ""

    connection = get_connection()

    if not connection:
        return "Database connection failed!"

    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":

        user_skills = request.form.get("skills", "")
        skills_list = clean_skills(user_skills)

        cursor.execute("""
            SELECT jobs.*, companies.company_name
            FROM jobs
            JOIN companies
            ON jobs.company_id = companies.company_id
            ORDER BY jobs.job_id DESC
        """)

        all_jobs = cursor.fetchall()

        for job in all_jobs:

            requirements = read_requirements(job["requirements"])

            matched_skills = [
                skill for skill in requirements
                if skill in skills_list
            ]

            if requirements:
                percentage = (
                    len(matched_skills) / len(requirements)
                ) * 100
            else:
                percentage = 0

            job["requirements_list"] = requirements
            job["matched_skills"] = matched_skills
            job["match_percentage"] = round(percentage, 2)

            matched_jobs.append(job)

        matched_jobs.sort(
            key=lambda job: job["match_percentage"],
            reverse=True
        )

    cursor.close()
    connection.close()

    return render_template(
        "job_match.html",
        jobs=matched_jobs,
        user_skills=user_skills
    )


# =====================================
# RUN APPLICATION
# =====================================

if __name__ == "__main__":
    app.run(debug=True)