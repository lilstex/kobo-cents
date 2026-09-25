# Kobo & Cents frontend

Next.js (App Router) frontend for Kobo & Cents, a Nigerian (NGX) and
US stock research platform. Public landing page and glossary first,
the authenticated app after, per the build order in
`docs/frontend-architecture/07-phases.md`.

Full architecture and reasoning: `docs/frontend-architecture/` at the
repo root (`00.md` stack, `01.md` the Terminal Precision design
system, `02.md` logo and icon system, `03-landing-page.md` through
`06-design.md` the actual pages and screens, `07-phases.md` the build
roadmap this code is being built from).

## Stack

Next.js, TypeScript, Tailwind CSS, TanStack Query, React Hook Form +
Zod, Lucide icons, TradingView Lightweight Charts. Reasoning for each
in `docs/frontend-architecture/00.md`.

## Local development

```bash
cp .env.example .env.local   # fill in real values, never commit .env.local
npm install
npm run dev
```

Serves at `http://localhost:3000`.

## Brand assets

`image-assets/` holds every logo, favicon, PWA icon, and wordmark
export the design docs call for, already generated, labeled in
`image-assets/README.md`.

## Linting

```bash
npm run lint:oxlint
```
