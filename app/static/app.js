const form = document.getElementById("tailor-form");
const jobUrlInput = document.getElementById("job-url");
const jobTextInput = document.getElementById("job-text");
const cvFileInput = document.getElementById("cv-file");
const dropZone = document.getElementById("drop-zone");
const dropLabel = document.getElementById("drop-label");
const fileInfo = document.getElementById("file-info");
const fileName = document.getElementById("file-name");
const fileSize = document.getElementById("file-size");
const clearFileBtn = document.getElementById("clear-file");
const submitBtn = document.getElementById("submit-btn");
const progressEl = document.getElementById("progress");
const progressText = document.getElementById("progress-text");
const errorEl = document.getElementById("error");
const errorText = document.getElementById("error-text");
const resultsEl = document.getElementById("results");

// File upload
dropZone.addEventListener("click", () => cvFileInput.click());
dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
});
dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
});
dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    if (e.dataTransfer.files.length) {
        cvFileInput.files = e.dataTransfer.files;
        showFileInfo(e.dataTransfer.files[0]);
    }
});
cvFileInput.addEventListener("change", () => {
    if (cvFileInput.files.length) {
        showFileInfo(cvFileInput.files[0]);
    }
});
clearFileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    cvFileInput.value = "";
    dropLabel.classList.remove("hidden");
    fileInfo.classList.add("hidden");
});

function showFileInfo(file) {
    fileName.textContent = file.name;
    fileSize.textContent = formatBytes(file.size);
    dropLabel.classList.add("hidden");
    fileInfo.classList.remove("hidden");
}

function formatBytes(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1048576).toFixed(1) + " MB";
}

// Form submission
form.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideError();
    hideResults();

    const jobUrl = jobUrlInput.value.trim();
    const jobText = jobTextInput.value.trim();
    const file = cvFileInput.files[0];

    if (!jobUrl && !jobText) {
        showError("Please provide a job URL or paste the job description.");
        return;
    }
    if (!file) {
        showError("Please upload your CV (DOCX or PDF).");
        return;
    }

    const formData = new FormData();
    formData.append("cv_file", file);
    if (jobUrl) formData.append("job_url", jobUrl);
    if (jobText) formData.append("job_text", jobText);

    showProgress("Analyzing job description and tailoring your CV...");
    submitBtn.disabled = true;

    try {
        const response = await fetch("/api/tailor", {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Something went wrong.");
        }

        const data = await response.json();
        showResults(data);
    } catch (err) {
        showError(err.message);
    } finally {
        hideProgress();
        submitBtn.disabled = false;
    }
});

function showProgress(msg) {
    progressText.textContent = msg;
    progressEl.classList.remove("hidden");
}

function hideProgress() {
    progressEl.classList.add("hidden");
}

function showError(msg) {
    errorText.textContent = msg;
    errorEl.classList.remove("hidden");
}

function hideError() {
    errorEl.classList.add("hidden");
}

function hideResults() {
    resultsEl.classList.add("hidden");
}

let lastPrepSummary = "";

function showResults(data) {
    // Job info
    document.getElementById("result-title").textContent = data.job_title || "Unknown Role";
    document.getElementById("result-company").textContent = data.company ? `at ${data.company}` : "";

    // Download link
    const downloadLink = document.getElementById("download-link");
    downloadLink.href = `/api/download/${data.tailored_cv_filename}`;

    // Keywords
    const matchedContainer = document.getElementById("keywords-matched");
    const missingContainer = document.getElementById("keywords-missing");
    matchedContainer.innerHTML = "";
    missingContainer.innerHTML = "";

    (data.keywords_matched || []).forEach((kw) => {
        matchedContainer.innerHTML += `<span class="keyword-badge matched">${kw}</span>`;
    });
    (data.keywords_missing || []).forEach((kw) => {
        missingContainer.innerHTML += `<span class="keyword-badge missing">${kw}</span>`;
    });

    if (!data.keywords_matched?.length) {
        matchedContainer.innerHTML = '<span class="text-gray-500 text-sm">None detected</span>';
    }
    if (!data.keywords_missing?.length) {
        missingContainer.innerHTML = '<span class="text-gray-500 text-sm">All keywords covered</span>';
    }

    // Prep summary
    lastPrepSummary = data.prep_summary || "";
    const prepContent = document.getElementById("prep-content");
    prepContent.innerHTML = marked.parse(lastPrepSummary);

    resultsEl.classList.remove("hidden");
    resultsEl.scrollIntoView({ behavior: "smooth" });
}

// Download prep as markdown
document.getElementById("download-prep").addEventListener("click", () => {
    if (!lastPrepSummary) return;
    const blob = new Blob([lastPrepSummary], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "interview-prep.md";
    a.click();
    URL.revokeObjectURL(url);
});

// Reset
document.getElementById("reset-btn").addEventListener("click", () => {
    form.reset();
    dropLabel.classList.remove("hidden");
    fileInfo.classList.add("hidden");
    hideResults();
    hideError();
    window.scrollTo({ top: 0, behavior: "smooth" });
});
