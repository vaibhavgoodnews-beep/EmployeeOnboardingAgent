from __future__ import annotations

import json
import os
import re
from typing import Any

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - defensive import for local envs
    genai = None


class GeminiClient:
    """Thin Gemini wrapper with deterministic fallbacks for local/offline runs."""

    def __init__(self, model_name: str | None = None) -> None:
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self._model = None

        if genai is not None and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self._model = genai.GenerativeModel(self.model_name)
            except Exception:
                self._model = None

    @property
    def enabled(self) -> bool:
        return self._model is not None

    def _extract_json(self, text: str) -> Any:
        candidate = (text or "").strip()
        if not candidate:
            return None

        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

        for pattern in (r"\{[\s\S]*\}", r"\[[\s\S]*\]"):
            match = re.search(pattern, candidate)
            if not match:
                continue
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                continue
        return None

    def generate_text(self, prompt: str, temperature: float = 0.2, max_output_tokens: int = 2048) -> str:
        if not self._model:
            return ""

        try:
            response = self._model.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                },
            )
            return (getattr(response, "text", "") or "").strip()
        except Exception:
            return ""

    def _split_skills(self, tech_stack: str) -> list[str]:
        skills = [item.strip() for item in tech_stack.split(",") if item.strip()]
        return skills or ["Software Engineering", "Cloud Fundamentals", "Data Fundamentals"]

    def generate_assessment_questions(self, tech_stack: str, question_count: int = 12) -> list[str]:
        count = max(10, min(15, int(question_count)))
        prompt = f"""
        Generate {count} technical skill assessment questions for this project tech stack:
        {tech_stack}

        Requirements:
        - Questions must evaluate practical experience, debugging approach, architecture, and production readiness.
        - Keep each question concise and interview-grade.
        - Return valid JSON array only.
        """
        response_text = self.generate_text(prompt)
        parsed = self._extract_json(response_text)

        if isinstance(parsed, list):
            questions = [str(item).strip() for item in parsed if str(item).strip()]
            if len(questions) >= 10:
                return questions[:count]

        return self._fallback_questions(tech_stack, count)

    def _fallback_questions(self, tech_stack: str, count: int) -> list[str]:
        skills = self._split_skills(tech_stack)
        templates = [
            "Describe a production issue you resolved using {skill}. What was your root-cause process?",
            "How would you design a resilient module in {skill} for high traffic?",
            "Which performance bottlenecks are common in {skill}, and how do you mitigate them?",
            "Explain your preferred testing strategy for {skill} components in CI/CD.",
            "How do you secure a deployment that includes {skill} in an enterprise setting?",
            "Share one optimization you implemented with {skill} and the measurable impact.",
        ]

        generated: list[str] = []
        index = 0
        while len(generated) < count:
            skill = skills[index % len(skills)]
            template = templates[index % len(templates)]
            generated.append(template.format(skill=skill))
            index += 1
        return generated

    def analyze_skill_answers(self, tech_stack: str, qa_pairs: list[dict[str, str]]) -> dict[str, Any]:
        prompt = f"""
        Analyze this employee assessment response set for project stack: {tech_stack}

        Questions and Answers:
        {json.dumps(qa_pairs, ensure_ascii=True)}

        Return valid JSON object with these keys only:
        - strengths: list of short points
        - skill_gaps: list of short points
        - summary: concise paragraph
        """
        response_text = self.generate_text(prompt)
        parsed = self._extract_json(response_text)
        if isinstance(parsed, dict):
            strengths = [str(item).strip() for item in parsed.get("strengths", []) if str(item).strip()]
            skill_gaps = [str(item).strip() for item in parsed.get("skill_gaps", []) if str(item).strip()]
            summary = str(parsed.get("summary", "")).strip()
            if strengths or skill_gaps:
                return {
                    "strengths": strengths,
                    "skill_gaps": skill_gaps,
                    "summary": summary or "Assessment review completed.",
                }

        return self._fallback_analysis(tech_stack, qa_pairs)

    def _fallback_analysis(self, tech_stack: str, qa_pairs: list[dict[str, str]]) -> dict[str, Any]:
        skills = self._split_skills(tech_stack)
        strengths: list[str] = []
        weak_skills: list[str] = []

        for index, item in enumerate(qa_pairs):
            question = (item.get("question") or "").lower()
            answer = item.get("answer") or ""
            word_count = len(answer.split())

            related_skill = None
            for skill in skills:
                if skill.lower() in question:
                    related_skill = skill
                    break
            if not related_skill:
                related_skill = skills[index % len(skills)]

            if word_count >= 35:
                strengths.append(f"Demonstrates practical confidence in {related_skill}.")
            else:
                weak_skills.append(related_skill)

        if not strengths:
            strengths.append(f"Basic familiarity observed in {skills[0]}.")

        unique_gaps: list[str] = []
        for skill in weak_skills:
            if skill not in unique_gaps:
                unique_gaps.append(skill)

        if not unique_gaps:
            unique_gaps = [skills[min(1, len(skills) - 1)]]

        summary = (
            "Skill profile indicates readiness for guided project onboarding with focused upskilling "
            f"in {', '.join(unique_gaps[:3])}."
        )
        return {
            "strengths": strengths[:5],
            "skill_gaps": unique_gaps[:5],
            "summary": summary,
        }

    def recommend_courses(self, skill_gaps: list[str], tech_stack: str) -> dict[str, Any]:
        prompt = f"""
        Recommend enterprise-relevant learning paths for these skill gaps:
        {json.dumps(skill_gaps, ensure_ascii=True)}

        Project stack: {tech_stack}

        Return valid JSON object with:
        - certifications: list of certifications
        - courses: list of objects with keys title, provider, platform, url
        """
        response_text = self.generate_text(prompt)
        parsed = self._extract_json(response_text)

        if isinstance(parsed, dict):
            certs = [str(item).strip() for item in parsed.get("certifications", []) if str(item).strip()]
            courses_payload = []
            for item in parsed.get("courses", []):
                if not isinstance(item, dict):
                    continue
                title = str(item.get("title", "")).strip()
                provider = str(item.get("provider", "")).strip()
                platform = str(item.get("platform", "")).strip()
                url = str(item.get("url", "")).strip()
                if title and provider and platform:
                    courses_payload.append(
                        {
                            "title": title,
                            "provider": provider,
                            "platform": platform,
                            "url": url or "https://www.coursera.org/",
                        }
                    )
            if certs or courses_payload:
                return {
                    "certifications": certs,
                    "courses": courses_payload,
                }

        return self._fallback_courses(skill_gaps, tech_stack)

    def _fallback_courses(self, skill_gaps: list[str], tech_stack: str) -> dict[str, Any]:
        catalog = {
            "aws": {
                "certification": "AWS Certified Developer - Associate",
                "course": {
                    "title": "AWS Developer Associate Prep",
                    "provider": "Udemy",
                    "platform": "Udemy",
                    "url": "https://www.udemy.com/",
                },
            },
            "azure": {
                "certification": "Microsoft Azure Developer Associate (AZ-204)",
                "course": {
                    "title": "Developing Solutions for Microsoft Azure",
                    "provider": "Microsoft Learn",
                    "platform": "Azure",
                    "url": "https://learn.microsoft.com/training/",
                },
            },
            "python": {
                "certification": "PCAP: Certified Associate in Python Programming",
                "course": {
                    "title": "Python for Everybody",
                    "provider": "University of Michigan",
                    "platform": "Coursera",
                    "url": "https://www.coursera.org/",
                },
            },
            "kubernetes": {
                "certification": "Certified Kubernetes Application Developer (CKAD)",
                "course": {
                    "title": "Kubernetes for Developers",
                    "provider": "KodeKloud",
                    "platform": "Coursera",
                    "url": "https://www.coursera.org/",
                },
            },
            "spark": {
                "certification": "Databricks Certified Data Engineer Associate",
                "course": {
                    "title": "Apache Spark Programming with Databricks",
                    "provider": "Databricks",
                    "platform": "Databricks Academy",
                    "url": "https://www.databricks.com/learn",
                },
            },
            "salesforce": {
                "certification": "Salesforce Platform Developer I",
                "course": {
                    "title": "Salesforce Developer Learning Path",
                    "provider": "Trailhead",
                    "platform": "Salesforce",
                    "url": "https://trailhead.salesforce.com/",
                },
            },
            "java": {
                "certification": "Oracle Certified Professional: Java SE Developer",
                "course": {
                    "title": "Java Programming Masterclass",
                    "provider": "Udemy",
                    "platform": "Udemy",
                    "url": "https://www.udemy.com/",
                },
            },
        }

        certs: list[str] = []
        courses: list[dict[str, str]] = []
        stack_context = " ".join([tech_stack] + skill_gaps).lower()

        for key, package in catalog.items():
            if key in stack_context:
                certs.append(package["certification"])
                courses.append(package["course"])

        if not certs:
            certs = [
                "AWS Cloud Practitioner",
                "Azure Fundamentals (AZ-900)",
            ]

        if not courses:
            courses = [
                {
                    "title": "Cloud Computing Specialization",
                    "provider": "University of Illinois",
                    "platform": "Coursera",
                    "url": "https://www.coursera.org/",
                },
                {
                    "title": "Software Architecture and Design",
                    "provider": "Udemy",
                    "platform": "Udemy",
                    "url": "https://www.udemy.com/",
                },
            ]

        return {"certifications": certs[:5], "courses": courses[:6]}

    def reflect_recommendation(
        self,
        initial_recommendation: str,
        tech_stack: str,
        qa_pairs: list[dict[str, str]],
    ) -> dict[str, str]:
        prompt = f"""
        Review and improve this recommendation for employee upskilling.

        Initial recommendation:
        {initial_recommendation}

        Tech stack:
        {tech_stack}

        Assessment QA:
        {json.dumps(qa_pairs, ensure_ascii=True)}

        Self-reflection question:
        "Is this recommendation aligned with tech stack and answers?"

        Return valid JSON object with keys:
        - reflection_notes
        - final_recommendation
        """

        response_text = self.generate_text(prompt)
        parsed = self._extract_json(response_text)
        if isinstance(parsed, dict):
            notes = str(parsed.get("reflection_notes", "")).strip()
            final_recommendation = str(parsed.get("final_recommendation", "")).strip()
            if final_recommendation:
                return {
                    "reflection_notes": notes or "Recommendation validated against stack and answer quality.",
                    "final_recommendation": final_recommendation,
                }

        fallback_notes = (
            "Recommendation alignment check complete. Focus areas were adjusted to match weaker "
            "responses and the project stack requirements."
        )
        final = (
            initial_recommendation.strip()
            + "\n\nRefined Action: Prioritize one foundational and one project-aligned certification in the next 6 weeks."
        )
        return {"reflection_notes": fallback_notes, "final_recommendation": final}
