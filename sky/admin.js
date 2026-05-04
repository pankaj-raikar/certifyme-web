// ===== API HELPER =====
// Dynamically detect API base URL based on environment
// In production (same origin), use empty string (relative URLs)
// In development, use explicit backend URL
const API_BASE =
  window.location.hostname === "127.0.0.1" && window.location.port === "5500"
    ? "http://127.0.0.1:5000" // Development: frontend on 5500, backend on 5000
    : ""; // Production: same origin (empty string = relative URLs)

async function api(path, options = {}) {
  /**
   * Helper for all API calls.
   * - credentials: 'include' = send session cookies with request
   * - Content-Type: application/json = tell backend we're sending JSON
   *
   * Usage:
   *   const res = await api('/api/auth/signup', {
   *       method: 'POST',
   *       body: JSON.stringify({ email, password })
   *   });
   */
  const res = await fetch(API_BASE + path, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  return res;
}

async function apiJson(path, options = {}) {
  /**
   * Convenience wrapper — calls api() and parses JSON response.
   * Returns { data, status } tuple.
   */
  const res = await api(path, options);
  const data = await res.json();
  return { data, status: res.status };
}

// Global state
let fullName = ""; // Store logged-in user's name
let opportunities = []; // Store opportunities in memory
let editingOppId = null; // Track if editing existing opportunity

const captchas = { login: "", signup: "", forgot: "" };
function generateCaptcha(type) {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789";
  let code = "";
  for (let i = 0; i < 5; i++)
    code += chars.charAt(Math.floor(Math.random() * chars.length));
  captchas[type] = code;
  document.getElementById(type + "CaptchaText").textContent = code;
}
generateCaptcha("login");
generateCaptcha("signup");
generateCaptcha("forgot");

// ===== PAGE NAVIGATION =====
function showPage(pageId) {
  document
    .querySelectorAll(".form-page")
    .forEach((p) => p.classList.remove("active"));
  setTimeout(() => document.getElementById(pageId).classList.add("active"), 50);
  document
    .querySelectorAll(".error-msg")
    .forEach((e) => e.classList.remove("show"));
  document
    .querySelectorAll("input")
    .forEach((i) => i.classList.remove("error"));
}

function togglePass(inputId, btn) {
  const input = document.getElementById(inputId);
  const isPass = input.type === "password";
  input.type = isPass ? "text" : "password";
  btn.innerHTML = isPass
    ? '<svg viewBox="0 0 24 24"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>'
    : '<svg viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
}

// ===== HELPERS =====
function showError(id, msg) {
  const el = document.getElementById(id);
  if (msg) el.querySelector("span").textContent = msg;
  el.classList.add("show");
}
function clearAllErrors(formId) {
  document
    .querySelectorAll("#" + formId + " .error-msg")
    .forEach((e) => e.classList.remove("show"));
  document
    .querySelectorAll("#" + formId + " input")
    .forEach((i) => i.classList.remove("error"));
}
function shakeForm(formId) {
  const form = document.getElementById(formId);
  form.classList.add("shake");
  setTimeout(() => form.classList.remove("shake"), 400);
}
function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}
function showToast(msg) {
  document.getElementById("toastMsg").textContent = msg;
  document.getElementById("toast").classList.add("show");
  setTimeout(
    () => document.getElementById("toast").classList.remove("show"),
    3000,
  );
}

function checkStrength(val) {
  let score = 0;
  if (val.length >= 8) score++;
  if (/[A-Z]/.test(val)) score++;
  if (/[0-9]/.test(val)) score++;
  if (/[^A-Za-z0-9]/.test(val)) score++;
  const labels = ["", "Weak", "Medium", "Strong", "Very Strong"];
  const classes = ["", "weak", "medium", "strong", "very-strong"];
  for (let i = 1; i <= 4; i++) {
    const bar = document.getElementById("str" + i);
    bar.className = "strength-bar";
    if (i <= score) bar.classList.add(classes[score]);
  }
  document.getElementById("strengthLabel").textContent =
    val.length > 0 ? labels[score] : "";
}

// ===== SHOW DASHBOARD =====
function showDashboard(userFullName) {
  // Store full name in global
  fullName = userFullName || "Admin";

  document.getElementById("authWrapper").style.display = "none";
  document.getElementById("dashboardWrapper").classList.add("active");
  document.body.style.alignItems = "stretch";

  // Personalize
  document.getElementById("dashName").textContent = fullName;
  document.getElementById("dashAvatar").textContent = fullName
    .substring(0, 2)
    .toUpperCase();

  // Load opportunities after showing dashboard
  loadOpportunities();

  // Show menu toggle on mobile
  if (window.innerWidth <= 768) {
    document.getElementById("menuToggle").style.display = "flex";
  }
}

async function initializePageOnLoad() {
  /**
   * Check if user already has an active session on page load.
   * This ensures dashboard is shown on page refresh without re-login.
   */
  try {
    const { data, status } = await apiJson("/api/auth/me", {
      method: "GET",
    });

    if (status === 200) {
      // User already logged in — show dashboard
      console.log("Session active. Showing dashboard for:", data.full_name);
      showDashboard(data.full_name);
    } else if (status === 401) {
      // No active session — show login form (already displayed by default)
      console.log("No active session. Showing login form.");
    }
  } catch (err) {
    console.error("Session check error:", err);
    // On error, default to login form (safe fallback)
  }
}

async function handleLogout() {
  try {
    await api("/api/auth/logout", { method: "POST" });
  } catch (err) {
    console.error("Logout error:", err);
  }

  // Clear global state
  fullName = "";
  opportunities = [];
  editingOppId = null;

  document.getElementById("dashboardWrapper").classList.remove("active");
  document.getElementById("authWrapper").style.display = "flex";
  document.body.style.alignItems = "";
  showToast("Signed out successfully");
  showPage("loginPage");
}

// ===== NAV ITEMS =====
document.querySelectorAll(".nav-item[data-page]").forEach((item) => {
  item.addEventListener("click", function () {
    const page = this.getAttribute("data-page");
    document
      .querySelectorAll(".nav-item")
      .forEach((i) => i.classList.remove("active"));
    this.classList.add("active");

    // Hide all sections
    document
      .querySelectorAll(".dash-section")
      .forEach((s) => s.classList.remove("active"));

    // Show selected section
    if (page === "dashboard") {
      document.getElementById("dashboardSection").classList.add("active");
      document.getElementById("pageTitle").textContent = "Dashboard";
    } else if (page === "learner") {
      document.getElementById("learnerSection").classList.add("active");
      document.getElementById("pageTitle").textContent = "Learner Management";
    } else if (page === "verifier") {
      document.getElementById("verifierSection").classList.add("active");
      document.getElementById("pageTitle").textContent = "Verifier Management";
    } else if (page === "collaborator") {
      document.getElementById("collaboratorSection").classList.add("active");
      document.getElementById("pageTitle").textContent =
        "Collaborator Management";
    } else if (page === "opportunity") {
      document.getElementById("opportunitySection").classList.add("active");
      document.getElementById("pageTitle").textContent =
        "Opportunity Management";
    } else if (page === "reports") {
      document.getElementById("reportsSection").classList.add("active");
      document.getElementById("pageTitle").textContent =
        "Reports and Analytics";
    }
  });
});

// ===== TABS =====
function changeChartPeriod(period) {
  // Update active tab
  document.querySelectorAll(".tabs .tab-btn").forEach((btn) => {
    btn.classList.remove("active");
    if (btn.textContent.toLowerCase() === period) {
      btn.classList.add("active");
    }
  });

  // Chart data for different periods
  const chartData = {
    daily: "M0,120 Q50,110 100,90 T200,70 T300,50 T400,40",
    weekly: "M0,110 Q50,95 100,85 T200,65 T300,45 T400,35",
    monthly: "M0,100 Q50,85 100,75 T200,55 T300,40 T400,30",
    quarterly: "M0,90 Q50,75 100,65 T200,50 T300,35 T400,25",
    yearly: "M0,80 Q50,65 100,55 T200,40 T300,30 T400,20",
  };

  const linePath = document.getElementById("linePath");
  const lineArea = document.getElementById("lineArea");

  const path = chartData[period];
  linePath.setAttribute("d", path);
  lineArea.setAttribute("d", path + " L400,150 L0,150 Z");
}

// ===== NOTIFICATIONS =====
function toggleNotifications() {
  const dropdown = document.getElementById("notificationDropdown");
  dropdown.classList.toggle("active");
}

function markAllRead() {
  document.querySelectorAll(".notif-item.unread").forEach((item) => {
    item.classList.remove("unread");
  });
  showToast("All notifications marked as read");
}

// Close notification dropdown when clicking outside
document.addEventListener("click", function (e) {
  const dropdown = document.getElementById("notificationDropdown");
  const btn = document.getElementById("notifBtn");
  if (!dropdown.contains(e.target) && !btn.contains(e.target)) {
    dropdown.classList.remove("active");
  }
});

// ===== THEME TOGGLE =====
function toggleTheme() {
  const html = document.documentElement;
  const currentTheme = html.getAttribute("data-theme");
  const newTheme = currentTheme === "dark" ? "light" : "dark";
  html.setAttribute("data-theme", newTheme);

  // Update icon
  const icon = document.getElementById("themeIcon");
  if (newTheme === "dark") {
    icon.innerHTML =
      '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>';
  } else {
    icon.innerHTML =
      '<circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>';
  }
}

// ===== SEARCH =====
function openSearch() {
  document.getElementById("searchContainer").classList.add("active");
  document.getElementById("searchInput").focus();
}

function closeSearch() {
  document.getElementById("searchContainer").classList.remove("active");
}

// Close search on Escape key
document.addEventListener("keydown", function (e) {
  if (e.key === "Escape") {
    closeSearch();
    closeCourseModal();
    closeOpportunityModal();
    closeOpportunityDetailsModal();
    closeCollaboratorCoursesModal();
    closeQuickAddModal();
    closeBulkUploadModal();
    closeQuickAddVerifierModal();
    closeBulkUploadVerifierModal();
    closeVerifierDetailsModal();
  }
});

// Close search when clicking outside
document
  .getElementById("searchContainer")
  .addEventListener("click", function (e) {
    if (e.target === this) {
      closeSearch();
    }
  });

// ===== COURSE MODAL =====
function openCourseDetails(courseName, stats) {
  document.getElementById("modalCourseTitle").textContent = courseName;
  document.getElementById("modalEnrolled").textContent = stats.enrolled;
  document.getElementById("modalCompleted").textContent = stats.completed;
  document.getElementById("modalInProgress").textContent = stats.inProgress;
  document.getElementById("modalHalfDone").textContent = stats.halfDone;
  document.getElementById("courseModal").classList.add("active");
}

function closeCourseModal() {
  document.getElementById("courseModal").classList.remove("active");
}

// Close modal when clicking outside
document.getElementById("courseModal").addEventListener("click", function (e) {
  if (e.target === this) {
    closeCourseModal();
  }
});

// ===== OPPORTUNITY DETAILS MODAL =====
function openOpportunityDetails(title, details) {
  document.getElementById("opportunityDetailTitle").textContent = title;
  document.getElementById("opportunityDetailDuration").textContent =
    details.duration;
  document.getElementById("opportunityDetailStartDate").textContent =
    details.startDate;
  document.getElementById("opportunityDetailApplicants").textContent =
    details.applicants;
  document.getElementById("opportunityDetailDescription").textContent =
    details.description;
  document.getElementById("opportunityDetailFuture").textContent =
    details.futureOpportunities;
  document.getElementById("opportunityDetailPrereqs").textContent =
    details.prerequisites;

  const skillsContainer = document.getElementById("opportunityDetailSkills");
  skillsContainer.innerHTML = "";
  details.skills.forEach((skill) => {
    const tag = document.createElement("span");
    tag.className = "skill-tag";
    tag.textContent = skill;
    skillsContainer.appendChild(tag);
  });

  document.getElementById("opportunityDetailsModal").classList.add("active");
}

function closeOpportunityDetailsModal() {
  document.getElementById("opportunityDetailsModal").classList.remove("active");
}

function applyToOpportunity() {
  showToast("Application submitted successfully!");
  closeOpportunityDetailsModal();
}

document
  .getElementById("opportunityDetailsModal")
  .addEventListener("click", function (e) {
    if (e.target === this) {
      closeOpportunityDetailsModal();
    }
  });

// ===== COLLABORATOR COURSES MODAL =====
function openCollaboratorCourses(name, role) {
  document.getElementById("collaboratorName").textContent =
    name + "'s Submitted Courses";
  document.getElementById("collaboratorRole").textContent = "Role: " + role;
  document.getElementById("collaboratorCoursesModal").classList.add("active");
}

function closeCollaboratorCoursesModal() {
  document
    .getElementById("collaboratorCoursesModal")
    .classList.remove("active");
}

function approveCourse(courseName) {
  showToast(courseName + " has been approved!");
  // In a real app, you would update the course status here
}

function rejectCourse(courseName) {
  showToast(courseName + " has been rejected.");
  // In a real app, you would update the course status here
}

function viewCourseDetails(courseName) {
  showToast("Viewing details for " + courseName);
  // In a real app, you would open a detailed course modal
}

document
  .getElementById("collaboratorCoursesModal")
  .addEventListener("click", function (e) {
    if (e.target === this) {
      closeCollaboratorCoursesModal();
    }
  });

// ===== OPPORTUNITY MODAL =====
function openOpportunityModal(oppId = null) {
  editingOppId = oppId;
  const modal = document.getElementById("opportunityModal");
  const form = document.getElementById("opportunityForm");
  const modalTitle =
    modal.querySelector("h2") || modal.querySelector(".modal-header h2");

  if (oppId) {
    // Edit mode: populate form with existing opportunity data
    const opp = opportunities.find((o) => o.id === oppId);
    if (opp) {
      if (modalTitle) modalTitle.textContent = "Edit Opportunity";
      document.getElementById("oppName").value = opp.name;
      document.getElementById("oppDuration").value = opp.duration;
      document.getElementById("oppStartDate").value = opp.start_date;
      document.getElementById("oppDescription").value = opp.description;
      document.getElementById("oppSkills").value = opp.skills;
      document.getElementById("oppCategory").value = opp.category;
      document.getElementById("oppFuture").value = opp.future_opportunities;
      document.getElementById("oppMaxApplicants").value =
        opp.max_applicants || "";
    }
  } else {
    // Create mode: clear form
    if (modalTitle) modalTitle.textContent = "Create Opportunity";
    form.reset();
    editingOppId = null;
  }

  modal.classList.add("active");
}

function closeOpportunityModal() {
  document.getElementById("opportunityModal").classList.remove("active");
  editingOppId = null;
}

// Close modal when clicking outside
document
  .getElementById("opportunityModal")
  .addEventListener("click", function (e) {
    if (e.target === this) {
      closeOpportunityModal();
    }
  });

// Load opportunities from backend
async function loadOpportunities() {
  try {
    const res = await api("/api/opportunities", { method: "GET" });
    if (res.status === 200) {
      const data = await res.json();
      opportunities = data; // Store in global
      renderOpportunities();
    } else if (res.status === 401) {
      console.log("Not authenticated");
    } else {
      console.error("Failed to load opportunities", res.status);
    }
  } catch (err) {
    console.error("Error loading opportunities:", err);
  }
}

// Render opportunities to DOM
function renderOpportunities() {
  const grid = document.querySelector(".opportunities-grid");
  if (!grid) return;

  // Clear existing cards
  grid.innerHTML = "";

  opportunities.forEach((opp) => {
    const skills = opp.skills ? opp.skills.split(",").map((s) => s.trim()) : [];
    const card = document.createElement("div");
    card.className = "opportunity-card";
    card.setAttribute("data-opp-id", opp.id);

    const headerHtml = `
      <div class="opportunity-card-header">
        <h5>${escapeHtml(opp.name)}</h5>
        <div class="opportunity-meta">
          <span><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>${escapeHtml(opp.duration)}</span>
          <span><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>${escapeHtml(opp.start_date)}</span>
        </div>
      </div>
      <p class="opportunity-description">${escapeHtml(opp.description)}</p>
    `;

    const skillsHtml = `
      <div class="opportunity-skills">
        <div class="opportunity-skills-label">Skills You'll Gain</div>
        <div class="skills-tags">
          ${skills.map((s) => `<span class="skill-tag">${escapeHtml(s)}</span>`).join("")}
        </div>
      </div>
    `;

    const applicantsCount = opp.max_applicants
      ? `${parseInt(opp.max_applicants, 10)} applicants`
      : "0 applicants";
    const footerHtml = `
      <div class="opportunity-footer">
        <span class="applicants-count">${escapeHtml(applicantsCount)}</span>
        <div style="display: flex; gap: 8px;">
          <button class="view-course-btn" style="width: auto; padding: 8px 16px;">View Details</button>
          <button class="edit-opp-btn" style="width: auto; padding: 8px 16px; background: #4CAF50;">Edit</button>
          <button class="delete-opp-btn" style="width: auto; padding: 8px 16px; background: #f44336;">Delete</button>
        </div>
      </div>
    `;

    card.innerHTML = headerHtml + skillsHtml + footerHtml;

    // View Details button
    card
      .querySelector(".view-course-btn")
      .addEventListener("click", function () {
        openOpportunityDetails(opp.name, {
          duration: opp.duration,
          startDate: opp.start_date,
          description: opp.description,
          skills: skills,
          applicants: opp.max_applicants ? parseInt(opp.max_applicants, 10) : 0,
          futureOpportunities: opp.future_opportunities,
          prerequisites: "",
        });
      });

    // Edit button
    card.querySelector(".edit-opp-btn").addEventListener("click", function () {
      openOpportunityModal(opp.id);
    });

    // Delete button
    card
      .querySelector(".delete-opp-btn")
      .addEventListener("click", async function () {
        if (!confirm("Are you sure you want to delete this opportunity?"))
          return;
        try {
          const res = await api(`/api/opportunities/${opp.id}`, {
            method: "DELETE",
          });
          if (res.status === 204) {
            showToast("Opportunity deleted successfully!");
            await loadOpportunities();
          } else {
            showToast("Failed to delete opportunity");
          }
        } catch (err) {
          console.error("Delete error:", err);
          showToast("Error deleting opportunity");
        }
      });

    grid.appendChild(card);
  });
}

// Handle opportunity form submission
document
  .getElementById("opportunityForm")
  .addEventListener("submit", async function (e) {
    e.preventDefault();

    // Collect values
    const name = document.getElementById("oppName").value.trim();
    const duration = document.getElementById("oppDuration").value.trim();
    const startDate = document.getElementById("oppStartDate").value;
    const description = document.getElementById("oppDescription").value.trim();
    const skillsRaw = document.getElementById("oppSkills").value.trim();
    const category = document.getElementById("oppCategory").value;
    const futureOpportunities = document
      .getElementById("oppFuture")
      .value.trim();
    const maxApplicants = document
      .getElementById("oppMaxApplicants")
      .value.trim();

    // Basic validation
    if (
      !name ||
      !duration ||
      !startDate ||
      !description ||
      !skillsRaw ||
      !category ||
      !futureOpportunities
    ) {
      showToast("Please fill all required fields");
      return;
    }

    const payload = {
      name,
      duration,
      start_date: startDate,
      description,
      skills: skillsRaw,
      category,
      future_opportunities: futureOpportunities,
      max_applicants: maxApplicants ? parseInt(maxApplicants, 10) : null,
    };

    try {
      let res;
      if (editingOppId) {
        // Update existing opportunity
        res = await api(`/api/opportunities/${editingOppId}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
      } else {
        // Create new opportunity
        res = await api("/api/opportunities", {
          method: "POST",
          body: JSON.stringify(payload),
        });
      }

      const data = await res.json();

      if (res.status === 201 || res.status === 200) {
        showToast(
          editingOppId
            ? "Opportunity updated successfully!"
            : "Opportunity created successfully!",
        );
        closeOpportunityModal();
        this.reset();
        await loadOpportunities();
      } else if (res.status === 422) {
        showToast(
          "Validation error: " +
            (data.fields ? Object.values(data.fields).join(", ") : data.error),
        );
      } else {
        showToast("Error: " + (data.error || "Unknown error"));
      }
    } catch (err) {
      console.error("Opportunity error:", err);
      showToast("Network error. Please try again.");
    }
  });

// small helper to avoid HTML injection when inserting text
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// ===== QUICK ADD STUDENT MODAL =====
function openQuickAddModal() {
  document.getElementById("quickAddModal").classList.add("active");
}

function closeQuickAddModal() {
  document.getElementById("quickAddModal").classList.remove("active");
}

document
  .getElementById("quickAddModal")
  .addEventListener("click", function (e) {
    if (e.target === this) {
      closeQuickAddModal();
    }
  });

document
  .getElementById("quickAddForm")
  .addEventListener("submit", function (e) {
    e.preventDefault();
    showToast("Student added successfully! Email invitation sent.");
    closeQuickAddModal();
    this.reset();
  });

// ===== BULK UPLOAD MODAL =====
function openBulkUploadModal() {
  document.getElementById("bulkUploadModal").classList.add("active");
}

function closeBulkUploadModal() {
  document.getElementById("bulkUploadModal").classList.remove("active");
}

document
  .getElementById("bulkUploadModal")
  .addEventListener("click", function (e) {
    if (e.target === this) {
      closeBulkUploadModal();
    }
  });

document
  .getElementById("bulkUploadForm")
  .addEventListener("submit", function (e) {
    e.preventDefault();
    const fileInput = document.getElementById("csvFileInput");
    if (fileInput.files.length === 0) {
      showToast("Please select a CSV file");
      return;
    }
    showToast("Students uploaded successfully! Email invitations sent.");
    closeBulkUploadModal();
    this.reset();
    document.getElementById("fileName").textContent = "";
  });

function handleFileSelect(event) {
  const file = event.target.files[0];
  if (file) {
    document.getElementById("fileName").textContent =
      "✓ Selected: " + file.name;
  }
}

function downloadSampleCSV() {
  const csvContent =
    "First Name,Last Name,Email\nJohn,Doe,john.doe@example.com\nJane,Smith,jane.smith@example.com";
  const blob = new Blob([csvContent], { type: "text/csv" });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "sample_students.csv";
  a.click();
  window.URL.revokeObjectURL(url);
}

// ===== QUICK ADD VERIFIER MODAL =====
function openQuickAddVerifierModal() {
  document.getElementById("quickAddVerifierModal").classList.add("active");
}

function closeQuickAddVerifierModal() {
  document.getElementById("quickAddVerifierModal").classList.remove("active");
}

document
  .getElementById("quickAddVerifierModal")
  .addEventListener("click", function (e) {
    if (e.target === this) {
      closeQuickAddVerifierModal();
    }
  });

document
  .getElementById("quickAddVerifierForm")
  .addEventListener("submit", function (e) {
    e.preventDefault();
    showToast("Verifier added successfully! Email invitation sent.");
    closeQuickAddVerifierModal();
    this.reset();
  });

// ===== BULK UPLOAD VERIFIER MODAL =====
function openBulkUploadVerifierModal() {
  document.getElementById("bulkUploadVerifierModal").classList.add("active");
}

function closeBulkUploadVerifierModal() {
  document.getElementById("bulkUploadVerifierModal").classList.remove("active");
}

document
  .getElementById("bulkUploadVerifierModal")
  .addEventListener("click", function (e) {
    if (e.target === this) {
      closeBulkUploadVerifierModal();
    }
  });

document
  .getElementById("bulkUploadVerifierForm")
  .addEventListener("submit", function (e) {
    e.preventDefault();
    const fileInput = document.getElementById("csvVerifierFileInput");
    if (fileInput.files.length === 0) {
      showToast("Please select a CSV file");
      return;
    }
    showToast("Verifiers uploaded successfully! Email invitations sent.");
    closeBulkUploadVerifierModal();
    this.reset();
    document.getElementById("verifierFileName").textContent = "";
  });

function handleVerifierFileSelect(event) {
  const file = event.target.files[0];
  if (file) {
    document.getElementById("verifierFileName").textContent =
      "✓ Selected: " + file.name;
  }
}

function downloadSampleVerifierCSV() {
  const csvContent =
    "First Name,Last Name,Email,Subject\nDr. John,Doe,john.doe@qf.edu.qa,Mathematics\nProf. Jane,Smith,jane.smith@qf.edu.qa,Physics";
  const blob = new Blob([csvContent], { type: "text/csv" });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "sample_verifiers.csv";
  a.click();
  window.URL.revokeObjectURL(url);
}

// ===== VERIFIER DETAILS MODAL =====
function openVerifierDetails(name, stats) {
  document.getElementById("verifierName").textContent = name;
  document.getElementById("verifierTotalStudents").textContent =
    stats.totalStudents;
  document.getElementById("verifierCertified").textContent = stats.certified;
  document.getElementById("verifierInProgress").textContent = stats.inProgress;

  // Populate subjects
  const container = document.getElementById("subjectsContainer");
  container.innerHTML = "";
  stats.subjects.forEach((subject) => {
    const div = document.createElement("div");
    div.className = "subject-item";
    div.innerHTML = `
            <span class="subject-name">${subject.name}</span>
            <span class="subject-students">${subject.students} students</span>
        `;
    container.appendChild(div);
  });

  document.getElementById("verifierDetailsModal").classList.add("active");
}

function closeVerifierDetailsModal() {
  document.getElementById("verifierDetailsModal").classList.remove("active");
}

document
  .getElementById("verifierDetailsModal")
  .addEventListener("click", function (e) {
    if (e.target === this) {
      closeVerifierDetailsModal();
    }
  });

// ===== STUDENT FILTERS =====
function filterStudents() {
  const statusFilter = document.getElementById("statusFilter").value;
  const dateFrom = document.getElementById("dateFrom").value;
  const dateTo = document.getElementById("dateTo").value;

  const rows = document.querySelectorAll("#studentsTableBody tr");

  rows.forEach((row) => {
    const rowStatus = row.getAttribute("data-status");
    let showRow = true;

    // Status filter
    if (statusFilter !== "all" && rowStatus !== statusFilter) {
      showRow = false;
    }

    // Date filters would be implemented here with actual date data

    row.style.display = showRow ? "" : "none";
  });
}

// ===== VERIFIER FILTERS =====
function filterVerifiers() {
  const statusFilter = document.getElementById("verifierStatusFilter").value;
  const dateFrom = document.getElementById("verifierDateFrom").value;
  const dateTo = document.getElementById("verifierDateTo").value;

  const rows = document.querySelectorAll("#verifiersTableBody tr");

  rows.forEach((row) => {
    const rowStatus = row.getAttribute("data-status");
    let showRow = true;

    // Status filter
    if (statusFilter !== "all" && rowStatus !== statusFilter) {
      showRow = false;
    }

    // Date filters would be implemented here with actual date data

    row.style.display = showRow ? "" : "none";
  });
}

// ===== LOGIN =====
document
  .getElementById("loginForm")
  .addEventListener("submit", async function (e) {
    e.preventDefault();
    clearAllErrors("loginForm");

    let valid = true;
    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value.trim();
    const rememberMe = document.getElementById("rememberMe")?.checked || false;
    const captchaInput = document
      .getElementById("loginCaptchaInput")
      .value.trim();

    if (!email || !isValidEmail(email)) {
      showError("loginEmailErr");
      document.getElementById("loginEmail").classList.add("error");
      valid = false;
    }
    if (!password) {
      showError("loginPasswordErr", "Please enter your password");
      document.getElementById("loginPassword").classList.add("error");
      valid = false;
    }
    if (!captchaInput) {
      showError("loginCaptchaErr", "Please enter the captcha code");
      valid = false;
    } else if (captchaInput !== captchas.login) {
      showError("loginCaptchaErr", "Captcha does not match. Please try again.");
      valid = false;
      generateCaptcha("login");
    }

    if (!valid) {
      shakeForm("loginForm");
      return;
    }

    // Send to backend
    try {
      const { data, status } = await apiJson("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: email,
          password: password,
          remember_me: rememberMe,
        }),
      });

      if (status === 200) {
        // Success — session started
        showToast("Login successful! Redirecting...");
        setTimeout(() => showDashboard(data.full_name), 1200);
        generateCaptcha("login");
      } else if (status === 401) {
        // Invalid credentials
        showError("loginPasswordErr", "Invalid email or password");
        document.getElementById("loginPassword").classList.add("error");
      } else {
        showToast("Login failed: " + (data.error || "Unknown error"));
      }
    } catch (err) {
      console.error("Login error:", err);
      showToast("Network error. Please try again.");
    }
  });

// ===== SIGNUP =====
document
  .getElementById("signupForm")
  .addEventListener("submit", async function (e) {
    e.preventDefault();
    clearAllErrors("signupForm");

    let valid = true;
    const fullName = document.getElementById("signupName").value.trim();
    const email = document.getElementById("signupEmail").value.trim();
    const password = document.getElementById("signupPassword").value.trim();
    const confirmPassword = document
      .getElementById("signupConfirmPassword")
      .value.trim();
    const captchaInput = document
      .getElementById("signupCaptchaInput")
      .value.trim();

    // Client-side validation (UX — instant feedback)
    if (!fullName) {
      showError("signupNameErr");
      document.getElementById("signupName").classList.add("error");
      valid = false;
    }
    if (!email || !isValidEmail(email)) {
      showError("signupEmailErr");
      document.getElementById("signupEmail").classList.add("error");
      valid = false;
    }
    if (!password || password.length < 8) {
      showError("signupPasswordErr");
      document.getElementById("signupPassword").classList.add("error");
      valid = false;
    }
    if (!confirmPassword || password !== confirmPassword) {
      showError("signupConfirmPasswordErr");
      document.getElementById("signupConfirmPassword").classList.add("error");
      valid = false;
    }
    if (!captchaInput) {
      showError("signupCaptchaErr", "Please enter the captcha code");
      valid = false;
    } else if (captchaInput !== captchas.signup) {
      showError("signupCaptchaErr", "Captcha does not match.");
      valid = false;
      generateCaptcha("signup");
    }

    if (!valid) {
      shakeForm("signupForm");
      return;
    }

    // Send to backend
    try {
      const { data, status } = await apiJson("/api/auth/signup", {
        method: "POST",
        body: JSON.stringify({
          full_name: fullName,
          email: email,
          password: password,
          confirm_password: confirmPassword,
        }),
      });

      if (status === 201) {
        // Success — account created
        showToast("Account created successfully! Redirecting to login...");
        generateCaptcha("signup");
        this.reset();
        checkStrength("");
        setTimeout(() => showPage("loginPage"), 1500);
      } else if (status === 409) {
        // Email already exists
        showError(
          "signupEmailErr",
          "An account with this email already exists",
        );
        document.getElementById("signupEmail").classList.add("error");
      } else if (status === 422) {
        // Validation error — show field-specific errors
        if (data.fields) {
          Object.entries(data.fields).forEach(([field, message]) => {
            const errId = `signup${field.charAt(0).toUpperCase() + field.slice(1)}Err`;
            const inputId = `signup${field.charAt(0).toUpperCase() + field.slice(1)}`;
            const errEl = document.getElementById(errId);
            const inputEl = document.getElementById(inputId);
            if (errEl) {
              showError(errId, message);
              if (inputEl) inputEl.classList.add("error");
            }
          });
        }
      } else {
        showToast("Signup failed: " + (data.error || "Unknown error"));
      }
    } catch (err) {
      console.error("Signup error:", err);
      showToast("Network error. Please try again.");
    }
  });

// ===== FORGOT PASSWORD =====
document
  .getElementById("forgotForm")
  .addEventListener("submit", async function (e) {
    e.preventDefault();
    clearAllErrors("forgotForm");

    let valid = true;
    const email = document.getElementById("forgotEmail").value.trim();
    const captchaInput = document
      .getElementById("forgotCaptchaInput")
      .value.trim();

    if (!email || !isValidEmail(email)) {
      showError("forgotEmailErr");
      document.getElementById("forgotEmail").classList.add("error");
      valid = false;
    }
    if (!captchaInput) {
      showError("forgotCaptchaErr", "Please enter the captcha code");
      valid = false;
    } else if (captchaInput !== captchas.forgot) {
      showError("forgotCaptchaErr", "Captcha does not match.");
      valid = false;
      generateCaptcha("forgot");
    }

    if (!valid) {
      shakeForm("forgotForm");
      return;
    }

    // Send to backend (always returns 200, don't leak email existence)
    try {
      const { data, status } = await apiJson("/api/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email: email }),
      });

      if (status === 200) {
        showToast("If an account exists, a reset email has been sent");
        generateCaptcha("forgot");
        this.reset();
      } else {
        showToast("Request failed: " + (data.error || "Unknown error"));
      }
    } catch (err) {
      console.error("Forgot password error:", err);
      showToast("Network error. Please try again.");
    }
  });

// Clear errors on input
document.querySelectorAll("input").forEach((input) => {
  input.addEventListener("input", function () {
    this.classList.remove("error");
    const err = this.closest(".form-group")?.querySelector(".error-msg");
    if (err) err.classList.remove("show");
  });
});

// Responsive sidebar
window.addEventListener("resize", () => {
  const toggle = document.getElementById("menuToggle");
  if (toggle) toggle.style.display = window.innerWidth <= 768 ? "flex" : "none";
});

// ===== PAGE INITIALIZATION =====
// On page load, check if user already has an active session
document.addEventListener("DOMContentLoaded", () => {
  initializePageOnLoad();
});
