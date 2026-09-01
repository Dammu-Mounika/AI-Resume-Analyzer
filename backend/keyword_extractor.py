"""
Skill and keyword extraction from resume and job description text.

Uses a configurable skills dictionary with alias normalization.
"""

import re
from dataclasses import dataclass, field

from backend.skills_config import SKILL_ALIASES, SKILLS_BY_CATEGORY


@dataclass
class ExtractedSkills:
    """Skills grouped by category."""

    programming: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    databases: list[str] = field(default_factory=list)
    cloud: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    data_ml: list[str] = field(default_factory=list)
    other: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, list[str]]:
        return {
            "programming": self.programming,
            "frameworks": self.frameworks,
            "databases": self.databases,
            "cloud": self.cloud,
            "tools": self.tools,
            "data_ml": self.data_ml,
            "other": self.other,
        }

    def all_skills(self) -> list[str]:
        skills: list[str] = []
        for category in self.to_dict().values():
            skills.extend(category)
        return sorted(set(skills))


def normalize_skill(skill: str) -> str:
    """Normalize a skill name using alias mapping."""
    cleaned = skill.strip()
    alias_key = cleaned.lower()
    return SKILL_ALIASES.get(alias_key, cleaned)
<<<<<<< HEAD


def _find_category(canonical: str) -> str:
    for category, skills in SKILLS_BY_CATEGORY.items():
        if canonical in skills or canonical.lower() in [s.lower() for s in skills]:
            return category
    return "other"


def _build_skill_patterns() -> list[tuple[str, str, str]]:
    """
    Build searchable patterns: (pattern_text, canonical_name, category).
    Longer patterns are checked first to avoid partial matches (e.g. Java vs JavaScript).
    """
    patterns: list[tuple[str, str, str]] = []
    seen_patterns: set[str] = set()

    # Base skills from category mapping
    for category, skills in SKILLS_BY_CATEGORY.items():
        for skill in skills:
            pattern_text = skill.lower()
            if pattern_text not in seen_patterns:
                canonical = normalize_skill(skill)
                patterns.append((pattern_text, canonical, category))
                seen_patterns.add(pattern_text)

    # Alias mappings
    for alias, canonical in SKILL_ALIASES.items():
        pattern_text = alias.lower()
        if pattern_text not in seen_patterns:
            category = _find_category(canonical)
            patterns.append((pattern_text, canonical, category))
            seen_patterns.add(pattern_text)

    # Sort longest pattern text first to prevent substring false positives
    patterns.sort(key=lambda item: len(item[0]), reverse=True)
    return patterns


=======


def _find_category(canonical: str) -> str:
    for category, skills in SKILLS_BY_CATEGORY.items():
        if canonical in skills or canonical.lower() in [s.lower() for s in skills]:
            return category
    return "other"


def _build_skill_patterns() -> list[tuple[str, str, str]]:
    """
    Build searchable patterns: (pattern_text, canonical_name, category).
    Longer patterns are checked first to avoid partial matches (e.g. Java vs JavaScript).
    """
    patterns: list[tuple[str, str, str]] = []
    seen: set[str] = set()

    for category, skills in SKILLS_BY_CATEGORY.items():
        for skill in skills:
            canonical = normalize_skill(skill)
            key = canonical.lower()
            if key not in seen:
                patterns.append((skill.lower(), canonical, category))
                seen.add(key)

    for alias, canonical in SKILL_ALIASES.items():
        key = canonical.lower()
        category = _find_category(canonical)
        patterns.append((alias.lower(), canonical, category))
        seen.add(key)

    patterns.sort(key=lambda item: len(item[0]), reverse=True)
    return patterns


>>>>>>> 17f2cf1 (Your commit message here)
# Build searchable patterns after defining helper functions
SKILL_PATTERNS = _build_skill_patterns()


def normalize_text(text: str) -> str:
    """Lowercase text and collapse whitespace for consistent matching."""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _word_boundary_pattern(term: str) -> re.Pattern[str]:
    """
    Build a regex that matches whole terms.
    Prevents 'Java' from matching inside 'JavaScript'.
    """
    escaped = re.escape(term)
    if term.replace(".", "").replace("+", "").replace("#", "").isalnum():
        return re.compile(rf"(?<![a-z0-9#+.]){escaped}(?![a-z0-9#+.])", re.IGNORECASE)
    return re.compile(rf"\b{escaped}\b", re.IGNORECASE)


def extract_skills(text: str) -> ExtractedSkills:
    """
    Extract categorized skills from text using the skills dictionary.

    Returns structured skills data with normalized canonical names.
    """
    if not text or not text.strip():
        return ExtractedSkills()

    normalized = normalize_text(text)
    found: dict[str, tuple[str, str]] = {}  # canonical_lower -> (canonical, category)

    for pattern_text, canonical, category in SKILL_PATTERNS:
        regex = _word_boundary_pattern(pattern_text)
        if regex.search(normalized):
            key = canonical.lower()
            if key not in found:
                found[key] = (canonical, category)

    result = ExtractedSkills()
    for canonical, category in found.values():
        target_list = getattr(result, category, result.other)
        target_list.append(canonical)

    for category in result.to_dict():
        getattr(result, category).sort()

    return result


def count_skill_mentions(text: str, skill: str) -> int:
    """Count how often a skill appears in text (used for gap priority)."""
    normalized = normalize_text(text)
    aliases = [skill.lower()]
    for alias, canonical in SKILL_ALIASES.items():
        if canonical.lower() == skill.lower():
            aliases.append(alias)

    count = 0
    for alias in set(aliases):
        regex = _word_boundary_pattern(alias)
        count += len(regex.findall(normalized))
    return count