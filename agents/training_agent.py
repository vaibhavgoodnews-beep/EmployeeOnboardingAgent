from __future__ import annotations

from typing import Any

from agents.base_agent import BaseAgent


class TrainingAgent(BaseAgent):
    name = "Training Agent"

    def plan(self, context: dict[str, Any]) -> dict[str, Any]:
        action = str(context.get("action", "")).strip()
        if action not in {"assign_training"}:
            raise ValueError("Training Agent received unsupported action.")
        return {"action": action, **context}

    def use_tools(self, context: dict[str, Any]) -> dict[str, Any]:
        employee_id = int(context.get("employee_id", 0))
        project_id = int(context.get("project_id", 0)) if context.get("project_id") else None
        if employee_id <= 0:
            raise ValueError("employee_id is required for training assignment.")

        employee_rows = self.mcp.execute_tool(
            "db_read",
            {
                "query": "SELECT first_name, email, role FROM Employees WHERE employee_id = ?",
                "params": (employee_id,),
            },
        )
        if not employee_rows:
            raise ValueError("Employee not found for training assignment.")

        employee = employee_rows[0]
        modules = self._build_modules(employee["role"], project_id)

        self.mcp.execute_tool(
            "log_action",
            {
                "agent_name": self.name,
                "action": "Training plan assigned",
                "employee_id": employee_id,
                "project_id": project_id,
                "metadata": {"modules": modules},
            },
        )

        self.mcp.execute_tool(
            "send_email",
            {
                "recipient": employee["email"],
                "subject": "Mandatory onboarding trainings assigned",
                "body": "Assigned modules: " + ", ".join(modules),
            },
        )

        return {
            "status": "training_assigned",
            "employee_id": employee_id,
            "project_id": project_id,
            "modules": modules,
        }

    def reflect(self, result: dict[str, Any]) -> dict[str, Any]:
        result["agent"] = self.name
        result["reflection"] = "Training plan includes compliance baseline and role-specific upskilling."
        return result

    def _build_modules(self, role: str, project_id: int | None) -> list[str]:
        modules = [
            "Code of Conduct and Compliance",
            "Information Security Awareness",
            "Enterprise Data Protection",
        ]

        normalized_role = (role or "").lower()
        if "engineer" in normalized_role:
            modules.extend([
                "Secure SDLC Fundamentals",
                "Agile Delivery for Distributed Teams",
            ])
        if "manager" in normalized_role:
            modules.append("Delivery Governance and Risk Management")
        if project_id:
            modules.append("Project Context Briefing")

        return modules
