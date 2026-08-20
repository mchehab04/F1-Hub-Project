# F1Hub frontend

Next.js app consuming [`docs/api-contract.md`](../docs/api-contract.md) via the typed client in [`lib/api.ts`](lib/api.ts).

## Setup

```
cd frontend
npm install
cp .env.local.example .env.local
```

## Run

```
npm run dev
```

Runs at http://localhost:3000, expects the backend at http://localhost:8000 (see `NEXT_PUBLIC_API_BASE_URL` in `.env.local`).

## Structure

- `app/` — Next.js App Router pages
- `lib/api.ts` — typed fetch client with one function + response type per contract endpoint; import from here rather than calling `fetch` directly, so the contract stays the single source of truth
