"""
URL patterns for the campaign_manager app.

These are included from questlog/urls.py, so the paths here are relative
to the root of the site (no prefix is added).

URL naming conventions used here:
  - Named URLs (name='...') let templates use {% url 'name' %} instead of
    hardcoding paths. This means URL changes only need to happen in one place.
"""

from django.urls import path
from . import views

urlpatterns = [

    # ── Dashboard ──────────────────────────────────────────────────
    path('', views.dashboard, name='dashboard'),


    # ── Campaigns ──────────────────────────────────────────────────
    # List all campaigns:         GET  /campaigns/
    path('campaigns/', views.campaign_list, name='campaign_list'),

    # Create a new campaign:      GET/POST  /campaigns/create/
    path('campaigns/create/', views.campaign_create, name='campaign_create'),

    # View a campaign's details:  GET  /campaigns/5/
    path('campaigns/<int:pk>/', views.campaign_detail, name='campaign_detail'),

    # Edit a campaign:            GET/POST  /campaigns/5/edit/
    path('campaigns/<int:pk>/edit/', views.campaign_edit, name='campaign_edit'),

    # Join a campaign:            POST  /campaigns/5/join/
    path('campaigns/<int:pk>/join/', views.campaign_join, name='campaign_join'),


    # ── Sessions (nested under campaign) ───────────────────────────
    # Log a new session:          GET/POST  /campaigns/5/sessions/create/
    path(
        'campaigns/<int:campaign_pk>/sessions/create/',
        views.session_create,
        name='session_create',
    ),

    # View session details:       GET  /sessions/3/
    path('sessions/<int:pk>/', views.session_detail, name='session_detail'),


    # ── Encounters (nested under session) ──────────────────────────
    # Add an encounter:           GET/POST  /sessions/3/encounters/create/
    path(
        'sessions/<int:session_pk>/encounters/create/',
        views.encounter_create,
        name='encounter_create',
    ),


    # ── Characters (nested under campaign) ─────────────────────────
    # Create a character:         GET/POST  /campaigns/5/characters/create/
    path(
        'campaigns/<int:campaign_pk>/characters/create/',
        views.character_create,
        name='character_create',
    ),

    # View character details:     GET  /characters/7/
    path('characters/<int:pk>/', views.character_detail, name='character_detail'),

    # Edit a character:           GET/POST  /characters/7/edit/
    path('characters/<int:pk>/edit/', views.character_edit, name='character_edit'),


    # ── Inventory ──────────────────────────────────────────────────
    # Add item to character:      GET/POST  /characters/7/inventory/add/
    path(
        'characters/<int:character_pk>/inventory/add/',
        views.add_item_to_character,
        name='add_item_to_character',
    ),
]
