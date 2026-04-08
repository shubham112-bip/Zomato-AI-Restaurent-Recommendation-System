# Zomato AI — Next.js frontend

Marketing-style UI aligned with the design mock: hero with food imagery, search card, quick tags, filters, and a **Personalized Picks** grid. It calls the same FastAPI backend as `zomato_recommendation.phase4`.

## Prerequisites

- **Backend** running on `http://127.0.0.1:8000` (from repo root):

  ```bash
  python -m zomato_recommendation.phase4
  ```

- **Groq** API key in `.env` at repo root for live LLM responses.

## Setup

```bash
cd web
npm install
```

Copy `.env.local.example` to `.env.local` if you need a non-default backend URL.

## Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). API calls to `/api/v1/*` and `/health` are **rewritten** to the backend (see `next.config.mjs`), so you do not need CORS on FastAPI for this setup.

## Production build

```bash
npm run build
npm start
```

Set `BACKEND_URL` to your deployed API host when building.

## Assets

- `public/hero-bg.png` — hero background (from `design/Screenshot 2026-04-05 145536.png`). Replace to change the hero look.
