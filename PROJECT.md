# PROJECT.md — SparkTrack Constitution

**Version:** 1.0 (Living Document)  
**Status:** Draft — Single Source of Truth  
**Last Updated:** 2026-06-27  
**Purpose:** Any AI (Grok, Codex, Claude, Gemini, etc.) or developer reading only this file should fully understand the vision, philosophy, architecture, entities, rules, and priorities of SparkTrack.

## 1. Executive Summary
SparkTrack is a **Personal Intelligence Operating System (PIOS)** — not a todo app, note-taking app, second brain, or project manager.

It serves as the operating layer between **Knowledge**, **Productivity**, **Skills**, **Reflection**, **Philosophy**, and **Life Evolution**. Its goal is to support personal growth over **30–50 years** by connecting actions, understanding, patterns, and insights while keeping the user firmly in control.

## 2. Core Philosophy
**SparkTrack is NOT:**
- A todo / habit / streak app
- A general note-taking or knowledge management app (Obsidian/Notion clone)
- A traditional project manager

**SparkTrack IS:**
- A personal evolution system focused on long-term growth.
- Local-first, user-owned, explainable, and AI-assisted (never AI-controlled).

**Core Design Principles:**
- **Local-First Forever** — Works offline. User owns data. No cloud dependency by default.
- **Desktop-First** — Windows desktop is primary/master platform. Android as companion.
- **Experience-First** — Build UI/UX before database implementation. CRUD hidden in Forge.
- **AI as Assistant** — Suggests, explains, never silently edits or deletes.
- **Explainable & Overrideable** — Every AI action must show evidence and allow manual override.
- **Two Interconnected Worlds** — Productivity (actions) + Knowledge (understanding).
- **Long-term Focus** — Reduce cognitive load, increase understanding, support life evolution.

## 3. Mental Model & Hierarchies

### Productivity World (Actions)
```
Season → Path → Field → Project → Burst
```

- **Season**: Large life period (e.g., University, Startup Phase, Recovery).
- **Path**: Life dimension/role (Builder, Warrior, Philosopher, Creator, etc.). Each Path has its own dashboard/widgets/analytics/AI/graph.
- **Field**: Specific domain (Programming, Muay Boran, Philosophy, etc.).
- **Project**: Concrete objective with start/complete dates.
- **Burst**: Smallest atomic work unit (timed or logged activity). Produces Artifacts.

### Knowledge World (Understanding)
```
Artifact → Method → Resource → Relationship → Atlas
```

- **Artifact**: Permanent output (Idea, Reflection, Code, Drawing, PDF, etc.).
- **Method**: Reusable "how" (Pomodoro, Feynman, Cornell Notes, Muay Thai techniques, etc.). Highly connected and AI-searchable.
- **Resource**: Inputs (Books, Videos, Courses, Mentors, etc.).
- **Relationship**: First-class citizens. AI suggests connections.
- **Atlas**: Living, zoomable knowledge universe (constellation/graph view, not just a page).
- **Codex**: Permanent knowledge library/vault.
- **Competency**: Evidence-based capability tracking (inferred from Bursts, Artifacts, etc. — no manual XP).

These two worlds constantly interact.

## 4. Major Pages & Their Single Job
- **Homepage** — "What matters now?" (dynamic focus, momentum, insights, neglected areas).
- **Competency** — Track real growth in capabilities.
- **Codex** — Permanent knowledge library.
- **Atlas** — Visual living knowledge universe (zoomable graph).
- **Methods** — Discover, evolve, and apply reusable approaches.
- **Forge** — Hidden developer tools (entity editor, DB viewer, migrations, AI logs, etc.).

**UI Philosophy:** Dense, alive, animated, keyboard-first, inspired by Assassin's Creed Valhalla, Obsidian, Linear, Arc Browser, Cursor, Spotify. Custom drag-drop dashboards per Path.

**Mobile:** Dial interface, fast capture, path switching.

## 5. AI Layer & Rules
- **Primary:** Local (Ollama). Manual bridge for others (ChatGPT/Claude exports).
- **Responsibilities:** Summaries, suggestions, linking, competency estimation, gap detection, resource intelligence, relationship intelligence.
- **AI MUST:**
  - Always explain with evidence + confidence.
  - Cite sources.
  - Allow rejection/override.
- **AI MUST NEVER:**
  - Edit/delete data silently.
  - Hallucinate relationships.
  - Own or control the system.

## 6. Architecture & Development Rules
- Local-first (SQLite/Room + SQLCipher initially).
- Experience-first development.
- All raw operations in Forge.
- Homepage highest priority.
- Every feature evaluated against: Reduces cognitive load? Increases understanding? Supports long-term growth?

## 7. Future Directions
Voice/OCR, advanced AI agents, local embeddings + GraphRAG, plugins, cross-platform, encrypted backups, time machine, etc.

---

**Changelog for this Document** (append-only):
- 2026-06-27: Initial v1.0 drafted from vision synthesis.

**All future changes** to SparkTrack (features, architecture, UI, entities) **must update this file first** (and `CHANGELOG.md`).