# SparkTrack System Context

Future AI sessions should read this file first.

## Vision

SparkTrack is a local-first Personal Intelligence Operating System for a polymath. It is not a task manager, notes app, dashboard toy, cloud app, Streamlit project, or mobile app. It is a Windows desktop application built with Python, PySide6, SQLite, and SQLAlchemy.

The product goal is to help a person learn, create, evolve, reflect, and build across many domains of life. The experience should move toward attention, context, focus, and retrieval instead of tables, forms, CRUD, and entity management.

## Ontology

Storage ontology:

`Path -> Field -> Quest -> Burst`

Supporting entities:

- Artifact: Reflection, Idea, Principle, Quote, Lesson, Research Note, Observation, Story Fragment, Character Sketch, Concept.
- Resource: Book, Course, Video, Article, Paper.
- Season: bounded life period or strategic cycle.
- Principle: active personal belief or rule.
- Relationship: generic graph edge for future intelligence.

Experience ontology:

- Workspace: primary operating environment.
- TodayContext: single source of truth for what matters today.
- AttentionSummary: momentum, dormancy, neglected fields, and recent activity.
- LifeFeedItem: unified human-readable activity item.

## Design Decisions

- Local-first only. No cloud dependency.
- SQLite database lives under `%LOCALAPPDATA%\SparkTrack\sparktrack.db` unless `SPARKTRACK_DB_PATH` is set.
- PySide6 is the desktop UI layer.
- SQLAlchemy ORM owns persistence.
- Path and Field remain schema infrastructure, but Workspace should be the user-facing abstraction.
- CRUD and dashboard views are maintenance infrastructure, not the future product center.
- Relationship edges are polymorphic to support future graph intelligence.
- Future AI should analyze local data through service contracts, not direct UI scraping.
- V1.8 added `AttentionEngine`, `TodayService`, typed `LifeFeedItem`, and `WorkspaceProfile`.

## Key Files

- `sparktrack_core/models/entities.py`: SQLAlchemy ontology.
- `sparktrack_core/services/workspace_service.py`: workspace scopes and profiles.
- `sparktrack_core/services/attention_engine.py`: recently active quests, dormant quests, active fields, neglected fields, recent bursts, recent artifacts.
- `sparktrack_core/services/today_service.py`: TodayContext.
- `sparktrack_core/services/unified_feed_service.py`: LifeFeedItem stream across bursts, artifacts, resources, quest updates.
- `sparktrack_core/services/now_service.py`: adapter for current Now UI.
- `ARCHITECTURE.md`: current architectural explanation.
- `ARCHITECT_REVIEW_V1_8.md`: V1.8 diagnosis.
- `ROADMAP.md`: next direction.

## Rejected Ideas

- Do not make SparkTrack a web app.
- Do not add more dashboards just to show more data.
- Do not add more CRUD screens as the main path forward.
- Do not add new entities before improving attention/context architecture.
- Do not implement cloud sync or AI in V1.8.
- Do not treat Workspace as mere branding for Path or Field.

## Open Questions

- Should Workspace become a persisted database entity later, or remain a settings-backed operating scope?
- Should Burst eventually allow nullable `quest_id` for frictionless capture?
- Should Resources be attached to quests/fields through explicit ownership or relationship edges?
- Should an activity event log become the canonical Life Feed source?
- How should local LLM analysis consume TodayContext and LifeFeedItem safely?

## V1.9 Direction

Make TodayContext the primary UI data contract. Introduce tests for attention scoring and feed ordering. Add an explicit activity/event log before adding more UI. Continue moving database tables behind command palette or developer flows.
