# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup (run once)
pip install -r requirements.txt
python manage.py migrate
python manage.py seed

# Development server
python manage.py runserver          # http://127.0.0.1:8000/

# After changing models.py
python manage.py makemigrations
python manage.py migrate

# Django shell (interactive DB access)
python manage.py shell
```

All commands must be run from the `questlog/` directory (where `manage.py` lives).

To run on a non-default port:

```bash
python manage.py runserver 8080
```

## Architecture

Single Django app (`campaign_manager`) inside the `questlog/` project. No REST API — traditional server-rendered views with form POST/redirect patterns.

**Key files:**
- [campaign_manager/models.py](campaign_manager/models.py) — 7 models; all FK relationships defined here
- [campaign_manager/views.py](campaign_manager/views.py) — all view functions (one file, sectioned by entity)
- [campaign_manager/urls.py](campaign_manager/urls.py) — URL patterns with named routes
- [campaign_manager/forms.py](campaign_manager/forms.py) — ModelForms for each entity
- [campaign_manager/admin.py](campaign_manager/admin.py) — all models registered with list_display

**The two explicit join tables** (important for the database course):
- `CampaignPlayer` — Campaign ↔ User, adds `role` and `joined_at`
- `CharacterItem`  — Character ↔ Item, adds `quantity` and `equipped`

## URL naming conventions

All named URLs follow `entity_action` pattern (e.g., `campaign_detail`, `session_create`, `add_item_to_character`). Use `{% url 'name' pk=x %}` in templates.

URL parameters:
- Entity-owning views use `pk` (e.g., `/campaigns/<int:pk>/`)
- Nested creation views use `campaign_pk`, `session_pk`, or `character_pk` as the parent identifier

## Patterns to follow when extending

- Views check membership/DM permissions with direct queryset checks (no decorators beyond `@login_required`)
- `commit=False` pattern on form saves to inject FK values (e.g., `session.campaign = campaign`) before saving
- `get_or_create` in the seed command keeps it idempotent
- Templates extend `campaign_manager/base.html` and fill `{% block content %}`
- Flash messages via `messages.success/error(request, "...")`

## Database

SQLite (`db.sqlite3`) — created automatically by `migrate`. No setup required. Delete `db.sqlite3` and re-run `migrate` + `seed` to reset to a clean state.

## Django template gotcha

Django parses `{% %}` tags even inside HTML comments (`<!-- -->`). Never put real template tags in comments inside `.html` files — use plain descriptive text instead. This caused two bugs in `base.html` during initial setup:
- A `{% block content %}` in a comment was treated as a real block definition (duplicate block error).
- A `{% extends "..." %}` in a comment caused `base.html` to extend itself (recursion error).

## Seed credentials

- `dungeon_master` / `player_one` / `player_two` — password `password123`
- `admin` — password `admin123` (superuser, access `/admin/`)
