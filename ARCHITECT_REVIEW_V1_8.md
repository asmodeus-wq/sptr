# Architect Review V1.8

## What Still Feels Database-First

- The original ontology is mirrored too directly in visible pages and page names.
- Several services still return dictionaries that look like table rows instead of stable domain contracts.
- Recent activity is reconstructed from entity creation records rather than a deliberate activity log.
- Path and Field remain overly visible compared with Workspace, Context, Attention, and Today.
- Resources have no strong contextual ownership, so they float outside the operating environment.
- CRUD screens still exist as convenient maintenance tools, even when they should be secondary or developer-oriented.

## Architectural Causes

- The schema was created before the experience model matured.
- Dashboard and CRUD pages were useful for V1 foundation work, but they trained the app around record management.
- Workspace started as a path/field filter preset instead of a first-class operating abstraction.
- Feed, focus, momentum, and neglect services evolved separately, so the app lacked one central Today contract.
- Relationship edges are powerful but still too invisible to anchor retrieval and context.

## What Should Become Infrastructure

- Path and Field should mostly become classification infrastructure.
- CRUD pages should become maintenance/developer tools.
- Dashboard metrics should become supporting telemetry, not the home experience.
- Database rows should be adapted into domain objects before UI consumption.
- Relationship handling should become retrieval infrastructure.
- Resources should be contextualized through relationships or a future explicit ownership model.

## V1.8 Refocus

V1.8 introduces Attention Engine, Today Service, and Life Feed contracts. These services should become the bridge between the raw ontology and the user's lived experience.

The main architectural move is:

`Database records -> Domain signals -> Today context -> UI`

instead of:

`Database records -> Tables -> Dashboard`

## Risks

- Without tests, attention scoring can drift silently.
- Without an event log, quest updates remain approximate.
- Without a richer workspace model, Workspace may stay a filter with better branding.
- Adding AI too early would amplify weak context rather than solve it.

## Recommendation

V1.9 should make TodayContext the primary UI data contract, reduce direct page dependence on raw service dictionaries, and introduce an explicit activity/event log before adding more features.
