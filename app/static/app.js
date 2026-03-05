const form = document.getElementById("tailor-form");
const formatCards = document.querySelectorAll(".format-card");
const cvFormatInput = document.getElementById("cv-format");

// Format picker
formatCards.forEach((card) => {
    card.addEventListener("click", () => {
        formatCards.forEach((c) => c.classList.remove("selected"));
        card.classList.add("selected");
        cvFormatInput.value = card.dataset.format;
    });
});

const jobUrlInput   = document.getElementById("job-url");
const jobTextInput  = document.getElementById("job-text");
const cvFileInput   = document.getElementById("cv-file");
const dropZone      = document.getElementById("drop-zone");
const dropLabel     = document.getElementById("drop-label");
const fileInfo      = document.getElementById("file-info");
const fileName      = document.getElementById("file-name");
const fileSize      = document.getElementById("file-size");
const clearFileBtn  = document.getElementById("clear-file");
const submitBtn     = document.getElementById("submit-btn");
const progressEl    = document.getElementById("progress");
const progressText  = document.getElementById("progress-text");
const errorEl       = document.getElementById("error");
const errorText     = document.getElementById("error-text");
const resultsEl     = document.getElementById("results");

// File upload
dropZone.addEventListener("click", () => cvFileInput.click());
dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("drag-over"); });
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    if (e.dataTransfer.files.length) { cvFileInput.files = e.dataTransfer.files; showFileInfo(e.dataTransfer.files[0]); }
});
cvFileInput.addEventListener("change", () => { if (cvFileInput.files.length) showFileInfo(cvFileInput.files[0]); });
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

    const jobUrl  = jobUrlInput.value.trim();
    const jobText = jobTextInput.value.trim();
    const file    = cvFileInput.files[0];

    if (!jobUrl && !jobText) { showError("Please provide a job URL or paste the job description."); return; }
    if (!file)               { showError("Please upload your CV (DOCX or PDF)."); return; }

    const formData = new FormData();
    formData.append("cv_file", file);
    if (jobUrl)  formData.append("job_url",  jobUrl);
    if (jobText) formData.append("job_text", jobText);
    formData.append("cv_format", cvFormatInput.value || "classic");

    showProgress("Analysing job description, tailoring your CV and writing cover letter…");
    submitBtn.disabled = true;

    try {
        const response = await fetch("/api/tailor", { method: "POST", body: formData });

        if (!response.ok) {
            let msg = "Something went wrong.";
            try { const err = await response.json(); msg = err.detail || msg; }
            catch { const t = await response.text(); msg = t.slice(0, 200) || msg; }
            throw new Error(msg);
        }

        const text = await response.text();
        let data;
        try { data = JSON.parse(text); }
        catch { throw new Error("Server returned invalid response: " + text.slice(0, 200)); }
        showResults(data);
    } catch (err) {
        showError(err.message);
    } finally {
        hideProgress();
        submitBtn.disabled = false;
    }
});

function showProgress(msg) { progressText.textContent = msg; progressEl.classList.remove("hidden"); }
function hideProgress()    { progressEl.classList.add("hidden"); }
function showError(msg)    { errorText.textContent = msg; errorEl.classList.remove("hidden"); }
function hideError()       { errorEl.classList.add("hidden"); }
function hideResults()     { resultsEl.classList.add("hidden"); }

let lastPrepSummary = "";
let lastCoverLetter = "";

function showResults(data) {
    // Job info
    document.getElementById("result-title").textContent   = data.job_title || "Unknown Role";
    document.getElementById("result-company").textContent = data.company ? `at ${data.company}` : "";

    // ATS score ring
    const score    = data.ats_score ?? 0;
    const circumference = 2 * Math.PI * 32; // r=32
    const fill     = document.getElementById("ats-ring-fill");
    const numEl    = document.getElementById("ats-score-number");

    fill.style.strokeDasharray  = circumference;
    fill.style.strokeDashoffset = circumference;            // start empty

    // Colour based on score
    const color = score >= 75 ? "#22c55e" : score >= 50 ? "#f59e0b" : "#ef4444";
    fill.style.stroke = color;
    numEl.style.color = color;

    // Animate counter + ring
    let current = 0;
    const step = Math.ceil(score / 40);
    const timer = setInterval(() => {
        current = Math.min(current + step, score);
        numEl.textContent = current;
        fill.style.strokeDashoffset = circumference - (current / 100) * circumference;
        if (current >= score) clearInterval(timer);
    }, 30);

    // Format label
    const formatLabels = { classic: "Classic", modern: "Modern", executive: "Executive", minimal: "Minimal" };
    const resultFormat = document.getElementById("result-format");
    if (resultFormat) resultFormat.textContent = formatLabels[data.cv_format] || "Classic";

    // Download links
    document.getElementById("download-link").href     = `/api/download/${data.tailored_cv_filename}`;
    document.getElementById("download-pdf-link").href = `/api/download/${data.pdf_filename}`;

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
    if (!data.keywords_matched?.length)
        matchedContainer.innerHTML = '<span class="text-gray-500 text-sm">None detected</span>';
    if (!data.keywords_missing?.length)
        missingContainer.innerHTML = '<span class="text-gray-500 text-sm">All keywords covered ✓</span>';

    // Cover letter
    lastCoverLetter = data.cover_letter || "";
    document.getElementById("cover-letter-text").value = lastCoverLetter;

    // Prep summary
    lastPrepSummary = data.prep_summary || "";
    document.getElementById("prep-content").innerHTML = marked.parse(lastPrepSummary);

    resultsEl.classList.remove("hidden");
    resultsEl.scrollIntoView({ behavior: "smooth" });
}

// ── Cover letter actions ──────────────────────────────────────────────────
document.getElementById("copy-cover").addEventListener("click", async () => {
    if (!lastCoverLetter) return;
    await navigator.clipboard.writeText(lastCoverLetter);
    const btn = document.getElementById("copy-cover");
    btn.textContent = "Copied!";
    setTimeout(() => { btn.innerHTML = `<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg> Copy`; }, 2000);
});

document.getElementById("download-cover").addEventListener("click", () => {
    const text = document.getElementById("cover-letter-text").value;
    if (!text) return;
    const blob = new Blob([text], { type: "text/plain" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href = url; a.download = "cover-letter.txt"; a.click();
    URL.revokeObjectURL(url);
});

// ── Interview prep download ───────────────────────────────────────────────
document.getElementById("download-prep").addEventListener("click", () => {
    if (!lastPrepSummary) return;
    const blob = new Blob([lastPrepSummary], { type: "text/markdown" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href = url; a.download = "interview-prep.md"; a.click();
    URL.revokeObjectURL(url);
});

// ── Reset ─────────────────────────────────────────────────────────────────
document.getElementById("reset-btn").addEventListener("click", () => {
    form.reset();
    dropLabel.classList.remove("hidden");
    fileInfo.classList.add("hidden");
    hideResults();
    hideError();
    window.scrollTo({ top: 0, behavior: "smooth" });
});
