# SparkTrack Architecture

## Core Ontology

SparkTrack's storage ontology is:

`Path -> Field -> Quest -> Burst`

Supporting entities:

- Artifact: reflections, ideas, principles, quotes, lessons, observations, story fragments, and concepts.
- Resource: books, courses, videos, articles, and papers.
- Season: bounded life period or strategic cycle.
- Principle: active personal rule or operating belief.
- Relationship: polymorphic graph edge for future intelligence.

V1.8's experience ontology is different:

- Workspace: the user's operating environment.
- Attention: what needs care, momentum, or retrieval.
- TodayContext: what matters now.
- LifeFeedItem: what happened recently in human terms.

Path and Field remain important infrastructure, but they should not dominate the main experience.

## Database Structure

SQLite is the local database. SQLAlchemy ORM models live in `sparktrack_core/models/entities.py`.

The database is initialized locally and migration support is kept lightweight in `sparktrack_core/database/migrations.py`. Database files, generated datasets, and local settings are excluded from Git.

The Relationship table is intentionally generic so future graph intelligence can connect artifacts, quests, fields, paths, seasons, resources, and principles without repeated schema churn.

## Major Services

- `WorkspaceService`: resolves operating scopes and decides whether domain items belong to a workspace.
- `AttentionEngine`: calculates recently active quests, dormant quests, active and neglected fields, recent bursts, and recent artifacts.
- `TodayService`: produces `TodayContext`, the future heart of Now/Focus workflows.
- `UnifiedFeedService`: produces common `LifeFeedItem` records across bursts, artifacts, resources, and quest updates.
- `NowService`: adapts focus, feed, progress, and today context for current UI.
- `FocusService`, `MomentumService`, `NeglectService`, and `ProgressService`: domain signals for action and reflection.
- `ContextResolver`: turns selected IDs into human labels.
- `CaptureService`: records new bursts/artifacts and connects them to context.

## UI Architecture

The app is PySide6 desktop software, not a web app. The UI uses a dark theme, main window shell, contextual sidebar, command palette, workspace selector, status bar, and dense information views.

V1.8 intentionally avoids adding more visible dashboards or CRUD pages. New architecture is service-first so future UI can consume stable domain objects instead of raw ORM rows.

## Current Design Philosophy

SparkTrack should feel like an operating environment, not an admin panel. Entity tables are infrastructure. The visible experience should answer:

- What matters today?
- What has momentum?
- What has gone dormant?
- What context am I operating inside?
- What has happened recently?
- What should be retrieved when I return to a path of life?

The app remains local-first, fast, inspectable, keyboard-friendly, and prepared for future local AI without requiring cloud services.
