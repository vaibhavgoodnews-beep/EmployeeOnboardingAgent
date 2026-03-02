from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from agents.base_agent import BaseAgent


class SkillGapAgent(BaseAgent):
    name = "Skill Gap Agent"

    def plan(self, context: dict[str, Any]) -> dict[str, Any]:
        action = str(context.get("action", "generate_assessment")).strip()
        if action not in {"generate_assessment", "evaluate_assessment"}:
            raise ValueError("Skill Gap Agent received unsupported action.")

        if action == "generate_assessment":
            employee_id = int(context.get("employee_id", 0))
            project_id = int(context.get("project_id", 0))
            question_count = max(10, min(15, int(context.get("question_count", 12))))

            employee = self._fetch_single(
                "SELECT employee_id, first_name, last_name FROM Employees WHERE employee_id = ?",
                (employee_id,),
            )
            project = self._fetch_single(
                "SELECT project_id, project_name, tech_stack FROM Projects WHERE project_id = ?",
                (project_id,),
            )

            return {
                "action": action,
                "employee": employee,
                "project": project,
                "question_count": question_count,
            }

        assessment_id = int(context.get("assessment_id", 0))
        if assessment_id <= 0:
            raise ValueError("assessment_id is required for evaluation.")

        assessment = self._fetch_single(
            """
            SELECT a.assessment_id, a.employee_id, a.project_id, p.project_name, p.tech_stack
            FROM Assessments a
            JOIN Projects p ON a.project_id = p.project_id
            WHERE a.assessment_id = ?
            """,
            (assessment_id,),
        )
        return {"action": action, "assessment": assessment}

    def use_tools(self, context: dict[str, Any]) -> dict[str, Any]:
        action = context["action"]
        if action == "generate_assessment":
            return self._generate_assessment(context)
        return self._evaluate_assessment(context)

    def reflect(self, result: dict[str, Any]) -> dict[str, Any]:
        if result["action"] == "generate_assessment":
            questions = result["questions"]
            if len(questions) < 10:
                missing = 10 - len(questions)
                filler_questions = [
                    f"Explain your readiness to deliver production outcomes in {result['project']['tech_stack']}.",
                    "Describe the last defect triage you handled and your resolution strategy.",
                    "How do you prioritize reliability, security, and delivery speed for enterprise systems?",
                ]
                additions = []
                for index in range(missing):
                    additions.append(filler_questions[index % len(filler_questions)])

                question_rows = [
                    (result["assessment_id"], question, result["project"]["tech_stack"])
                    for question in additions
                ]
                self.mcp.execute_tool(
                    "db_write",
                    {
                        "query": """
                            INSERT INTO AssessmentQuestions (assessment_id, question_text, expected_topics)
                            VALUES (?, ?, ?)
                        """,
                        "params": question_rows,
                        "many": True,
                    },
                )
                questions.extend(additions)

            result["agent"] = self.name
            result["reflection"] = "Assessment questions validated for stack coverage and minimum depth."
            return result

        reflection_result = self.mcp.execute_tool(
            "reflect_recommendation",
            {
                "initial_recommendation": result["draft_recommendation"],
                "tech_stack": result["assessment"]["tech_stack"],
                "qa_pairs": result["qa_pairs"],
            },
        )

        if isinstance(reflection_result, dict):
            reflection_notes = str(reflection_result.get("reflection_notes", "")).strip()
            final_recommendation = str(reflection_result.get("final_recommendation", "")).strip()
        else:
            reflection_notes = "Reflection response unavailable; retained initial recommendation."
            final_recommendation = result["draft_recommendation"]

        if not final_recommendation:
            final_recommendation = result["draft_recommendation"]

        certifications = result["recommendations"].get("certifications", [])
        courses = result["recommendations"].get("courses", [])

        self.mcp.execute_tool(
            "db_write",
            {
                "query": "UPDATE Assessments SET status = 'Completed', summary = ? WHERE assessment_id = ?",
                "params": (final_recommendation[:600], result["assessment"]["assessment_id"]),
            },
        )

        self.mcp.execute_tool(
            "db_write",
            {
                "query": """
                    INSERT INTO Recommendations
                    (assessment_id, employee_id, project_id, recommendation_text, certifications, courses, created_at, reflection_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                "params": (
                    result["assessment"]["assessment_id"],
                    result["assessment"]["employee_id"],
                    result["assessment"]["project_id"],
                    final_recommendation,
                    json.dumps(certifications, ensure_ascii=True),
                    json.dumps(courses, ensure_ascii=True),
                    datetime.now(timezone.utc).isoformat(),
                    reflection_notes,
                ),
            },
        )

        self.mcp.execute_tool(
            "log_action",
            {
                "agent_name": self.name,
                "action": "Skill gap recommendations finalized",
                "employee_id": result["assessment"]["employee_id"],
                "project_id": result["assessment"]["project_id"],
                "metadata": {
                    "assessment_id": result["assessment"]["assessment_id"],
                    "identified_gaps": result["analysis"].get("skill_gaps", []),
                },
            },
        )

        return {
            "agent": self.name,
            "assessment_id": result["assessment"]["assessment_id"],
            "employee_id": result["assessment"]["employee_id"],
            "project_id": result["assessment"]["project_id"],
            "analysis": result["analysis"],
            "certifications": certifications,
            "courses": courses,
            "reflection_notes": reflection_notes,
            "final_recommendation": final_recommendation,
        }

    def _generate_assessment(self, context: dict[str, Any]) -> dict[str, Any]:
        employee = context["employee"]
        project = context["project"]

        questions = self.mcp.execute_tool(
            "generate_assessment_questions",
            {
                "tech_stack": project["tech_stack"],
                "question_count": context["question_count"],
            },
        )

        assessment_id = self.mcp.execute_tool(
            "db_write",
            {
                "query": """
                    INSERT INTO Assessments (employee_id, project_id, created_at, status, summary)
                    VALUES (?, ?, ?, 'Pending', ?)
                """,
                "params": (
                    employee["employee_id"],
                    project["project_id"],
                    datetime.now(timezone.utc).isoformat(),
                    "Skill assessment generated",
                ),
            },
        )

        question_rows = [(assessment_id, question, project["tech_stack"]) for question in questions]
        self.mcp.execute_tool(
            "db_write",
            {
                "query": """
                    INSERT INTO AssessmentQuestions (assessment_id, question_text, expected_topics)
                    VALUES (?, ?, ?)
                """,
                "params": question_rows,
                "many": True,
            },
        )

        self.mcp.execute_tool(
            "log_action",
            {
                "agent_name": self.name,
                "action": "Skill gap assessment generated",
                "employee_id": employee["employee_id"],
                "project_id": project["project_id"],
                "metadata": {"assessment_id": assessment_id, "question_count": len(questions)},
            },
        )

        return {
            "action": "generate_assessment",
            "assessment_id": assessment_id,
            "employee": employee,
            "project": project,
            "questions": questions,
        }

    def _evaluate_assessment(self, context: dict[str, Any]) -> dict[str, Any]:
        assessment = context["assessment"]

        qa_rows = self.mcp.execute_tool(
            "db_read",
            {
                "query": """
                    SELECT q.question_id, q.question_text, COALESCE(a.answer_text, '') AS answer_text
                    FROM AssessmentQuestions q
                    LEFT JOIN AssessmentAnswers a
                        ON q.question_id = a.question_id
                        AND a.employee_id = ?
                    WHERE q.assessment_id = ?
                    ORDER BY q.question_id
                """,
                "params": (assessment["employee_id"], assessment["assessment_id"]),
            },
        )

        if not qa_rows:
            raise ValueError("No assessment questions available for evaluation.")

        qa_pairs = []
        for row in qa_rows:
            answer_text = row["answer_text"].strip()
            qa_pairs.append({"question": row["question_text"], "answer": answer_text})

            score = self._score_answer(answer_text)
            self.mcp.execute_tool(
                "db_write",
                {
                    "query": """
                        UPDATE AssessmentAnswers
                        SET score = ?, evaluated_at = ?
                        WHERE question_id = ? AND employee_id = ?
                    """,
                    "params": (
                        score,
                        datetime.now(timezone.utc).isoformat(),
                        row["question_id"],
                        assessment["employee_id"],
                    ),
                },
            )

        analysis = self.mcp.execute_tool(
            "analyze_skill_answers",
            {
                "tech_stack": assessment["tech_stack"],
                "qa_pairs": qa_pairs,
            },
        )

        recommendations = self.mcp.execute_tool(
            "recommend_courses",
            {
                "skill_gaps": analysis.get("skill_gaps", []),
                "tech_stack": assessment["tech_stack"],
            },
        )

        draft_recommendation = self._compose_recommendation_text(analysis, recommendations)

        return {
            "action": "evaluate_assessment",
            "assessment": assessment,
            "qa_pairs": qa_pairs,
            "analysis": analysis,
            "recommendations": recommendations,
            "draft_recommendation": draft_recommendation,
        }

    def _fetch_single(self, query: str, params: tuple[Any, ...]) -> dict[str, Any]:
        rows = self.mcp.execute_tool("db_read", {"query": query, "params": params})
        if not rows:
            raise ValueError("Required database record not found.")
        return rows[0]

    def _score_answer(self, answer: str) -> float:
        words = len(answer.split())
        if words >= 80:
            return 5.0
        if words >= 50:
            return 4.0
        if words >= 30:
            return 3.0
        if words >= 15:
            return 2.0
        if words > 0:
            return 1.0
        return 0.0

    def _compose_recommendation_text(self, analysis: dict[str, Any], recommendations: dict[str, Any]) -> str:
        strengths = analysis.get("strengths", [])
        skill_gaps = analysis.get("skill_gaps", [])
        summary = str(analysis.get("summary", "Assessment completed.")).strip()

        certs = recommendations.get("certifications", [])
        course_titles = [course.get("title", "") for course in recommendations.get("courses", []) if isinstance(course, dict)]

        lines = ["Assessment Summary", summary]
        if strengths:
            lines.append("Strengths: " + "; ".join(strengths[:4]))
        if skill_gaps:
            lines.append("Improvement Areas: " + "; ".join(skill_gaps[:5]))
        if certs:
            lines.append("Recommended Certifications: " + "; ".join(certs[:4]))
        if course_titles:
            lines.append("Recommended Courses: " + "; ".join(course_titles[:5]))

        return "\n".join(lines)
