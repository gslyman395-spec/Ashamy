# Ashamy

Minimal reconstruction of the missing Ashamy project pieces so the repository is understandable and runnable in development.

## What is included

- `/backend/api/routes.py` — a small FastAPI backend with mock responses for the existing mobile screens
- `/mobile/` — the original React Native screens, now using a shared API config module
- `/App.js` and `/package.json` — a tiny Expo shell to switch between the two screens
- `/tests/test_api.py` — focused backend tests for the mock API and WebSocket stream

## Backend

Install the lightweight Python dependencies and run the API:

```bash
cd /home/runner/work/Ashamy/Ashamy
python -m pip install -r requirements.txt
python -m uvicorn backend.api.routes:app --reload
```

Available development endpoints:

- `GET /health`
- `GET /api/v1/leaderboard`
- `GET /api/v1/signals/{symbol}`
- `POST /api/v1/ai/run-tests`
- `POST /api/v1/ai/optimize`
- `POST /api/v1/ai/update-models`
- `POST /api/v1/ai/cleanup`
- `POST /api/v1/ai/security-scan`
- `WS /ws/signals`

Run backend tests:

```bash
cd /home/runner/work/Ashamy/Ashamy
python -m unittest discover -s tests -v
```

## Mobile

The repository still contains only a minimal mobile shell, not a full production application.

```bash
cd /home/runner/work/Ashamy/Ashamy
npm install
npm start
```

By default the mobile app talks to:

- iOS / web: `http://localhost:8000`
- Android emulator: `http://10.0.2.2:8000`

You can override that with:

```bash
EXPO_PUBLIC_API_BASE_URL=http://YOUR_HOST:8000 npm start
```