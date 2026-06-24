# SparkTrack Core

SparkTrack is a local-first Windows desktop application for personal intelligence.

It is not a productivity tracker, web app, mobile app, or cloud service. It is a PySide6 desktop operating environment for learning, creating, reflecting, and building across many domains of life.

## Project Philosophy

SparkTrack's direction is attention-first:

- Surface what matters today.
- Recover context when returning to a life domain.
- Show momentum and neglect.
- Capture bursts, artifacts, resources, and reflections locally.
- Keep raw database management as infrastructure, not the main experience.

The storage ontology still matters, but the user experience should increasingly speak in Workspaces, Today Context, Attention, Focus, and Life Feed.

## Screenshots

Screenshots will be added as the V1.8 interface stabilizes.

- Now view placeholder
- Workspace view placeholder
- Focus view placeholder
- Life feed placeholder

## Requirements

- Python 3.12+
- Windows 10/11 recommended
- PySide6
- SQLAlchemy
- SQLite

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

By default, SparkTrack stores its SQLite database at:

`%LOCALAPPDATA%\SparkTrack\sparktrack.db`

To override the database path:

```powershell
$env:SPARKTRACK_DB_PATH = "C:\path\to\sparktrack.db"
python main.py
```

## Development

Run a syntax check:

```powershell
python -m compileall sparktrack_core
```

Keep these out of Git:

- `.venv/`
- `__pycache__/`
- `*.pyc`
- `*.db`
- `*.sqlite`
- generated datasets
- local settings

## Architecture

Important documents:

- `ARCHITECTURE.md`
- `ARCHITECT_REVIEW_V1_8.md`
- `ROADMAP.md`
- `CHANGELOG.md`
- `SPARKTRACK_SYSTEM_CONTEXT.md`

Core services introduced or formalized in V1.8:

- `AttentionEngine`
- `TodayService`
- `UnifiedFeedService` with `LifeFeedItem`
- `WorkspaceService` with `WorkspaceProfile`

## Version History

- V1.0: Desktop, local database, ontology, CRUD foundation.
- V1.5: Service layer and richer operational views.
- V1.6: Momentum, neglect, progress, and focus signals.
- V1.7: Workspace OS direction, Now and contextual navigation.
- V1.8: Git foundation and architectural refocus toward attention, context, focus, and retrieval.
