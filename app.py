from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from agents.hr_agent import HRAgent
from agents.it_agent import ITAgent
from agents.skill_gap_agent import SkillGapAgent
from agents.training_agent import TrainingAgent
from db.database import execute_read, execute_write, initialize_database
from db.seed_data import seed_data
from mcp.registry import MCPRegistry
from utils.gemini_client import GeminiClient
from utils.logger import log_action

LOGO_PATH = Path(__file__).resolve().parent / "utils" / "Mastek-logo.svg"
AUTH_USERS = {
    "admin": "admin123",
    "hrlead": "hrlead123",
    "itops": "itops123",
}


def sanitize_text(value: str, max_len: int = 2000) -> str:
    normalized = " ".join((value or "").strip().split())
    return normalized[:max_len]


def is_valid_email(email: str) -> bool:
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return bool(re.match(pattern, email or ""))


def to_df(rows: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def load_css() -> None:
    css_path = Path(__file__).resolve().parent / "static" / "styles.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def parse_json_field(raw_value: str | None, default: Any) -> Any:
    if not raw_value:
        return default
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return default


def get_logo_data_uri() -> str:
    if not LOGO_PATH.exists():
        return ""
    logo_bytes = LOGO_PATH.read_bytes()
    encoded = base64.b64encode(logo_bytes).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


class AgentOrchestrator:
    def __init__(self, registry: MCPRegistry) -> None:
        self.registry = registry
        self.hr_agent = HRAgent(registry)
        self.it_agent = ITAgent(registry)
        self.training_agent = TrainingAgent(registry)
        self.skill_gap_agent = SkillGapAgent(registry)

    def run_onboarding(self, employee_id: int) -> dict[str, Any]:
        self.hr_agent.execute(
            {
                "action": "update_onboarding",
                "employee_id": employee_id,
                "status": "In Progress",
            }
        )
        it_result = self.it_agent.execute({"action": "provision_access", "employee_id": employee_id})
        training_result = self.training_agent.execute(
            {
                "action": "assign_training",
                "employee_id": employee_id,
            }
        )
        self.hr_agent.execute(
            {
                "action": "update_onboarding",
                "employee_id": employee_id,
                "status": "Active",
            }
        )
        return {
            "it": it_result,
            "training": training_result,
        }

    def assign_project_and_trigger_skill_gap(
        self,
        employee_id: int,
        project_id: int,
        role_on_project: str,
    ) -> dict[str, Any]:
        assignment = self.hr_agent.execute(
            {
                "action": "assign_project",
                "employee_id": employee_id,
                "project_id": project_id,
                "role_on_project": role_on_project,
            }
        )
        assessment = self.skill_gap_agent.execute(
            {
                "action": "generate_assessment",
                "employee_id": employee_id,
                "project_id": project_id,
            }
        )
        return {
            "assignment": assignment,
            "assessment": assessment,
        }

    def submit_assessment_answers(self, assessment_id: int, answers: dict[int, str]) -> dict[str, Any]:
        assessment_rows = self.registry.execute_tool(
            "db_read",
            {
                "query": "SELECT assessment_id, employee_id FROM Assessments WHERE assessment_id = ?",
                "params": (assessment_id,),
            },
        )
        if not assessment_rows:
            raise ValueError("Assessment not found.")

        employee_id = int(assessment_rows[0]["employee_id"])

        for question_id, answer_text in answers.items():
            sanitized_answer = sanitize_text(answer_text)
            self.registry.execute_tool(
                "db_write",
                {
                    "query": "DELETE FROM AssessmentAnswers WHERE question_id = ? AND employee_id = ?",
                    "params": (question_id, employee_id),
                },
            )
            self.registry.execute_tool(
                "db_write",
                {
                    "query": """
                        INSERT INTO AssessmentAnswers (question_id, employee_id, answer_text)
                        VALUES (?, ?, ?)
                    """,
                    "params": (question_id, employee_id, sanitized_answer),
                },
            )

        return self.skill_gap_agent.execute(
            {
                "action": "evaluate_assessment",
                "assessment_id": assessment_id,
            }
        )


def register_mcp_tools(registry: MCPRegistry, gemini_client: GeminiClient) -> None:
    def db_read(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        return execute_read(query, params)

    def db_write(
        query: str,
        params: tuple[Any, ...] | list[tuple[Any, ...]] = (),
        many: bool = False,
    ) -> int:
        return execute_write(query, params, many=many)

    def generate_assessment_questions(tech_stack: str, question_count: int = 12) -> list[str]:
        return gemini_client.generate_assessment_questions(tech_stack, question_count)

    def analyze_skill_answers(tech_stack: str, qa_pairs: list[dict[str, str]]) -> dict[str, Any]:
        return gemini_client.analyze_skill_answers(tech_stack, qa_pairs)

    def recommend_courses(skill_gaps: list[str], tech_stack: str) -> dict[str, Any]:
        return gemini_client.recommend_courses(skill_gaps, tech_stack)

    def reflect_recommendation(
        initial_recommendation: str,
        tech_stack: str,
        qa_pairs: list[dict[str, str]],
    ) -> dict[str, str]:
        return gemini_client.reflect_recommendation(initial_recommendation, tech_stack, qa_pairs)

    def send_email(recipient: str, subject: str, body: str) -> dict[str, str]:
        # Simulation only; no actual SMTP call.
        return {
            "status": "sent",
            "recipient": recipient,
            "subject": subject,
            "body": body,
        }

    def log_tool(
        agent_name: str,
        action: str,
        employee_id: int | None = None,
        project_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        return log_action(
            db_write=db_write,
            agent_name=agent_name,
            action=action,
            employee_id=employee_id,
            project_id=project_id,
            metadata=metadata,
        )

    registry.register_tool("db_read", db_read)
    registry.register_tool("db_write", db_write)
    registry.register_tool("log_action", log_tool)
    registry.register_tool("generate_assessment_questions", generate_assessment_questions)
    registry.register_tool("analyze_skill_answers", analyze_skill_answers)
    registry.register_tool("recommend_courses", recommend_courses)
    registry.register_tool("reflect_recommendation", reflect_recommendation)
    registry.register_tool("send_email", send_email)


@st.cache_resource(show_spinner=False)
def bootstrap() -> tuple[AgentOrchestrator, MCPRegistry, GeminiClient]:
    initialize_database()
    seed_data()

    registry = MCPRegistry()
    gemini_client = GeminiClient()
    register_mcp_tools(registry, gemini_client)

    orchestrator = AgentOrchestrator(registry)
    return orchestrator, registry, gemini_client


def init_session_state() -> None:
    defaults = {
        "authenticated": False,
        "current_user": "",
        "current_page": "Dashboard",
        "pending_assessment_id": None,
        "last_recommendation": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_auth_gate() -> bool:
    if st.session_state.authenticated:
        st.sidebar.markdown(f"**Signed in:** `{st.session_state.current_user}`")
        if st.sidebar.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.current_user = ""
            st.session_state.current_page = "Dashboard"
            st.rerun()
        return True

    st.markdown(
        """
        <div class="section-card">
            <h2>Secure Access</h2>
            <p>Sign in to continue to the Agentic Employee Onboarding workspace.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In")

    if submitted:
        if AUTH_USERS.get(username.strip()) == password:
            st.session_state.authenticated = True
            st.session_state.current_user = username.strip()
            st.rerun()
        st.error("Invalid credentials.")

    return False


def render_header() -> None:
    logo_src = get_logo_data_uri()
    st.markdown(
        f"""
        <div class="brand-strip">
            <img src="{logo_src}" alt="Company Logo" />
            <div>
                <h1>Agentic AI Employee Onboarding</h1>
                <p>Multi-agent workforce management with MCP tools, auditability, and skill intelligence.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard(registry: MCPRegistry) -> None:
    st.subheader("Dashboard")

    employee_count = registry.execute_tool("db_read", {"query": "SELECT COUNT(*) AS count FROM Employees"})[0]["count"]
    project_count = registry.execute_tool("db_read", {"query": "SELECT COUNT(*) AS count FROM Projects"})[0]["count"]
    active_assignments = registry.execute_tool(
        "db_read",
        {"query": "SELECT COUNT(*) AS count FROM EmployeeProjects WHERE status = 'Active'"},
    )[0]["count"]
    pending_assessments = registry.execute_tool(
        "db_read",
        {"query": "SELECT COUNT(*) AS count FROM Assessments WHERE status = 'Pending'"},
    )[0]["count"]

    cards = [
        ("Employees", employee_count),
        ("Projects", project_count),
        ("Active Assignments", active_assignments),
        ("Pending Skill Assessments", pending_assessments),
    ]

    columns = st.columns(4)
    for column, (label, value) in zip(columns, cards):
        column.markdown(
            f"""
            <div class="metric-card">
                <h3>{label}</h3>
                <p>{value}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    recent_logs = registry.execute_tool(
        "db_read",
        {
            "query": """
                SELECT timestamp, agent_name, action, employee_id, project_id
                FROM AuditLogs
                ORDER BY log_id DESC
                LIMIT 8
            """
        },
    )
    st.markdown("### Recent Agent Activity")
    st.dataframe(to_df(recent_logs), use_container_width=True, hide_index=True)


def render_employees(orchestrator: AgentOrchestrator, registry: MCPRegistry) -> None:
    st.subheader("Employees")

    employee_rows = registry.execute_tool(
        "db_read",
        {
            "query": """
                SELECT employee_id, first_name, last_name, email, department, role, joining_date, status
                FROM Employees
                ORDER BY employee_id
            """
        },
    )
    st.dataframe(to_df(employee_rows), use_container_width=True, hide_index=True)

    st.markdown("### Add Employee")
    with st.form("employee_create_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        first_name = col1.text_input("First Name")
        last_name = col2.text_input("Last Name")
        email = st.text_input("Email")
        col3, col4 = st.columns(2)
        department = col3.text_input("Department")
        role = col4.text_input("Role")
        joining_date = st.date_input("Joining Date")
        submitted = st.form_submit_button("Create Employee")

    if submitted:
        payload = {
            "action": "create_employee",
            "first_name": sanitize_text(first_name, 50),
            "last_name": sanitize_text(last_name, 50),
            "email": sanitize_text(email.lower(), 120),
            "department": sanitize_text(department, 80),
            "role": sanitize_text(role, 80),
            "joining_date": joining_date.isoformat(),
        }

        if not all(payload[field] for field in ["first_name", "last_name", "email", "department", "role"]):
            st.error("All employee fields are required.")
        elif not is_valid_email(payload["email"]):
            st.error("Enter a valid email address.")
        else:
            try:
                result = orchestrator.hr_agent.execute(payload)
                st.success(f"Employee created successfully (ID: {result['employee_id']}).")
                st.rerun()
            except Exception as exc:
                st.error(f"Unable to create employee: {exc}")

    st.markdown("### Multi-Agent Onboarding")
    if not employee_rows:
        st.info("Create at least one employee to start onboarding.")
        return

    employee_labels = {
        row["employee_id"]: f"{row['employee_id']} - {row['first_name']} {row['last_name']}"
        for row in employee_rows
    }
    selected_employee_id = st.selectbox(
        "Select employee",
        options=list(employee_labels.keys()),
        format_func=lambda emp_id: employee_labels[emp_id],
    )

    if st.button("Run End-to-End Onboarding", use_container_width=True):
        try:
            workflow = orchestrator.run_onboarding(int(selected_employee_id))
            st.success("Onboarding completed through HR, IT, and Training agents.")
            st.write({
                "IT": workflow["it"]["asset_tag"],
                "Training Modules": workflow["training"]["modules"],
            })
            st.rerun()
        except Exception as exc:
            st.error(f"Onboarding failed: {exc}")


def render_projects(registry: MCPRegistry) -> None:
    st.subheader("Projects")

    project_rows = registry.execute_tool(
        "db_read",
        {
            "query": """
                SELECT p.project_id, p.project_name, p.client, p.tech_stack, p.status,
                       COUNT(ep.assignment_id) AS assigned_employees
                FROM Projects p
                LEFT JOIN EmployeeProjects ep
                    ON ep.project_id = p.project_id
                    AND ep.status = 'Active'
                GROUP BY p.project_id
                ORDER BY p.project_id
            """
        },
    )

    st.dataframe(to_df(project_rows), use_container_width=True, hide_index=True)


def render_assign_project(orchestrator: AgentOrchestrator, registry: MCPRegistry) -> None:
    st.subheader("Assign Project")

    employees = registry.execute_tool(
        "db_read",
        {
            "query": "SELECT employee_id, first_name, last_name FROM Employees ORDER BY employee_id",
        },
    )
    projects = registry.execute_tool(
        "db_read",
        {
            "query": "SELECT project_id, project_name FROM Projects ORDER BY project_id",
        },
    )

    if not employees or not projects:
        st.info("Employees and projects must exist before assignment.")
        return

    employee_map = {
        row["employee_id"]: f"{row['employee_id']} - {row['first_name']} {row['last_name']}"
        for row in employees
    }
    project_map = {row["project_id"]: f"{row['project_id']} - {row['project_name']}" for row in projects}

    with st.form("assign_project_form"):
        employee_id = st.selectbox(
            "Employee",
            options=list(employee_map.keys()),
            format_func=lambda emp_id: employee_map[emp_id],
        )
        project_id = st.selectbox(
            "Project",
            options=list(project_map.keys()),
            format_func=lambda proj_id: project_map[proj_id],
        )
        role_on_project = st.text_input("Role on Project", value="Engineer")
        submitted = st.form_submit_button("Assign Project and Trigger Skill Gap Assessment")

    if submitted:
        role = sanitize_text(role_on_project, 100)
        if not role:
            st.error("Role on project is required.")
            return

        try:
            outcome = orchestrator.assign_project_and_trigger_skill_gap(
                employee_id=int(employee_id),
                project_id=int(project_id),
                role_on_project=role,
            )
            assessment_id = int(outcome["assessment"]["assessment_id"])
            st.session_state.pending_assessment_id = assessment_id
            st.session_state.current_page = "Skill Gap Assessment"
            st.success(
                f"Project assigned and Skill Gap Assessment #{assessment_id} generated. Redirecting to assessment form."
            )
            st.rerun()
        except Exception as exc:
            st.error(f"Project assignment failed: {exc}")


def render_recommendation_block(recommendation: dict[str, Any]) -> None:
    st.markdown("### Skill Gap Recommendation")
    st.markdown(
        f"""
        <div class="result-card">
            <h4>Final Recommendation</h4>
            <p>{recommendation.get('final_recommendation', 'No recommendation available.')}</p>
            <h5>Reflection</h5>
            <p>{recommendation.get('reflection_notes', 'No reflection notes available.')}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    analysis = recommendation.get("analysis", {})
    strengths = analysis.get("strengths", [])
    skill_gaps = analysis.get("skill_gaps", [])

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Strengths**")
        if strengths:
            for item in strengths:
                st.markdown(f"- {item}")
        else:
            st.caption("No strengths recorded.")

    with col2:
        st.markdown("**Improvement Areas**")
        if skill_gaps:
            for item in skill_gaps:
                st.markdown(f"- {item}")
        else:
            st.caption("No skill gaps recorded.")

    certs = recommendation.get("certifications", [])
    courses = recommendation.get("courses", [])

    st.markdown("**Recommended Certifications**")
    if certs:
        for cert in certs:
            st.markdown(f"- {cert}")
    else:
        st.caption("No certifications suggested.")

    st.markdown("**Recommended Courses**")
    if courses:
        for course in courses:
            if isinstance(course, dict):
                title = course.get("title", "Untitled")
                provider = course.get("provider", "Provider")
                platform = course.get("platform", "Platform")
                url = course.get("url", "")
                if url:
                    st.markdown(f"- [{title}]({url}) ({provider}, {platform})")
                else:
                    st.markdown(f"- {title} ({provider}, {platform})")
    else:
        st.caption("No courses suggested.")


def render_skill_gap_assessment(orchestrator: AgentOrchestrator, registry: MCPRegistry) -> None:
    st.subheader("Skill Gap Assessment")

    pending_rows = registry.execute_tool(
        "db_read",
        {
            "query": """
                SELECT a.assessment_id, a.employee_id, a.project_id, a.created_at,
                       e.first_name || ' ' || e.last_name AS employee_name,
                       p.project_name
                FROM Assessments a
                JOIN Employees e ON a.employee_id = e.employee_id
                JOIN Projects p ON a.project_id = p.project_id
                WHERE a.status = 'Pending'
                ORDER BY a.assessment_id DESC
            """
        },
    )

    form_tab, history_tab = st.tabs(["Assessment Form", "Recommendation History"])

    with form_tab:
        if not pending_rows:
            st.info("No pending assessments. Assign a project to trigger a new skill gap assessment.")
        else:
            option_map = {
                row["assessment_id"]: (
                    f"Assessment {row['assessment_id']} | {row['employee_name']} | {row['project_name']}"
                )
                for row in pending_rows
            }
            assessment_ids = list(option_map.keys())

            default_assessment_id = st.session_state.get("pending_assessment_id")
            default_index = 0
            if default_assessment_id in assessment_ids:
                default_index = assessment_ids.index(default_assessment_id)

            selected_assessment_id = st.selectbox(
                "Select assessment",
                options=assessment_ids,
                index=default_index,
                format_func=lambda item: option_map[item],
            )

            questions = registry.execute_tool(
                "db_read",
                {
                    "query": """
                        SELECT question_id, question_text
                        FROM AssessmentQuestions
                        WHERE assessment_id = ?
                        ORDER BY question_id
                    """,
                    "params": (selected_assessment_id,),
                },
            )

            if not questions:
                st.warning("This assessment has no generated questions.")
            else:
                with st.form(f"assessment_answers_form_{selected_assessment_id}"):
                    answers: dict[int, str] = {}
                    for index, question in enumerate(questions, start=1):
                        answers[question["question_id"]] = st.text_area(
                            f"Q{index}. {question['question_text']}",
                            height=110,
                            key=f"answer_{selected_assessment_id}_{question['question_id']}",
                        )
                    submitted = st.form_submit_button("Submit Assessment and Generate Recommendations")

                if submitted:
                    if any(not sanitize_text(text) for text in answers.values()):
                        st.error("Please answer all questions before submission.")
                    else:
                        try:
                            recommendation = orchestrator.submit_assessment_answers(
                                int(selected_assessment_id),
                                answers,
                            )
                            st.session_state.last_recommendation = recommendation
                            st.session_state.pending_assessment_id = None
                            st.success("Assessment submitted and recommendation generated.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Failed to evaluate assessment: {exc}")

        if st.session_state.get("last_recommendation"):
            render_recommendation_block(st.session_state["last_recommendation"])

    with history_tab:
        recommendations = registry.execute_tool(
            "db_read",
            {
                "query": """
                    SELECT r.recommendation_id, r.assessment_id, r.employee_id, r.project_id,
                           r.recommendation_text, r.certifications, r.courses, r.created_at, r.reflection_notes,
                           e.first_name || ' ' || e.last_name AS employee_name,
                           p.project_name
                    FROM Recommendations r
                    JOIN Employees e ON r.employee_id = e.employee_id
                    JOIN Projects p ON r.project_id = p.project_id
                    ORDER BY r.recommendation_id DESC
                """
            },
        )
        if not recommendations:
            st.caption("No recommendation history available yet.")
        else:
            display_rows = [
                {
                    "recommendation_id": row["recommendation_id"],
                    "assessment_id": row["assessment_id"],
                    "employee": row["employee_name"],
                    "project": row["project_name"],
                    "created_at": row["created_at"],
                }
                for row in recommendations
            ]
            st.dataframe(to_df(display_rows), use_container_width=True, hide_index=True)

            selected_id = st.selectbox(
                "Inspect recommendation",
                options=[row["recommendation_id"] for row in recommendations],
                format_func=lambda value: f"Recommendation #{value}",
            )
            selected = next(item for item in recommendations if item["recommendation_id"] == selected_id)

            st.markdown("#### Recommendation Detail")
            st.write(selected["recommendation_text"])
            st.markdown("**Reflection Notes**")
            st.write(selected["reflection_notes"] or "No reflection notes captured.")

            certs = parse_json_field(selected["certifications"], [])
            courses = parse_json_field(selected["courses"], [])

            st.markdown("**Certifications**")
            if certs:
                for cert in certs:
                    st.markdown(f"- {cert}")
            else:
                st.caption("No certifications recorded.")

            st.markdown("**Courses**")
            if courses:
                for course in courses:
                    if isinstance(course, dict):
                        title = course.get("title", "Untitled")
                        provider = course.get("provider", "")
                        platform = course.get("platform", "")
                        url = course.get("url", "")
                        if url:
                            st.markdown(f"- [{title}]({url}) ({provider}, {platform})")
                        else:
                            st.markdown(f"- {title} ({provider}, {platform})")
            else:
                st.caption("No courses recorded.")


def render_audit_logs(registry: MCPRegistry) -> None:
    st.subheader("Audit Logs")

    rows = registry.execute_tool(
        "db_read",
        {
            "query": """
                SELECT log_id, timestamp, agent_name, action, employee_id, project_id, metadata
                FROM AuditLogs
                ORDER BY log_id DESC
            """
        },
    )

    if not rows:
        st.info("No audit logs available yet.")
        return

    all_agents = sorted({row["agent_name"] for row in rows})
    selected_agent = st.selectbox("Filter by agent", ["All"] + all_agents)

    filtered_rows = rows
    if selected_agent != "All":
        filtered_rows = [row for row in rows if row["agent_name"] == selected_agent]

    display_rows = []
    for row in filtered_rows:
        payload = parse_json_field(row["metadata"], {})
        display_rows.append(
            {
                "log_id": row["log_id"],
                "timestamp": row["timestamp"],
                "agent_name": row["agent_name"],
                "action": row["action"],
                "employee_id": row["employee_id"],
                "project_id": row["project_id"],
                "metadata": json.dumps(payload, ensure_ascii=True),
            }
        )

    st.dataframe(to_df(display_rows), use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(
        page_title="Agentic AI Employee Onboarding",
        page_icon="AO",
        layout="wide",
    )
    load_css()
    init_session_state()

    orchestrator, registry, _gemini_client = bootstrap()

    if not render_auth_gate():
        return

    render_header()

    pages = [
        "Dashboard",
        "Employees",
        "Projects",
        "Assign Project",
        "Skill Gap Assessment",
        "Audit Logs",
    ]

    current_page = st.session_state.get("current_page", "Dashboard")
    if current_page not in pages:
        current_page = "Dashboard"

    selected_page = st.sidebar.radio(
        "Navigation",
        options=pages,
        index=pages.index(current_page),
    )
    st.session_state.current_page = selected_page

    if selected_page == "Dashboard":
        render_dashboard(registry)
    elif selected_page == "Employees":
        render_employees(orchestrator, registry)
    elif selected_page == "Projects":
        render_projects(registry)
    elif selected_page == "Assign Project":
        render_assign_project(orchestrator, registry)
    elif selected_page == "Skill Gap Assessment":
        render_skill_gap_assessment(orchestrator, registry)
    elif selected_page == "Audit Logs":
        render_audit_logs(registry)


if __name__ == "__main__":
    main()
