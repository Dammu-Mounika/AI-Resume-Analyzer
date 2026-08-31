"""
Unit tests for the AI Resume Analyzer.
"""

import io

import pymupdf
import pytest
from fastapi.testclient import TestClient

from backend.keyword_extractor import extract_skills, normalize_skill
from backend.main import app
from backend.matcher import compare_skills
from backend.resume_parser import (
    EmptyPDFError,
    InvalidPDFError,
    clean_text,
    extract_text_from_pdf,
    parse_resume_upload,
)
from backend.scorer import calculate_overall_score, calculate_semantic_similarity
from backend.suggestions import analyze_skill_gap, generate_suggestions

client = TestClient(app)


def _make_pdf_with_text(pages_text: list[str]) -> bytes:
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def _make_empty_pdf() -> bytes:
    doc = pymupdf.open()
    doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


JOB_DESC = (
    "Python Backend Developer with experience in Python, FastAPI, "
    "SQL, REST APIs, Git, Docker and AWS."
)

RESUME_WITH_MATCHES = (
    "John Doe - Software Developer\n"
    "Skills: Python, FastAPI, SQL, Git, MySQL, Docker\n"
    "Experience building REST APIs with FastAPI and Python."
)


class TestCleanText:
    def test_collapses_whitespace(self):
        assert clean_text("Python   Developer\n\n\nFastAPI") == "Python Developer\nFastAPI"

    def test_empty_string(self):
        assert clean_text("") == ""


class TestPDFExtraction:
    def test_single_page_extraction(self):
        pdf = _make_pdf_with_text(["Python Developer with FastAPI experience"])
        result = extract_text_from_pdf(pdf)
        assert "Python" in result.text
        assert result.page_count == 1

    def test_multi_page_extraction(self):
        pdf = _make_pdf_with_text(["Page one: Python", "Page two: Docker and AWS"])
        result = extract_text_from_pdf(pdf)
        assert result.page_count == 2
        assert "Docker" in result.text

    def test_invalid_pdf_raises(self):
        with pytest.raises(InvalidPDFError):
            extract_text_from_pdf(b"not a pdf file")

    def test_empty_pdf_raises(self):
        with pytest.raises(EmptyPDFError):
            extract_text_from_pdf(_make_empty_pdf())


class TestSkillExtraction:
    def test_extracts_job_skills(self):
        skills = extract_skills(JOB_DESC)
        flat = skills.all_skills()
        assert "Python" in flat
        assert "FastAPI" in flat
        assert "Docker" in flat
        assert "AWS" in flat

    def test_java_does_not_match_javascript(self):
        skills = extract_skills("Expert in JavaScript and React")
        flat = [s.lower() for s in skills.all_skills()]
        assert "javascript" in flat
        assert "java" not in flat

    def test_normalization(self):
        assert normalize_skill("restful api") == "REST API"
        assert normalize_skill("postgres") == "PostgreSQL"
        assert normalize_skill("ml") == "Machine Learning"


class TestMatching:
    def test_matched_and_missing(self):
        resume_skills = extract_skills(RESUME_WITH_MATCHES)
        job_skills = extract_skills(JOB_DESC)
        result = compare_skills(resume_skills, job_skills)

        assert "Python" in result.matched_skills
        assert "FastAPI" in result.matched_skills
        assert "Git" in result.matched_skills
        assert "AWS" in result.missing_skills
        assert result.keyword_match_percentage > 0

    def test_no_job_skills(self):
        resume_skills = extract_skills(RESUME_WITH_MATCHES)
        job_skills = extract_skills("General office administrator role.")
        result = compare_skills(resume_skills, job_skills)
        assert result.keyword_match_percentage == 0.0


class TestScoring:
    def test_semantic_similarity(self):
        score = calculate_semantic_similarity(RESUME_WITH_MATCHES, JOB_DESC)
        assert 0 <= score <= 100

    def test_overall_score_formula(self):
        result = calculate_overall_score(80, 65)
        assert result.overall_score == 75.5
        assert result.keyword_score == 80
        assert result.semantic_score == 65


class TestSuggestions:
    def test_skill_gap_priority(self):
        gap = analyze_skill_gap(JOB_DESC, ["AWS", "Docker", "REST API"])
        assert "AWS" in gap["high_priority"] or "AWS" in gap["medium_priority"]

    def test_suggestions_are_ethical(self):
        suggestions = generate_suggestions(["Docker", "AWS"], 40, {"high_priority": ["AWS"], "medium_priority": ["Docker"], "low_priority": []})
        assert any("genuinely" in s.lower() or "if you" in s.lower() for s in suggestions)
        assert not any("add fake" in s.lower() for s in suggestions)


class TestAnalyzeEndpoint:
    def test_missing_job_description(self):
        pdf = _make_pdf_with_text(["Python skills"])
        response = client.post(
            "/analyze",
            files={"resume": ("resume.pdf", io.BytesIO(pdf), "application/pdf")},
            data={"job_description": ""},
        )
        assert response.status_code == 400

    def test_short_job_description(self):
        pdf = _make_pdf_with_text(["Python skills"])
        response = client.post(
            "/analyze",
            files={"resume": ("resume.pdf", io.BytesIO(pdf), "application/pdf")},
            data={"job_description": "Too short"},
        )
        assert response.status_code == 400

    def test_invalid_pdf_upload(self):
        response = client.post(
            "/analyze",
            files={"resume": ("resume.pdf", io.BytesIO(b"fake"), "application/pdf")},
            data={"job_description": JOB_DESC},
        )
        assert response.status_code == 400

    def test_full_analysis_response(self):
        pdf = _make_pdf_with_text([RESUME_WITH_MATCHES])
        response = client.post(
            "/analyze",
            files={"resume": ("resume.pdf", io.BytesIO(pdf), "application/pdf")},
            data={"job_description": JOB_DESC},
        )
        assert response.status_code == 200
        data = response.json()

        assert "overall_score" in data
        assert "keyword_score" in data
        assert "semantic_score" in data
        assert "matched_skills" in data
        assert "missing_skills" in data
        assert "suggestions" in data
        assert "Python" in data["matched_skills"]
        assert data["overall_score"] >= 0
