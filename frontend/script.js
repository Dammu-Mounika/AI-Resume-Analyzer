/**
 * AI Resume Analyzer — form handling, API integration, and results dashboard.
 */

const CONFIG = {
    API_ANALYZE_URL: "/analyze",
    MIN_JOB_DESCRIPTION_LENGTH: 20,
    MAX_FILE_SIZE_BYTES: 5 * 1024 * 1024,
    ALLOWED_EXTENSION: ".pdf",
};

const SAMPLE_JOB_DESCRIPTION = `Python Backend Developer

We are looking for a Python Developer with experience in Python, FastAPI, SQL, REST APIs, Git, Docker and AWS.

Responsibilities:
- Build and maintain backend services using FastAPI
- Design and query relational databases (SQL)
- Develop RESTful APIs and integrate with front-end systems
- Use Git for version control and collaborate via GitHub
- Deploy services using Docker and cloud platforms (AWS preferred)

Requirements:
- Strong Python fundamentals
- Experience with web frameworks and API development
- Familiarity with CI/CD and containerization is a plus`;

// DOM elements
const form = document.getElementById("analyze-form");
const resumeInput = document.getElementById("resume-input");
const uploadArea = document.getElementById("upload-area");
const uploadPlaceholder = document.getElementById("upload-placeholder");
const uploadSelected = document.getElementById("upload-selected");
const browseBtn = document.getElementById("browse-btn");
const removeFileBtn = document.getElementById("remove-file-btn");
const fileNameEl = document.getElementById("file-name");
const fileSizeEl = document.getElementById("file-size");
const resumeError = document.getElementById("resume-error");

const jobDescription = document.getElementById("job-description");
const charCount = document.getElementById("char-count");
const jobError = document.getElementById("job-error");
const sampleJobBtn = document.getElementById("sample-job-btn");

const analyzeBtn = document.getElementById("analyze-btn");
const btnSpinner = document.getElementById("btn-spinner");
const globalError = document.getElementById("global-error");
const resultsDashboard = document.getElementById("results-dashboard");

let selectedFile = null;
let skillsChart = null;
let scoreChart = null;

// --- File upload handlers ---

browseBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    resumeInput.click();
});

uploadArea.addEventListener("click", () => {
    if (!selectedFile) resumeInput.click();
});

resumeInput.addEventListener("change", () => {
    if (resumeInput.files.length > 0) handleFileSelect(resumeInput.files[0]);
});

removeFileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    clearFileSelection();
});

uploadArea.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadArea.classList.add("drag-over");
});

uploadArea.addEventListener("dragleave", () => uploadArea.classList.remove("drag-over"));

uploadArea.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadArea.classList.remove("drag-over");
    if (e.dataTransfer.files.length > 0) handleFileSelect(e.dataTransfer.files[0]);
});

function handleFileSelect(file) {
    hideElement(resumeError);
    const validationError = validateResumeFile(file);
    if (validationError) {
        showError(resumeError, validationError);
        clearFileSelection();
        return;
    }
    selectedFile = file;
    fileNameEl.textContent = file.name;
    fileSizeEl.textContent = formatFileSize(file.size);
    hideElement(uploadPlaceholder);
    showElement(uploadSelected);
}

function clearFileSelection() {
    selectedFile = null;
    resumeInput.value = "";
    hideElement(uploadSelected);
    showElement(uploadPlaceholder);
}

function validateResumeFile(file) {
    if (!file.name.toLowerCase().endsWith(CONFIG.ALLOWED_EXTENSION)) return "Only PDF files are accepted.";
    if (file.size > CONFIG.MAX_FILE_SIZE_BYTES) return "File exceeds the maximum allowed size of 5 MB.";
    if (file.size === 0) return "The selected file is empty.";
    return null;
}

function formatFileSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

// --- Job description ---

jobDescription.addEventListener("input", updateCharCount);

sampleJobBtn.addEventListener("click", () => {
    jobDescription.value = SAMPLE_JOB_DESCRIPTION;
    updateCharCount();
    jobDescription.focus();
});

function updateCharCount() {
    const length = jobDescription.value.trim().length;
    charCount.textContent = `${length} character${length !== 1 ? "s" : ""}`;
    charCount.classList.toggle("valid", length >= CONFIG.MIN_JOB_DESCRIPTION_LENGTH);
    charCount.classList.toggle("invalid", length > 0 && length < CONFIG.MIN_JOB_DESCRIPTION_LENGTH);
}

function validateJobDescription() {
    const text = jobDescription.value.trim();
    if (!text) return "Job description is required.";
    if (text.length < CONFIG.MIN_JOB_DESCRIPTION_LENGTH) {
        return `Job description is too short. Please provide at least ${CONFIG.MIN_JOB_DESCRIPTION_LENGTH} characters.`;
    }
    return null;
}

// --- Form submission ---

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideElement(globalError);
    hideElement(resultsDashboard);
    hideElement(resumeError);
    hideElement(jobError);

    let hasError = false;
    if (!selectedFile) {
        showError(resumeError, "Please upload your resume PDF.");
        hasError = true;
    }
    const jobValidationError = validateJobDescription();
    if (jobValidationError) {
        showError(jobError, jobValidationError);
        jobDescription.classList.add("input-error");
        hasError = true;
    } else {
        jobDescription.classList.remove("input-error");
    }
    if (hasError) return;

    await submitAnalysis();
});

async function submitAnalysis() {
    setLoading(true);
    const formData = new FormData();
    formData.append("resume", selectedFile);
    formData.append("job_description", jobDescription.value.trim());

    try {
        const response = await fetch(CONFIG.API_ANALYZE_URL, { method: "POST", body: formData });
        const data = await response.json();

        if (!response.ok) {
            const message = data.detail || "Analysis failed. Please try again.";
            showGlobalError(typeof message === "string" ? message : JSON.stringify(message));
            return;
        }

        showResults(data);
    } catch {
        showGlobalError("Could not connect to the server. Make sure the backend is running at http://127.0.0.1:8000");
    } finally {
        setLoading(false);
    }
}

// --- Results dashboard ---

function showResults(data) {
    // Scores
    document.getElementById("overall-score").textContent = `${Math.round(data.overall_score)}%`;
    document.getElementById("keyword-score").textContent = `${data.keyword_score}%`;
    document.getElementById("semantic-score").textContent = `${data.semantic_score}%`;
    document.getElementById("keyword-bar").style.width = `${data.keyword_score}%`;
    document.getElementById("semantic-bar").style.width = `${data.semantic_score}%`;

    const circle = document.getElementById("overall-score-circle");
    circle.className = "score-circle";
    if (data.overall_score >= 70) circle.classList.add("score-good");
    else if (data.overall_score >= 40) circle.classList.add("score-medium");
    else circle.classList.add("score-low");

    // Skills lists
    renderSkillList("matched-skills", data.matched_skills, "matched");
    renderSkillList("missing-skills", data.missing_skills, "missing");
    toggleEmpty("no-matched", data.matched_skills.length === 0);
    toggleEmpty("no-missing", data.missing_skills.length === 0);

    // Skill gap
    renderSkillList("gap-high", data.skill_gap.high_priority, "gap");
    renderSkillList("gap-medium", data.skill_gap.medium_priority, "gap");
    renderSkillList("gap-low", data.skill_gap.low_priority, "gap");

    // Suggestions
    const suggestionsEl = document.getElementById("suggestions");
    suggestionsEl.innerHTML = "";
    data.suggestions.forEach((s) => {
        const li = document.createElement("li");
        li.textContent = s;
        suggestionsEl.appendChild(li);
    });

    // Charts
    renderCharts(data);

    showElement(resultsDashboard);
    resultsDashboard.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderSkillList(elementId, skills, type) {
    const ul = document.getElementById(elementId);
    ul.innerHTML = "";
    skills.forEach((skill) => {
        const li = document.createElement("li");
        li.className = `skill-tag ${type}`;
        li.textContent = skill;
        ul.appendChild(li);
    });
}

function toggleEmpty(elementId, isEmpty) {
    const el = document.getElementById(elementId);
    if (isEmpty) showElement(el);
    else hideElement(el);
}

function renderCharts(data) {
    if (skillsChart) skillsChart.destroy();
    if (scoreChart) scoreChart.destroy();

    skillsChart = new Chart(document.getElementById("skills-chart"), {
        type: "doughnut",
        data: {
            labels: ["Matched", "Missing"],
            datasets: [{
                data: [data.matched_skills.length, data.missing_skills.length],
                backgroundColor: ["#059669", "#dc2626"],
            }],
        },
        options: { plugins: { legend: { position: "bottom" } } },
    });

    scoreChart = new Chart(document.getElementById("score-chart"), {
        type: "bar",
        data: {
            labels: ["Keyword Match", "Semantic Similarity", "Overall Score"],
            datasets: [{
                label: "Score (%)",
                data: [data.keyword_score, data.semantic_score, data.overall_score],
                backgroundColor: ["#2563eb", "#7c3aed", "#059669"],
            }],
        },
        options: {
            scales: { y: { beginAtZero: true, max: 100 } },
            plugins: { legend: { display: false } },
        },
    });
}

// --- UI helpers ---

function setLoading(isLoading) {
    analyzeBtn.disabled = isLoading;
    btnSpinner.classList.toggle("hidden", !isLoading);
    analyzeBtn.querySelector(".btn-label").textContent = isLoading ? "Analyzing..." : "Analyze Resume";
}

function showError(element, message) {
    element.textContent = message;
    showElement(element);
}

function showGlobalError(message) {
    globalError.textContent = message;
    showElement(globalError);
    globalError.scrollIntoView({ behavior: "smooth", block: "center" });
}

function showElement(el) { el.classList.remove("hidden"); }
function hideElement(el) { el.classList.add("hidden"); }

updateCharCount();
