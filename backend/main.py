"""
AI Resume Analyzer & Job Matcher - FastAPI Application Entry Point
"""

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.config import ALLOWED_ORIGINS, BASE_DIR, MAX_UPLOAD_SIZE_BYTES
from backend.database import save_analysis
from backend.keyword_extractor import extract_skills
from backend.matcher import compare_skills
from backend.resume_parser import (
    EmptyPDFError,
    FileTooLargeError,
    InvalidPDFError,
    ResumeParserError,
    parse_resume_upload,
)
from backend.scorer import calculate_overall_score, calculate_semantic_similarity
from backend.suggestions import analyze_skill_gap, generate_suggestions

FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="AI Resume Analyzer & Job Matcher",
    description="Analyze your resume against a job description and identify improvement opportunities.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or use ALLOWED_ORIGINS from config.py
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MIN_JOB_DESCRIPTION_LENGTH = 20


class SkillCategories(BaseModel):
    programming: list[str] = []
    frameworks: list[str] = []
    databases: list[str] = []
    cloud: list[str] = []
    tools: list[str] = []
    data_ml: list[str] = []
    other: list[str] = []


class SkillGap(BaseModel):
    high_priority: list[str] = []
    medium_priority: list[str] = []
    low_priority: list[str] = []


class AnalyzeResponse(BaseModel):
    overall_score: float = Field(..., description="Job Match Score (not an official ATS score)")
    keyword_score: float
    semantic_score: float
    resume_skills: list[str]
    job_skills: list[str]
    resume_skills_by_category: SkillCategories
    job_skills_by_category: SkillCategories
    matched_skills: list[str]
    missing_skills: list[str]
    skill_gap: SkillGap
    suggestions: list[str]
    page_count: int
    character_count: int


@app.get("/")
def root(request: Request):
    """Browser visits receive the web UI; API clients receive JSON health check."""
    accept = request.headers.get("accept", "")
    index_file = FRONTEND_DIR / "index.html"
    if "text/html" in accept and index_file.exists():
        return FileResponse(index_file)
    return {
        "message": "AI Resume Analyzer & Job Matcher API",
        "status": "running",
        "version": "1.0.0",
        "frontend": "/",
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_resume(
    resume: UploadFile = File(..., description="Resume PDF file"),
    job_description: str = Form(default="", description="Job description text"),
):
    """Analyze a resume PDF against a job description."""
    if not job_description or not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description is required.")

    if len(job_description.strip()) < MIN_JOB_DESCRIPTION_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Job description is too short. Please provide at least {MIN_JOB_DESCRIPTION_LENGTH} characters.",
        )

    if not resume.filename:
        raise HTTPException(status_code=400, detail="Resume file is required.")

    file_bytes = await resume.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded resume file is empty.")

    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="File exceeds the maximum allowed size of 5 MB.",
        )

    try:
        parsed = parse_resume_upload(
            filename=resume.filename,
            content_type=resume.content_type,
            file_bytes=file_bytes,
        )
    except FileTooLargeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except InvalidPDFError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except EmptyPDFError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ResumeParserError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the resume.",
        )

    job_text = job_description.strip()
    resume_text = parsed.text

    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_text)
    match = compare_skills(resume_skills, job_skills)
    semantic_score = calculate_semantic_similarity(resume_text, job_text)
    scores = calculate_overall_score(match.keyword_match_percentage, semantic_score)
    skill_gap = analyze_skill_gap(job_text, match.missing_skills)
    suggestions = generate_suggestions(
        match.missing_skills,
        scores.keyword_score,
        skill_gap,
    )

    # Optional: Log analysis execution to SQLite database
    try:
        save_analysis(
            filename=resume.filename,
            job_title=None,
            overall_score=scores.overall_score,
            keyword_score=scores.keyword_score,
            semantic_score=scores.semantic_score,
            matched_skills=match.matched_skills,
            missing_skills=match.missing_skills,
        )
    except Exception:
        pass  # Non-blocking if database write fails

    return AnalyzeResponse(
        overall_score=scores.overall_score,
        keyword_score=scores.keyword_score,
        semantic_score=scores.semantic_score,
        resume_skills=match.resume_skills_flat,
        job_skills=match.job_skills_flat,
        resume_skills_by_category=SkillCategories(**resume_skills.to_dict()),
        job_skills_by_category=SkillCategories(**job_skills.to_dict()),
        matched_skills=match.matched_skills,
        missing_skills=match.missing_skills,
        skill_gap=SkillGap(**skill_gap),
        suggestions=suggestions,
        page_count=parsed.page_count,
        character_count=parsed.character_count,
    )


if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR)), name="assets")
