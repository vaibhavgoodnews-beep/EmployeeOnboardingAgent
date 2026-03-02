from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agents.base_agent import BaseAgent


class HRAgent(BaseAgent):
    name = "HR Agent"

    def plan(self, context: dict[str, Any]) -> dict[str, Any]:
        action = str(context.get("action", "")).strip()
        if action not in {"create_employee", "update_onboarding", "assign_project"}:
            raise ValueError("HR Agent received unsupported action.")
        return {"action": action, **context}

    def use_tools(self, context: dict[str, Any]) -> dict[str, Any]:
        action = context["action"]

        if action == "create_employee":
            return self._create_employee(context)
        if action == "update_onboarding":
            return self._update_onboarding_status(context)
        return self._assign_project(context)

    def reflect(self, result: dict[str, Any]) -> dict[str, Any]:
        result["agent"] = self.name
        if result.get("status") in {"created", "updated", "assigned"}:
            result["reflection"] = "HR workflow completed with validated records and notifications."
        else:
            result["reflection"] = "HR workflow completed with partial validation."
        return result

    def _create_employee(self, context: dict[str, Any]) -> dict[str, Any]:
        required_fields = ["first_name", "last_name", "email", "department", "role", "joining_date"]
        for field in required_fields:
            value = str(context.get(field, "")).strip()
            if not value:
                raise ValueError(f"Missing required employee field: {field}")

        employee_id = self.mcp.execute_tool(
            "db_write",
            {
                "query": """
                    INSERT INTO Employees (first_name, last_name, email, department, role, joining_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                "params": (
                    str(context["first_name"]).strip()[:50],
                    str(context["last_name"]).strip()[:50],
                    str(context["email"]).strip().lower()[:120],
                    str(context["department"]).strip()[:80],
                    str(context["role"]).strip()[:80],
                    str(context["joining_date"]).strip(),
                    "Pending",
                ),
            },
        )

        self.mcp.execute_tool(
            "log_action",
            {
                "agent_name": self.name,
                "action": "Employee created",
                "employee_id": employee_id,
                "metadata": {"department": context["department"], "role": context["role"]},
            },
        )

        self.mcp.execute_tool(
            "send_email",
            {
                "recipient": str(context["email"]).strip().lower(),
                "subject": "Welcome to the organization",
                "body": "Your employee profile is created. HR onboarding is now in progress.",
            },
        )

        return {"status": "created", "employee_id": employee_id}

    def _update_onboarding_status(self, context: dict[str, Any]) -> dict[str, Any]:
        employee_id = int(context.get("employee_id", 0))
        status = str(context.get("status", "")).strip()
        if employee_id <= 0 or not status:
            raise ValueError("Invalid employee_id or status for onboarding update.")

        self.mcp.execute_tool(
            "db_write",
            {
                "query": "UPDATE Employees SET status = ? WHERE employee_id = ?",
                "params": (status[:40], employee_id),
            },
        )

        self.mcp.execute_tool(
            "log_action",
            {
                "agent_name": self.name,
                "action": "Onboarding status updated",
                "employee_id": employee_id,
                "metadata": {"status": status},
            },
        )

        return {"status": "updated", "employee_id": employee_id, "onboarding_status": status}

    def _assign_project(self, context: dict[str, Any]) -> dict[str, Any]:
        employee_id = int(context.get("employee_id", 0))
        project_id = int(context.get("project_id", 0))
        role_on_project = str(context.get("role_on_project", "")).strip()

        if employee_id <= 0 or project_id <= 0 or not role_on_project:
            raise ValueError("Invalid assignment context. employee_id, project_id, and role_on_project are required.")

        employee_rows = self.mcp.execute_tool(
            "db_read",
            {
                "query": "SELECT employee_id, email FROM Employees WHERE employee_id = ?",
                "params": (employee_id,),
            },
        )
        project_rows = self.mcp.execute_tool(
            "db_read",
            {
                "query": "SELECT project_id, project_name FROM Projects WHERE project_id = ?",
                "params": (project_id,),
            },
        )

        if not employee_rows or not project_rows:
            raise ValueError("Employee or project not found for assignment.")

        self.mcp.execute_tool(
            "db_write",
            {
                "query": """
                    UPDATE EmployeeProjects
                    SET status = 'Completed'
                    WHERE employee_id = ? AND status = 'Active'
                """,
                "params": (employee_id,),
            },
        )

        assignment_id = self.mcp.execute_tool(
            "db_write",
            {
                "query": """
                    INSERT INTO EmployeeProjects (employee_id, project_id, assigned_on, role_on_project, status)
                    VALUES (?, ?, ?, ?, 'Active')
                """,
                "params": (
                    employee_id,
                    project_id,
                    datetime.now(timezone.utc).date().isoformat(),
                    role_on_project[:100],
                ),
            },
        )

        self.mcp.execute_tool(
            "log_action",
            {
                "agent_name": self.name,
                "action": "Project assigned",
                "employee_id": employee_id,
                "project_id": project_id,
                "metadata": {"role_on_project": role_on_project},
            },
        )

        self.mcp.execute_tool(
            "send_email",
            {
                "recipient": employee_rows[0]["email"],
                "subject": "Project assignment confirmation",
                "body": f"You have been assigned to project {project_rows[0]['project_name']} as {role_on_project}.",
            },
        )

        return {
            "status": "assigned",
            "assignment_id": assignment_id,
            "employee_id": employee_id,
            "project_id": project_id,
        }
