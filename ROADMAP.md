# Roadmap

## Current State

SparkTrack is a local-first Windows desktop application for personal intelligence. It stores the core ontology locally in SQLite and exposes a dark PySide6 desktop interface centered on Now, Focus, Workspaces, capture, activity, and supporting management views.

The architecture now has a service layer for attention, today context, workspace scope, feed narration, momentum, neglect, progress, capture, search, and relationships.

## Known Problems

- Some screens still reflect the database structure too directly.
- Path and Field remain schema primitives, but Workspace should increasingly be the user's primary mental model.
- Resources are weakly connected to workspace context because the schema has no direct resource-to-field or resource-to-quest ownership.
- There is no dedicated event log; life feed is reconstructed from entity tables.
- Quest updates are inferred from quest creation and activity rather than tracked as first-class state transitions.
- No updated_at columns, so some recency calculations depend on bursts, artifacts, and created_at.
- The app has future AI seams but no local LLM implementation.

## Next Priorities

- Make TodayContext the main data contract for Now and Focus UI.
- Replace table-shaped UI dependencies with AttentionSummary and LifeFeedItem contracts.
- Add an activity event log for explicit quest updates and state transitions.
- Make workspace persistence richer while avoiding premature schema expansion.
- Improve resource contextualization through relationships.
- Add tests around attention scoring, dormant quest detection, feed ordering, and workspace scoping.

## Future Vision

SparkTrack should become a local personal intelligence operating environment: it should retrieve the right context, surface neglected commitments, reveal momentum, and help the user decide what deserves attention today.

Future versions should support local LLM analysis, semantic search, encrypted local storage, backup, sync, and an Android companion while keeping the user's life data local-first and inspectable.
