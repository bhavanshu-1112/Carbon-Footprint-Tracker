# Hackathon Target Architecture & Evaluation Rules
- **Theme:** Carbon Footprint Awareness Platform
- **Stack:** FastAPI Backend, HTML5 / TailwindCSS Frontend

# Strict Engineering Quality Parameters (AI Judge Targets):
1. **Efficiency:** Backend endpoints must utilize asynchronous operations (`async/def`) and avoid redundant calculations. Front-end components must be lightweight with minimal paint cycles.
2. **Accessibility (a11y):** Strict compliance with WCAG 2.1 AA standards. Semantic HTML only, visible focus states, aria-labels for dynamic elements, and a clean accessibility tree.
3. **Security:** Implement parameterized data payloads, strong CORS configurations, secure headers, and strict data validation using Pydantic. 
4. **Testing:** Minimum 80% test coverage using PyTest for the backend logic and visual regression checkpoints for the frontend UI.