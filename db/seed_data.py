from __future__ import annotations

from datetime import date, timedelta

from db.database import execute_read, execute_write


def seed_data() -> None:
    existing_rows = execute_read("SELECT COUNT(*) AS count FROM Employees")
    if existing_rows and existing_rows[0]["count"] > 0:
        return

    today = date.today()

    employees = [
        ("Aarav", "Sharma", "aarav.sharma@acme.com", "Engineering", "Software Engineer", str(today - timedelta(days=40)), "Active"),
        ("Ishita", "Nair", "ishita.nair@acme.com", "Engineering", "Data Engineer", str(today - timedelta(days=25)), "Active"),
        ("Rohan", "Mehta", "rohan.mehta@acme.com", "Cybersecurity", "Security Analyst", str(today - timedelta(days=60)), "Active"),
        ("Neha", "Kulkarni", "neha.kulkarni@acme.com", "Delivery", "Project Manager", str(today - timedelta(days=12)), "Pending"),
        ("Arjun", "Rao", "arjun.rao@acme.com", "Engineering", "Cloud Engineer", str(today - timedelta(days=18)), "Active"),
        ("Pooja", "Singh", "pooja.singh@acme.com", "QA", "Automation Engineer", str(today - timedelta(days=50)), "Active"),
        ("Karan", "Patel", "karan.patel@acme.com", "Engineering", "Backend Engineer", str(today - timedelta(days=30)), "Active"),
        ("Divya", "Iyer", "divya.iyer@acme.com", "Engineering", "Frontend Engineer", str(today - timedelta(days=22)), "Active"),
        ("Manav", "Joshi", "manav.joshi@acme.com", "Support", "DevOps Specialist", str(today - timedelta(days=15)), "Pending"),
        ("Sara", "Thomas", "sara.thomas@acme.com", "Engineering", "Machine Learning Engineer", str(today - timedelta(days=35)), "Active"),
    ]
    execute_write(
        """
        INSERT INTO Employees (first_name, last_name, email, department, role, joining_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        employees,
        many=True,
    )

    projects = [
        (
            "Retail Banking Mobile Platform",
            "NorthBridge Bank",
            "Build a secure customer-facing mobile platform with API-first services.",
            "Python, FastAPI, PostgreSQL, React, Docker, AWS",
            str(today - timedelta(days=120)),
            str(today + timedelta(days=210)),
            "Active",
        ),
        (
            "Data Lake Modernization",
            "Vista Telecom",
            "Migrate legacy ETL to cloud-native streaming and analytical pipelines.",
            "Python, Spark, Databricks, Azure, SQL",
            str(today - timedelta(days=90)),
            str(today + timedelta(days=150)),
            "Active",
        ),
        (
            "CRM Rollout",
            "Helios Pharma",
            "Deploy enterprise CRM with custom workflows and integrations.",
            "Salesforce, Apex, Lightning, REST APIs",
            str(today - timedelta(days=60)),
            str(today + timedelta(days=200)),
            "Active",
        ),
        (
            "Cloud Migration Factory",
            "Global Freight Inc",
            "Refactor and migrate Java services to containerized cloud workloads.",
            "Java, Spring Boot, Kubernetes, Terraform, AWS",
            str(today - timedelta(days=45)),
            str(today + timedelta(days=300)),
            "Active",
        ),
        (
            "Cyber Defense Operations",
            "Union Trust",
            "Enhance SOC operations with automated playbooks and threat analytics.",
            "SIEM, SOC, Python, Azure Sentinel, Incident Response",
            str(today - timedelta(days=30)),
            str(today + timedelta(days=180)),
            "Active",
        ),
    ]
    execute_write(
        """
        INSERT INTO Projects (project_name, client, description, tech_stack, start_date, end_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        projects,
        many=True,
    )

    assignments = [
        (1, 1, str(today - timedelta(days=20)), "API Developer", "Active"),
        (2, 2, str(today - timedelta(days=18)), "Data Engineer", "Active"),
        (3, 5, str(today - timedelta(days=12)), "SOC Analyst", "Active"),
        (5, 4, str(today - timedelta(days=10)), "Cloud Engineer", "Active"),
        (8, 1, str(today - timedelta(days=9)), "Frontend Engineer", "Active"),
    ]
    execute_write(
        """
        INSERT INTO EmployeeProjects (employee_id, project_id, assigned_on, role_on_project, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        assignments,
        many=True,
    )

    skills = [
        (1, "Python", 4, str(today - timedelta(days=10))),
        (1, "FastAPI", 3, str(today - timedelta(days=10))),
        (1, "AWS", 3, str(today - timedelta(days=10))),
        (2, "Python", 4, str(today - timedelta(days=8))),
        (2, "Spark", 4, str(today - timedelta(days=8))),
        (2, "SQL", 4, str(today - timedelta(days=8))),
        (3, "SIEM", 4, str(today - timedelta(days=6))),
        (3, "Incident Response", 4, str(today - timedelta(days=6))),
        (4, "Stakeholder Management", 3, str(today - timedelta(days=7))),
        (4, "Agile Delivery", 4, str(today - timedelta(days=7))),
        (5, "AWS", 4, str(today - timedelta(days=4))),
        (5, "Terraform", 3, str(today - timedelta(days=4))),
        (6, "Selenium", 4, str(today - timedelta(days=5))),
        (6, "Pytest", 3, str(today - timedelta(days=5))),
        (7, "Java", 4, str(today - timedelta(days=9))),
        (7, "Spring Boot", 3, str(today - timedelta(days=9))),
        (8, "React", 4, str(today - timedelta(days=3))),
        (8, "TypeScript", 3, str(today - timedelta(days=3))),
        (9, "Docker", 3, str(today - timedelta(days=2))),
        (9, "Kubernetes", 3, str(today - timedelta(days=2))),
        (10, "Python", 4, str(today - timedelta(days=11))),
        (10, "Machine Learning", 4, str(today - timedelta(days=11))),
    ]
    execute_write(
        """
        INSERT INTO Skills (employee_id, skill_name, proficiency, last_updated)
        VALUES (?, ?, ?, ?)
        """,
        skills,
        many=True,
    )
