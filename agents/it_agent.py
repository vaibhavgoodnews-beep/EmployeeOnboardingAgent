from __future__ import annotations

from typing import Any

from agents.base_agent import BaseAgent


class ITAgent(BaseAgent):
    name = "IT Agent"

    def plan(self, context: dict[str, Any]) -> dict[str, Any]:
        action = str(context.get("action", "")).strip()
        if action not in {"provision_access"}:
            raise ValueError("IT Agent received unsupported action.")
        return {"action": action, **context}

    def use_tools(self, context: dict[str, Any]) -> dict[str, Any]:
        employee_id = int(context.get("employee_id", 0))
        project_id = int(context.get("project_id", 0)) if context.get("project_id") else None
        if employee_id <= 0:
            raise ValueError("employee_id is required for IT provisioning.")

        employee_rows = self.mcp.execute_tool(
            "db_read",
            {
                "query": "SELECT first_name, last_name, email FROM Employees WHERE employee_id = ?",
                "params": (employee_id,),
            },
        )
        if not employee_rows:
            raise ValueError("Employee not found for IT provisioning.")

        employee = employee_rows[0]
        full_name = f"{employee['first_name']} {employee['last_name']}"

        asset_tag = f"LAP-{employee_id:04d}"
        account_pack = {
            "asset_tag": asset_tag,
            "vpn_profile": "CORP-STD",
            "email_group": "all-employees",
            "sso_status": "Enabled",
        }

        self.mcp.execute_tool(
            "log_action",
            {
                "agent_name": self.name,
                "action": "IT provisioning completed",
                "employee_id": employee_id,
                "project_id": project_id,
                "metadata": account_pack,
            },
        )

        self.mcp.execute_tool(
            "send_email",
            {
                "recipient": employee["email"],
                "subject": "IT asset and access provisioned",
                "body": (
                    f"Hi {full_name}, your laptop {asset_tag}, VPN profile, and SSO access are ready."
                ),
            },
        )

        return {
            "status": "provisioned",
            "employee_id": employee_id,
            "project_id": project_id,
            "asset_tag": asset_tag,
            "account_pack": account_pack,
        }

    def reflect(self, result: dict[str, Any]) -> dict[str, Any]:
        result["agent"] = self.name
        result["reflection"] = "Provisioning aligns with baseline enterprise access controls."
        return result
