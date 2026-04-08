# Zomato AI — Next.js frontend (Phase 4)

This app lives **inside Phase 4** next to the Python API: `zomato_recommendation/phase4/web/`. It implements the marketing-style UI (hero, search card, filters, **Personalized Picks**) and calls the **Python JSON API** in the parent package (`zomato_recommendation.phase4`).

## Prerequisites

- **Python API** on `http://127.0.0.1:8000` (from repo root):

  ```bash
  python -m zomato_recommendation.phase4
  ```

- **Groq** API key in `.env` at repo root for live LLM responses.

## Setup

From **this directory** (`phase4/web/`):

```bash
npm install
```

Copy `.env.local.example` to `.env.local` if you need a non-default backend URL.

## Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Paths `/api/v1/*` and `/health` are **rewritten** to the Python backend (`next.config.mjs`), so the browser does not need a separate CORS setup for local development.

## Production build

```bash
npm run build
npm start
```

Set `BACKEND_URL` to your deployed API host when building.

## Assets

- `public/hero-bg.png` — hero background (from repo `design/Screenshot 2026-04-05 145536.png`). Replace to change the hero look.
