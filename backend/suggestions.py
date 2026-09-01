"""
Skill gap analysis and resume improvement suggestions.

Suggestions NEVER encourage falsely claiming skills.
"""

from typing import Dict, List
from backend.keyword_extractor import count_skill_mentions


def analyze_skill_gap(job_description: str, missing_skills: List[str]) -> Dict[str, List[str]]:
    """
    Categorize missing skills by priority based on job description frequency.

    HIGH: mentioned 2+ times
    MEDIUM: mentioned exactly once
    LOW: extracted but weak signal (fallback)
    """
    high: List[str] = []
    medium: List[str] = []
    low: List[str] = []

    for skill in missing_skills:
        mentions = count_skill_mentions(job_description, skill)
        if mentions >= 2:
            high.append(skill)
        elif mentions == 1:
            medium.append(skill)
        else:
            low.append(skill)

    return {
        "high_priority": sorted(high),
        "medium_priority": sorted(medium),
        "low_priority": sorted(low),
    }


def _suggestion_for_skill(skill: str) -> str:
    """Generate an ethical, skill-specific improvement suggestion."""
    skill_lower = skill.lower()

    templates = {
        "docker": (
            "If you genuinely have Docker experience, highlight it in a relevant "
            "Projects or Experience section with the containerized apps you built."
        ),
        "aws": (
            "If you have AWS experience, mention the specific services you used "
            "(e.g., EC2, S3, Lambda) rather than just listing 'AWS'."
        ),
        "rest api": (
            "If you have worked with REST APIs, describe the API development work "
            "clearly — endpoints built, methods used, and tools involved."
        ),
        "git": (
            "If you use Git regularly, mention collaborative workflows such as "
            "branching, pull requests, or contributions on GitHub."
        ),
        "fastapi": (
            "If you have FastAPI experience, describe a project where you built "
            "APIs including routes, validation, and testing."
        ),
        "sql": (
            "If you have SQL experience, mention specific databases and example "
            "queries or schema design work in your Experience section."
        ),
        "python": (
            "If Python is a core skill for you, ensure it appears prominently "
            "in your Skills and Experience sections with concrete examples."
        ),
        "machine learning": (
            "If you have ML experience, describe the models, datasets, or "
            "projects you worked on — only include what you can explain in an interview."
        ),
    }

    for key, suggestion in templates.items():
        if key in skill_lower:
            return suggestion

    return (
        f"If you genuinely have {skill} experience, consider highlighting it "
        f"with a specific project or role where you used it. "
        f"Only include skills you can confidently discuss in an interview."
    )


def generate_suggestions(
    missing_skills: List[str],
    keyword_score: float,
    skill_gap: Dict[str, List[str]],
) -> List[str]:
    """
    Generate actionable resume improvement suggestions.

    Prioritizes high-priority gaps first. Never recommends adding fake skills.
    """
    suggestions: List[str] = []

    priority_order = (
        skill_gap.get("high_priority", [])
        + skill_gap.get("medium_priority", [])
        + skill_gap.get("low_priority", [])
    )

    seen: set[str] = set()
    for skill in priority_order:
        key = skill.lower()
        if key not in seen:
            suggestions.append(_suggestion_for_skill(skill))
            seen.add(key)

    if keyword_score < 50 and missing_skills:
        suggestions.insert(
            0,
            "Your keyword match is below 50%. Review the job description and, "
            "where you honestly have the experience, mirror its language in your resume.",
        )
    elif not missing_skills and keyword_score >= 80:
        suggestions.append(
            "Strong keyword match! Consider tailoring your summary section to "
            "emphasize the matched skills most relevant to this role.",
        )
    elif not missing_skills:
        suggestions.append(
            "Good skill alignment. Fine-tune your resume summary to reflect "
            "the top requirements mentioned in the job description.",
        )

    if not suggestions:
        suggestions.append(
            "Review the job description and ensure your resume clearly reflects "
            "skills you genuinely possess. Never add skills you cannot demonstrate.",
        )

    return suggestions[:8]
