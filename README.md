# Job Application Tracker

## Project Description

The Job Application Tracker is a web-based application developed using Python, Flask, MySQL, HTML, and CSS.

It helps users organize companies, job opportunities, applications, and professional contacts in one place.

## Features

- Dashboard showing total companies, jobs, applications, and contacts.
- Add, view, edit, and delete companies.
- Add, view, edit, and delete jobs.
- Add, view, edit, and delete job applications.
- Add, view, edit, and delete contacts.
- Job Match feature that compares user skills with job requirements and calculates a matching percentage.

## Technologies Used

- Python 3
- Flask
- MySQL
- MySQL Connector
- HTML
- CSS
- Jinja2

## Project Structure

```text
job_tracker/
├── app.py
├── database.py
├── schema.sql
├── requirements.txt
├── README.md
├── AI_USAGE.md
├── .gitignore
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── companies.html
│   ├── jobs.html
│   ├── applications.html
│   ├── contacts.html
│   ├── job_match.html
│   ├── edit_company.html
│   ├── edit_job.html
│   ├── edit_application.html
│   └── edit_contact.html
└── static/
    └── style.css
```

## Installation

1. Install Python 3 and MySQL.
2. Clone or download this repository.
3. Open the project folder in VS Code.
4. Install dependencies:

```bash
py -m pip install -r requirements.txt
```

5. Create the MySQL database and tables by running `schema.sql` in MySQL Workbench.
6. Create a `.env` file in the project folder and add your local database credentials:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=job_tracker
DB_PORT=3306
```

7. Start the application:

```bash
py app.py
```

8. Open this address in your browser:

http://127.0.0.1:5000/

## Job Match Example

If a job requires Python, SQL, Flask, and HTML, and the user enters Python, SQL, and Flask, the match percentage is 75%.

## Developed For

Database Management / Full-Stack Development Project.
