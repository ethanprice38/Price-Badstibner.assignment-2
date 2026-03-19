# QuestLog — Tabletop RPG Campaign Manager

A Django starter application for managing tabletop RPG campaigns, characters,
sessions, and encounters. Built for CMSC424 (Database Design) as a learning
reference for Django and relational databases.

---

## Quick Start

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install Django
pip install -r requirements.txt

# 3. Create the database tables
python manage.py migrate

# 4. Populate with sample data
python manage.py seed

# 5. Start the development server
python manage.py runserver
```

Then open **http://127.0.0.1:8000/** in your browser.

---

## Seed Accounts

The `seed` command creates the following accounts:

| Username         | Password      | Role                        |
|------------------|---------------|-----------------------------|
| `dungeon_master` | `password123` | DM for both seed campaigns  |
| `player_one`     | `password123` | Player (Thorin & Viktor)    |
| `player_two`     | `password123` | Player (Aria & Sylva)       |
| `admin`          | `admin123`    | Django admin superuser      |

Admin panel: **http://127.0.0.1:8000/admin/**

---

## Project Structure

```
questlog/
├── manage.py               # Django management script
├── requirements.txt
├── questlog/               # Project settings
│   ├── settings.py
│   └── urls.py
└── campaign_manager/       # Main application
    ├── models.py           # Database models (entities + join tables)
    ├── views.py            # Request handlers
    ├── forms.py            # Django forms
    ├── urls.py             # URL routing
    ├── admin.py            # Admin panel configuration
    ├── management/
    │   └── commands/
    │       └── seed.py     # `python manage.py seed`
    ├── templates/
    │   ├── registration/   # Login & register pages
    │   └── campaign_manager/
    │       └── *.html
    └── static/
        └── campaign_manager/
            └── style.css
```

---

## Key Models and Relationships

```
User ──< CampaignPlayer >── Campaign   (join table with role + join date)
Campaign ──< Character >── User        (character belongs to campaign & player)
Campaign ──< Session ──< Encounter
Character ──< CharacterItem >── Item   (join table with quantity + equipped)
```

`CampaignPlayer` and `CharacterItem` are the two join tables you should study —
both have extra attributes beyond the two foreign keys.

---

## After Making Model Changes

```bash
python manage.py makemigrations   # Generate a migration file
python manage.py migrate          # Apply the migration to the database
```
