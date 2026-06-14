/**
 * CarbonAI Frontend Application
 *
 * Handles form submission, API communication, chart rendering,
 * history management, toast notifications, modal dialogs, and
 * accessibility announcements for the Carbon Footprint Tracker.
 */

const API_BASE = window.location.origin + "/api";

/** @type {Chart|null} Active Chart.js doughnut instance */
let breakdownChart = null;

// --- Tailwind class-string constants (eliminates duplication) ---

/** @type {string} Score style for high eco scores (>= 75) */
const SCORE_CLASS_HIGH =
  "text-4xl font-black text-emerald-400 tracking-tight transition-all duration-500 drop-shadow-[0_0_8px_rgba(52,211,153,0.3)]";

/** @type {string} Score style for moderate eco scores (40-74) */
const SCORE_CLASS_MID =
  "text-4xl font-black text-yellow-400 tracking-tight transition-all duration-500 drop-shadow-[0_0_8px_rgba(250,204,21,0.3)]";

/** @type {string} Score style for low eco scores (< 40) */
const SCORE_CLASS_LOW =
  "text-4xl font-black text-rose-500 tracking-tight transition-all duration-500 drop-shadow-[0_0_8px_rgba(244,63,94,0.3)]";

/** @type {string} Eco score container style for high scores */
const ECO_CLASS_HIGH =
  "mt-1 text-3xl font-extrabold text-emerald-400 transition-all duration-500 drop-shadow-[0_0_8px_rgba(52,211,153,0.3)]";

/** @type {string} Eco score container style for moderate scores */
const ECO_CLASS_MID =
  "mt-1 text-3xl font-extrabold text-yellow-400 transition-all duration-500 drop-shadow-[0_0_8px_rgba(250,204,21,0.3)]";

/** @type {string} Eco score container style for low scores */
const ECO_CLASS_LOW =
  "mt-1 text-3xl font-extrabold text-rose-500 transition-all duration-500 drop-shadow-[0_0_8px_rgba(244,63,94,0.3)]";

/** @type {string} Default score class before any calculation */
const SCORE_CLASS_DEFAULT =
  "text-4xl font-black text-emerald-400 tracking-tight transition-all duration-500";

/** @type {string} Default eco score container class */
const ECO_CLASS_DEFAULT =
  "mt-1 text-3xl font-extrabold text-emerald-400 transition-all duration-500";

// --- DOM Element References ---

const trackerForm = document.getElementById("tracker-form");
const resetBtn = document.getElementById("reset-btn");
const contrastToggle = document.getElementById("contrast-toggle");
const clearHistoryBtn = document.getElementById("clear-history-btn");
const historyRows = document.getElementById("history-rows");
const scoreValue = document.getElementById("score-value");
const scoreVerdict = document.getElementById("score-verdict");
const recommendationsList = document.getElementById("recommendations-list");
const ecoScoreValue = document.getElementById("eco-score-value");
const ecoScoreContainer = document.getElementById("eco-score-container");
const insightCallout = document.getElementById("insight-callout");
const insightText = document.getElementById("insight-text");
const toastAnnouncement = document.getElementById("toast-announcement");
const chartPlaceholder = document.getElementById("chart-placeholder");
const savingsWidget = document.getElementById("savings-widget");
const savingsDiet = document.getElementById("savings-diet");
const savingsTransport = document.getElementById("savings-transport");

// --- Accessibility helpers ---

/**
 * Push a message into the sr-only live region so screen readers announce it.
 * @param {string} message - The message to announce.
 */
function announceToScreenReader(message) {
  toastAnnouncement.textContent = message;
  // Clear after a delay to allow repeat announcements
  setTimeout(() => {
    toastAnnouncement.textContent = "";
  }, 10000);
}

// --- Premium Modal System ---

/** @type {Function|null} Callback invoked when the modal Confirm button is pressed */
let modalCallback = null;

const customModal = document.getElementById("custom-modal");
const modalCancelBtn = document.getElementById("modal-cancel-btn");
const modalConfirmBtn = document.getElementById("modal-confirm-btn");
const modalBox = document.getElementById("modal-box");

/**
 * Display a confirmation modal with custom title, message, and confirm handler.
 * @param {string} title   - The modal heading text.
 * @param {string} message - The modal description text.
 * @param {Function} onConfirm - Async callback executed on confirmation.
 */
function showConfirmModal(title, message, onConfirm) {
  document.getElementById("modal-title").textContent = title;
  document.getElementById("modal-desc").textContent = message;
  modalCallback = onConfirm;

  customModal.classList.remove("hidden");
  // Force a small reflow to trigger CSS scale transition
  void customModal.offsetWidth;
  customModal.classList.add("modal-visible");
}

/**
 * Dismiss the confirmation modal with an exit animation.
 */
function hideConfirmModal() {
  customModal.classList.remove("modal-visible");
  setTimeout(() => {
    customModal.classList.add("hidden");
    modalCallback = null;
  }, 300);
}

modalCancelBtn.addEventListener("click", () => {
  hideConfirmModal();
});

modalConfirmBtn.addEventListener("click", () => {
  if (modalCallback) modalCallback();
  hideConfirmModal();
});

customModal.addEventListener("click", (e) => {
  if (e.target === customModal) {
    hideConfirmModal();
  }
});

// --- Premium Toast System ---

const toastContainer = document.getElementById("toast-container");

/**
 * Show a premium toast notification with auto-dismiss and manual close.
 * @param {string} message - Notification message text.
 * @param {"info"|"success"|"error"} [type="info"] - Visual style variant.
 */
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast-item pointer-events-auto flex items-center justify-between p-4 rounded-xl border glass-panel w-80 text-sm font-medium text-slate-100 ${
    type === "success" ? "toast-success" : type === "error" ? "toast-error" : "toast-info"
  }`;

  const icon =
    type === "success"
      ? `<svg class="w-5 h-5 text-emerald-400 mr-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`
      : type === "error"
      ? `<svg class="w-5 h-5 text-rose-500 mr-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`
      : `<svg class="w-5 h-5 text-cyan-400 mr-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>`;

  toast.innerHTML = `
    <div class="flex items-center">
      ${icon}
      <span>${message}</span>
    </div>
    <button class="ml-4 text-slate-400 hover:text-slate-200 focus:outline-none focus:ring-2 focus:ring-slate-500 rounded p-0.5" aria-label="Close notification">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
    </button>
  `;

  toast.querySelector("button").addEventListener("click", () => {
    toast.classList.remove("toast-show");
    setTimeout(() => toast.remove(), 300);
  });

  toastContainer.appendChild(toast);

  void toast.offsetWidth;
  toast.classList.add("toast-show");

  setTimeout(() => {
    if (toast.parentElement) {
      toast.classList.remove("toast-show");
      setTimeout(() => toast.remove(), 300);
    }
  }, 5000);

  announceToScreenReader(message);
}

// --- Utility Formatters ---

/**
 * Format an ISO 8601 date string into a user-friendly short format.
 * @param {string} isoString - ISO 8601 timestamp.
 * @returns {string} Formatted date like "Jun 14, 10:30 AM".
 */
function formatDate(isoString) {
  try {
    const date = new Date(isoString);
    return date.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch (_e) {
    return isoString;
  }
}

/**
 * Convert a snake_case category key to a Title Case label.
 * @param {string} str - Snake-case string like "driving_gasoline".
 * @returns {string} Title-cased string like "Driving Gasoline".
 */
function cleanCategoryLabel(str) {
  return str
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/**
 * Safely escape HTML special characters to prevent XSS when building markup.
 * @param {string} text - Raw text that may contain HTML characters.
 * @returns {string} Escaped text safe for innerHTML insertion.
 */
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// --- High Contrast Mode ---

contrastToggle.addEventListener("click", () => {
  const isHighContrast = document.body.classList.toggle("high-contrast");
  announceToScreenReader(
    isHighContrast ? "High contrast mode enabled." : "High contrast mode disabled."
  );
});

// --- History Management ---

/**
 * Fetch all calculation history from the backend and render it.
 */
async function fetchHistory() {
  try {
    const response = await fetch(`${API_BASE}/history`);
    if (!response.ok) throw new Error("Failed to load history.");

    const logs = await response.json();
    renderHistory(logs);
  } catch (error) {
    console.error(error);
    historyRows.innerHTML = `
      <tr>
        <td colspan="5" class="py-4 text-center text-rose-400">
          Error loading history from server. Ensure FastAPI backend is running on port 8000.
        </td>
      </tr>
    `;
  }
}

/**
 * Render history log rows into the table body.
 * Uses data-log-id attributes for delegated event handling instead of inline onclick.
 * @param {Array<Object>} logs - Array of CalculationResponse objects.
 */
function renderHistory(logs) {
  if (logs.length === 0) {
    historyRows.innerHTML = `
      <tr>
        <td colspan="5" class="py-6 text-center italic text-slate-500">
          No calculations logged yet.
        </td>
      </tr>
    `;
    clearHistoryBtn.classList.add("hidden");
    return;
  }

  clearHistoryBtn.classList.remove("hidden");
  historyRows.innerHTML = logs
    .map(
      (log) => `
      <tr class="hover:bg-slate-900/40 transition-colors">
        <td class="py-3 px-3 text-slate-300 font-medium">${escapeHtml(formatDate(log.timestamp))}</td>
        <td class="py-3 px-3">
          ${escapeHtml(cleanCategoryLabel(log.inputs.transport.transport_type))}
          <span class="text-xs text-slate-500 block">${escapeHtml(String(log.inputs.transport.distance_km))} km</span>
        </td>
        <td class="py-3 px-3">
          ${escapeHtml(cleanCategoryLabel(log.inputs.diet.diet_type))}
          <span class="text-xs text-slate-500 block">${escapeHtml(String(log.inputs.diet.days))} day(s)</span>
        </td>
        <td class="py-3 px-3 font-semibold text-emerald-400">${escapeHtml(log.total_co2_kg.toFixed(1))} kg</td>
        <td class="py-3 px-3 text-right">
          <button
            data-log-id="${escapeHtml(log.id)}"
            class="delete-log-btn text-xs font-semibold text-rose-500 hover:text-rose-400 bg-rose-500/10 hover:bg-rose-500/20 px-2 py-1 rounded transition-colors focus:outline-none focus:ring-2 focus:ring-rose-500"
            aria-label="Delete entry from ${escapeHtml(formatDate(log.timestamp))}"
          >
            Delete
          </button>
        </td>
      </tr>
    `
    )
    .join("");
}

/**
 * Delete a single log entry by ID after user confirmation.
 * @param {string} id - UUID of the log entry to delete.
 */
async function deleteLog(id) {
  showConfirmModal(
    "Delete Log Entry",
    "Are you sure you want to delete this carbon footprint calculation record?",
    async () => {
      try {
        const response = await fetch(`${API_BASE}/history/${encodeURIComponent(id)}`, {
          method: "DELETE",
        });
        if (!response.ok) throw new Error("Failed to delete log entry.");

        showToast("Log entry deleted successfully.", "success");
        fetchHistory();
      } catch (error) {
        console.error(error);
        showToast("Could not delete log entry. Is the backend running?", "error");
      }
    }
  );
}

// Delegated event listener for delete buttons (replaces inline onclick)
historyRows.addEventListener("click", (e) => {
  const btn = e.target.closest(".delete-log-btn");
  if (btn) {
    const logId = btn.dataset.logId;
    if (logId) deleteLog(logId);
  }
});

// --- Clear All History ---

clearHistoryBtn.addEventListener("click", () => {
  showConfirmModal(
    "Clear Calculation History",
    "Are you sure you want to clear all history logs? This action is permanent.",
    async () => {
      try {
        const response = await fetch(`${API_BASE}/history`, {
          method: "DELETE",
        });
        if (!response.ok) throw new Error("Failed to clear history.");

        showToast("All logs cleared successfully.", "success");
        fetchHistory();
        resetDashboard();
      } catch (error) {
        console.error(error);
        showToast("Could not clear history. Is the backend running?", "error");
      }
    }
  );
});

// --- Dashboard Reset ---

/**
 * Reset the dashboard UI to its initial empty state.
 */
function resetDashboard() {
  scoreValue.textContent = "0.0";
  scoreValue.className = SCORE_CLASS_DEFAULT;
  scoreVerdict.textContent = "Submit activities to estimate Eco Score.";
  ecoScoreValue.textContent = "--";
  ecoScoreContainer.className = ECO_CLASS_DEFAULT;
  insightCallout.classList.add("hidden");
  insightText.textContent = "";

  savingsWidget.classList.add("hidden");
  savingsDiet.innerHTML = "";
  savingsTransport.innerHTML = "";

  recommendationsList.innerHTML = `
    <li class="p-3 bg-slate-950/40 rounded-xl border border-slate-800/50 text-slate-400 italic">
      Input logs to trigger AI recommendations for offsetting emission footprints.
    </li>
  `;

  if (breakdownChart) {
    breakdownChart.destroy();
    breakdownChart = null;
  }
  chartPlaceholder.classList.remove("hidden");
}

// Reset Form & Dashboard UI
resetBtn.addEventListener("click", () => {
  trackerForm.reset();
  resetDashboard();
  announceToScreenReader("Form and dashboard reset successfully.");
});

// --- Chart.js Rendering ---

/**
 * Create or replace the doughnut chart showing per-category CO2 breakdown.
 * @param {Object} breakdown - Breakdown object with transport, diet, energy, waste floats.
 */
function updateChart(breakdown) {
  chartPlaceholder.classList.add("hidden");

  const ctx = document.getElementById("breakdown-chart").getContext("2d");

  if (breakdownChart) {
    breakdownChart.destroy();
  }

  const dataValues = [breakdown.transport, breakdown.diet, breakdown.energy, breakdown.waste];

  breakdownChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Transport", "Diet", "Energy", "Waste"],
      datasets: [
        {
          data: dataValues,
          backgroundColor: [
            "rgba(16, 185, 129, 0.8)", // emerald
            "rgba(20, 184, 166, 0.8)", // teal
            "rgba(234, 179, 8, 0.8)", // yellow
            "rgba(244, 63, 94, 0.8)", // rose
          ],
          borderColor: ["#020617", "#020617", "#020617", "#020617"],
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: "bottom",
          labels: {
            color: "#94a3b8", // slate-400
            font: {
              family: "Outfit",
              size: 11,
            },
            padding: 10,
          },
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              return ` ${context.label}: ${context.raw.toFixed(1)} kg CO2e`;
            },
          },
        },
      },
      cutout: "70%",
    },
  });
}

// --- Form Submission Handler ---

trackerForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  // Extract inputs
  const formData = new FormData(trackerForm);
  const payload = {
    transport: {
      transport_type: formData.get("transport_type"),
      distance_km: parseFloat(formData.get("distance_km") || 0),
    },
    diet: {
      diet_type: formData.get("diet_type"),
      days: parseInt(formData.get("diet_days") || 1),
    },
    energy: {
      electricity_kwh: parseFloat(formData.get("electricity_kwh") || 0),
      electricity_type: formData.get("electricity_type"),
      gas_kwh: parseFloat(formData.get("gas_kwh") || 0),
    },
    waste: {
      unsorted_waste_kg: parseFloat(formData.get("unsorted_waste_kg") || 0),
      recycled_waste_kg: parseFloat(formData.get("recycled_waste_kg") || 0),
    },
  };

  try {
    const response = await fetch(`${API_BASE}/calculate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail?.[0]?.msg || "Failed to calculate carbon footprint.");
    }

    const data = await response.json();

    // Update Score & Eco Score
    const score = data.total_co2_kg;
    scoreValue.textContent = score.toFixed(1);

    const ecoScore = data.eco_score;
    ecoScoreValue.textContent = ecoScore;

    // Adjust colors based on Eco Score (visual cues)
    if (ecoScore >= 75) {
      scoreValue.className = SCORE_CLASS_HIGH;
      ecoScoreContainer.className = ECO_CLASS_HIGH;
      scoreVerdict.textContent = "High Eco Score! Excellent low-emission profile.";
    } else if (ecoScore >= 40) {
      scoreValue.className = SCORE_CLASS_MID;
      ecoScoreContainer.className = ECO_CLASS_MID;
      scoreVerdict.textContent = "Moderate Eco Score. Potential adjustments can help.";
    } else {
      scoreValue.className = SCORE_CLASS_LOW;
      ecoScoreContainer.className = ECO_CLASS_LOW;
      scoreVerdict.textContent = "Low Eco Score. Please review offsets & recommendations.";
    }

    // Render AI Witty Micro-Insight
    insightCallout.classList.remove("hidden");
    insightText.textContent = `"${data.micro_insight}"`;

    // Render savings comparison
    savingsWidget.classList.remove("hidden");

    // Determine labels for diet savings
    const dietType = payload.diet.diet_type;
    const isDietSaved = ["vegan", "vegetarian"].includes(dietType);
    savingsDiet.innerHTML = `
      <span>Diet ${isDietSaved ? "Saved" : "Potential Savings"}:</span>
      <span class="font-bold">${isDietSaved ? "+" : "-"}${data.savings.diet_saving_kg.toFixed(1)} kg</span>
    `;
    savingsDiet.className = `flex justify-between items-center ${isDietSaved ? "text-emerald-400" : "text-slate-300"}`;

    // Determine labels for transport savings
    const transportType = payload.transport.transport_type;
    const isTransitSaved = [
      "driving_electric",
      "public_transit_bus",
      "public_transit_train",
      "walking_biking",
    ].includes(transportType);
    savingsTransport.innerHTML = `
      <span>Transit ${isTransitSaved ? "Saved" : "Potential Savings"}:</span>
      <span class="font-bold">${isTransitSaved ? "+" : "-"}${data.savings.transport_saving_kg.toFixed(1)} kg</span>
    `;
    savingsTransport.className = `flex justify-between items-center ${isTransitSaved ? "text-emerald-400" : "text-slate-300"}`;

    // Render recommendations list (with HTML escaping)
    recommendationsList.innerHTML = data.recommendations
      .map(
        (rec) => `
        <li class="flex items-start space-x-2.5 p-3 bg-slate-950/60 rounded-xl border border-slate-800/80 hover:border-slate-700/80 transition-colors">
          <svg class="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>${escapeHtml(rec)}</span>
        </li>
      `
      )
      .join("");

    // Update Chart
    updateChart(data.breakdown);

    // Refresh history grid
    await fetchHistory();

    // Trigger success notification
    showToast("Carbon footprint calculated successfully!", "success");
  } catch (error) {
    console.error(error);
    showToast(error.message || "Error submitting calculation payload.", "error");
  }
});

// --- Initialization ---

document.addEventListener("DOMContentLoaded", () => {
  fetchHistory();
});
