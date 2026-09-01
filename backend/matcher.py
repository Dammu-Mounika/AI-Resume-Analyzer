"""
Resume vs job description skill matching engine.
"""

from dataclasses import dataclass, field
from typing import Any, Dict

from backend.keyword_extractor import ExtractedSkills


@dataclass
class MatchResult:
    """Result of comparing resume skills against job requirements."""

    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    total_required: int = 0
    matched_count: int = 0
    missing_count: int = 0
    keyword_match_percentage: float = 0.0
    resume_skills_flat: list[str] = field(default_factory=list)
    job_skills_flat: list[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "total_required": self.total_required,
            "matched_count": self.matched_count,
            "missing_count": self.missing_count,
            "keyword_match_percentage": self.keyword_match_percentage,
            "resume_skills": self.resume_skills_flat,
            "job_skills": self.job_skills_flat,
        }


def compare_skills(resume_skills: ExtractedSkills, job_skills: ExtractedSkills) -> MatchResult:
    """
    Compare resume skills against job required skills.

    Keyword Match Score = (Matched / Total Required) × 100
    """
    resume_set = {s.lower(): s for s in resume_skills.all_skills()}
    job_set = {s.lower(): s for s in job_skills.all_skills()}

    resume_flat = sorted(resume_set.values())
    job_flat = sorted(job_set.values())

    if not job_flat:
        return MatchResult(
            matched_skills=[],
            missing_skills=[],
            total_required=0,
            matched_count=0,
            missing_count=0,
            keyword_match_percentage=0.0,
            resume_skills_flat=resume_flat,
            job_skills_flat=job_flat,
        )

    matched: list[str] = []
    missing: list[str] = []

    for key, canonical in job_set.items():
        if key in resume_set:
            matched.append(canonical)
        else:
            missing.append(canonical)

    matched.sort()
    missing.sort()
    total = len(job_flat)
    matched_count = len(matched)
    percentage = round((matched_count / total) * 100, 1) if total > 0 else 0.0

    return MatchResult(
        matched_skills=matched,
        missing_skills=missing,
        total_required=total,
        matched_count=matched_count,
        missing_count=len(missing),
        keyword_match_percentage=percentage,
        resume_skills_flat=resume_flat,
        job_skills_flat=job_flat,
    )
