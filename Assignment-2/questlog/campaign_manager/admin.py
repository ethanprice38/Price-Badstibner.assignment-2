"""
Admin configuration for QuestLog models.

Registering models here makes them manageable via Django's built-in admin
interface at /admin/. This is extremely useful for:
  - Browsing and editing data during development
  - Debugging — see exactly what's in the database
  - Creating test data without writing code

To access /admin/, you need a superuser account:
    python manage.py createsuperuser
    (or use the 'admin' account created by the seed command)
"""

from django.contrib import admin
from .models import Campaign, CampaignPlayer, Character, Session, Encounter, Item, CharacterItem


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    # Columns shown in the list view
    list_display  = ['name', 'dungeon_master', 'status', 'world_name', 'created_at']
    list_filter   = ['status']
    search_fields = ['name', 'dungeon_master__username', 'world_name']


@admin.register(CampaignPlayer)
class CampaignPlayerAdmin(admin.ModelAdmin):
    list_display  = ['user', 'campaign', 'role', 'joined_at']
    list_filter   = ['role']
    search_fields = ['user__username', 'campaign__name']


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display  = ['name', 'campaign', 'player', 'race', 'character_class', 'level', 'hit_points']
    list_filter   = ['race', 'character_class', 'campaign']
    search_fields = ['name', 'player__username']


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display  = ['session_number', 'campaign', 'date', 'duration_hours']
    list_filter   = ['campaign']
    ordering      = ['campaign', 'session_number']


@admin.register(Encounter)
class EncounterAdmin(admin.ModelAdmin):
    list_display  = ['name', 'session', 'difficulty', 'outcome']
    list_filter   = ['difficulty', 'outcome']
    search_fields = ['name']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display  = ['name', 'item_type', 'rarity', 'weight', 'value_gold']
    list_filter   = ['item_type', 'rarity']
    search_fields = ['name']


@admin.register(CharacterItem)
class CharacterItemAdmin(admin.ModelAdmin):
    list_display  = ['character', 'item', 'quantity', 'equipped']
    list_filter   = ['equipped']
    search_fields = ['character__name', 'item__name']
