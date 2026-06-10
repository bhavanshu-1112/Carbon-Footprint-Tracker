# CarbonAI — Carbon Footprint awareness and tracking platform

CarbonAI is a full-stack interactive carbon footprint tracking dashboard. It empowers users to monitor their carbon output across multiple categories, view historical trends via custom visual charts, calculate their personal **Eco Score**, and receive witty, AI-driven daily carbon offset suggestions powered by the **Gemini API**.

---

## 🚀 Key Features

- **Activity Log Estimator:** Computes carbon equivalent emissions (kg CO2e) for daily Transportation, Diet, Home Energy, and Waste output.
- **Dynamic Eco Score:** Evaluates daily profiles to compute a numeric sustainability rating out of 100.
- **AI Witty Micro-Insights:** Leverages the **Gemini API** (`gemini-1.5-flash`) to generate witty, personalized 2-sentence tips based on the user's highest footprint category. Includes a graceful local offline fallback.
- **Interactive Breakdown Charts:** Visualizes emissions breakdowns in real-time using **Chart.js** with premium glassmorphism themes.
- **Saved History Logs:** Tracks records in a mock database (`database.json`) with capabilities to delete specific logs or clear history.
- **WCAG 2.1 AA Compliance:** Follows standard web accessibility rules (semantic components, explicit focus highlights, high-contrast toggle, and live aria screen-reader alerts).
- **High Security & Performance:** Employs async API routes, strict Pydantic payload models, and secure HTTP headers (CSP, X-Frame-Options, X-Content-Type-Options).

---

## 🛠️ Technology Stack

- **Backend:** FastAPI, Pydantic, HTTPX, PyTest, Uvicorn (Python)
- **Frontend:** HTML5, Tailwind CSS, Chart.js, Vanilla CSS, Vanilla JavaScript

---

## ⚙️ Getting Started

### 1. Prerequisites
- Python 3.10+
- pip (Python package installer)

### 2. Backend Setup
1. Open a terminal and navigate to the project directory.
2. Install the backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Set your Gemini API Key as an environment variable (optional, falls back to offline mode if unset):
   - **Linux/macOS:**
     ```bash
     export GEMINI_API_KEY="your_api_key_here"
     ```
   - **Windows (PowerShell):**
     ```powershell
     $env:GEMINI_API_KEY="your_api_key_here"
     ```
4. Start the FastAPI backend server using Uvicorn:
   ```bash
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```
   *The Swagger UI documentation is available at `http://127.0.0.1:8000/docs`.*

### 3. Frontend Setup
1. Serve the frontend static directory using Python's built-in HTTP server or open `frontend/index.html` in your browser:
   ```bash
   python -m http.server 5000 --directory frontend
   ```
2. Navigate to `http://localhost:5000` in your web browser.

---

## 🧪 Testing

The backend test suite is managed via PyTest. To run the validation checks:
```bash
python -m pytest backend/tests/
```
These tests cover endpoint health, request schema validations, emission calculations, history database mutations, and mock responses.

---

## 📂 Project Structure

```
.
├── backend/
│   ├── calculator.py       # Footprint formulas and witty fallback logic
│   ├── gemini_service.py   # Gemini API integration service
│   ├── main.py             # FastAPI server, endpoints, and security middleware
│   ├── requirements.txt    # Python packages
│   ├── schemas.py          # Pydantic validation models
│   └── tests/
│       ├── conftest.py     # PyTest fixtures and mock database setup
│       └── test_main.py    # Endpoint integration tests
├── frontend/
│   ├── app.js              # State logic, API fetchers, and Chart.js integration
│   ├── index.html          # Semantic, accessible web page markup
│   └── style.css           # Custom styles, focus-rings, and accessibility modes
├── database.json           # Mock JSON database containing constants and logs
├── .gitignore              # Git ignore rules for cached/sensitive files
└── README.md               # Project documentation
```
