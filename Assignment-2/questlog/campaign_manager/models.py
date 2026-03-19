"""
Models for the QuestLog campaign manager.

Each class here maps to a table in the SQLite database.
After changing this file, run:
    python manage.py makemigrations
    python manage.py migrate

Key relationships:
    Campaign  ←── CampaignPlayer ──→ User   (many-to-many with role + join date)
    Campaign  ──→ Character       ──→ User   (character belongs to campaign & player)
    Campaign  ──→ Session         ──→ Encounter
    Character ←── CharacterItem   ──→ Item   (many-to-many with quantity + equipped)
"""

from django.db import models
from django.contrib.auth.models import User


# ─────────────────────────────────────────────────────────────────────
# Campaign
# ─────────────────────────────────────────────────────────────────────

class Campaign(models.Model):
    """
    A tabletop RPG campaign. One user acts as the Dungeon Master (DM) and
    owns the campaign. Other users can join as players via CampaignPlayer.
    """

    STATUS_CHOICES = [
        ('active',    'Active'),
        ('completed', 'Completed'),
        ('on_hold',   'On Hold'),
    ]

    name        = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    world_name  = models.CharField(
        max_length=200, blank=True,
        help_text="The name of the setting or fictional world (e.g. Faerûn, Barovia)"
    )
    created_at  = models.DateTimeField(auto_now_add=True)  # Set automatically on creation
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # The user who created and runs this campaign as Dungeon Master.
    # on_delete=CASCADE means if the DM's account is deleted, the campaign is too.
    dungeon_master = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='campaigns_as_dm',
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']  # Newest campaigns first


# ─────────────────────────────────────────────────────────────────────
# CampaignPlayer  (join table: Campaign ↔ User)
# ─────────────────────────────────────────────────────────────────────

class CampaignPlayer(models.Model):
    """
    Represents a user's membership in a campaign.

    This is a JOIN TABLE with extra attributes:
      - role:      is the user a Player or the Dungeon Master?
      - joined_at: when did they join?

    Because we need these extra columns, we model this as an explicit table
    rather than using Django's automatic ManyToManyField (which would give
    us a plain join table with no extra columns).

    The unique_together constraint ensures one user can only have one
    membership record per campaign.
    """

    ROLE_CHOICES = [
        ('player', 'Player'),
        ('dm',     'Dungeon Master'),
    ]

    campaign  = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='memberships')
    user      = models.ForeignKey(User,     on_delete=models.CASCADE, related_name='campaign_memberships')
    role      = models.CharField(max_length=20, choices=ROLE_CHOICES, default='player')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('campaign', 'user')  # One membership per user per campaign

    def __str__(self):
        return f"{self.user.username} in '{self.campaign.name}' ({self.get_role_display()})"


# ─────────────────────────────────────────────────────────────────────
# Character
# ─────────────────────────────────────────────────────────────────────

class Character(models.Model):
    """
    A player character that exists within a specific campaign.
    Each character belongs to exactly one campaign and is controlled by one user.
    """

    RACE_CHOICES = [
        ('human',      'Human'),
        ('elf',        'Elf'),
        ('dwarf',      'Dwarf'),
        ('halfling',   'Halfling'),
        ('gnome',      'Gnome'),
        ('half_elf',   'Half-Elf'),
        ('half_orc',   'Half-Orc'),
        ('tiefling',   'Tiefling'),
        ('dragonborn', 'Dragonborn'),
        ('other',      'Other'),
    ]

    CLASS_CHOICES = [
        ('barbarian', 'Barbarian'),
        ('bard',      'Bard'),
        ('cleric',    'Cleric'),
        ('druid',     'Druid'),
        ('fighter',   'Fighter'),
        ('monk',      'Monk'),
        ('paladin',   'Paladin'),
        ('ranger',    'Ranger'),
        ('rogue',     'Rogue'),
        ('sorcerer',  'Sorcerer'),
        ('warlock',   'Warlock'),
        ('wizard',    'Wizard'),
    ]

    name             = models.CharField(max_length=200)
    race             = models.CharField(max_length=20, choices=RACE_CHOICES, default='human')
    character_class  = models.CharField(max_length=20, choices=CLASS_CHOICES, default='fighter')
    level            = models.IntegerField(default=1)
    hit_points       = models.IntegerField(default=10)
    background_story = models.TextField(blank=True, help_text="Optional backstory for this character")

    # Which campaign this character exists in
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='characters')

    # Which user controls this character
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='characters')

    def __str__(self):
        return (
            f"{self.name} "
            f"(Lvl {self.level} {self.get_race_display()} {self.get_character_class_display()})"
        )

    class Meta:
        ordering = ['name']


# ─────────────────────────────────────────────────────────────────────
# Item
# ─────────────────────────────────────────────────────────────────────

class Item(models.Model):
    """
    A game item that can exist in any character's inventory.

    Items are not tied to a specific character here — the relationship
    between characters and items is tracked by CharacterItem below.
    """

    TYPE_CHOICES = [
        ('weapon', 'Weapon'),
        ('armor',  'Armor'),
        ('potion', 'Potion'),
        ('quest',  'Quest Item'),
        ('misc',   'Misc'),
    ]

    RARITY_CHOICES = [
        ('common',    'Common'),
        ('uncommon',  'Uncommon'),
        ('rare',      'Rare'),
        ('very_rare', 'Very Rare'),
        ('legendary', 'Legendary'),
    ]

    name        = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    item_type   = models.CharField(max_length=20, choices=TYPE_CHOICES, default='misc')
    rarity      = models.CharField(max_length=20, choices=RARITY_CHOICES, default='common')
    weight      = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    value_gold  = models.IntegerField(default=0, help_text="Value in gold pieces (gp)")

    def __str__(self):
        return f"{self.name} ({self.get_rarity_display()} {self.get_item_type_display()})"

    class Meta:
        ordering = ['name']


# ─────────────────────────────────────────────────────────────────────
# CharacterItem  (join table: Character ↔ Item)
# ─────────────────────────────────────────────────────────────────────

class CharacterItem(models.Model):
    """
    Represents an item in a character's inventory.

    This is a JOIN TABLE with extra attributes:
      - quantity: how many of this item the character carries
      - equipped: whether the item is currently worn/held

    We define this as an explicit model (NOT using Django's ManyToManyField
    shortcut) so you can see it as a real database table with its own rows
    and columns. Every row says: "Character X has Y of Item Z, equipped=True/False."

    The unique_together constraint means a character can only have one
    inventory slot per item — to add more, increase the quantity.
    """

    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='inventory')
    item      = models.ForeignKey(Item,      on_delete=models.CASCADE, related_name='character_inventories')
    quantity  = models.IntegerField(default=1)
    equipped  = models.BooleanField(default=False)

    class Meta:
        unique_together = ('character', 'item')  # One inventory row per character-item pair

    def __str__(self):
        equipped_label = ' [equipped]' if self.equipped else ''
        return f"{self.character.name} — {self.item.name} ×{self.quantity}{equipped_label}"


# ─────────────────────────────────────────────────────────────────────
# Session
# ─────────────────────────────────────────────────────────────────────

class Session(models.Model):
    """
    A single play session within a campaign.
    The DM typically logs sessions after (or before) they happen.
    Sessions are numbered sequentially within each campaign.
    """

    session_number = models.IntegerField(
        help_text="Which session this is in the campaign (1, 2, 3, …)"
    )
    date           = models.DateField()
    duration_hours = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True,
        help_text="How long the session ran, in hours (e.g., 3.5)"
    )
    summary  = models.TextField(blank=True, help_text="Recap notes for this session")

    # Which campaign this session belongs to
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='sessions')

    def __str__(self):
        return f"Session {self.session_number} — {self.campaign.name} ({self.date})"

    class Meta:
        ordering            = ['campaign', 'session_number']
        unique_together     = ('campaign', 'session_number')  # No duplicate session numbers per campaign


# ─────────────────────────────────────────────────────────────────────
# Encounter
# ─────────────────────────────────────────────────────────────────────

class Encounter(models.Model):
    """
    A single encounter within a session — a battle, puzzle, social interaction, etc.
    Encounters have a difficulty rating and an optional outcome.
    A null outcome means the encounter is still unresolved.
    """

    DIFFICULTY_CHOICES = [
        ('easy',   'Easy'),
        ('medium', 'Medium'),
        ('hard',   'Hard'),
        ('deadly', 'Deadly'),
    ]

    OUTCOME_CHOICES = [
        ('victory',    'Victory'),
        ('defeat',     'Defeat'),
        ('fled',       'Fled'),
        ('negotiated', 'Negotiated'),
    ]

    name        = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    difficulty  = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium')

    # outcome is nullable — null means the encounter hasn't been resolved yet
    outcome = models.CharField(
        max_length=20, choices=OUTCOME_CHOICES,
        null=True, blank=True,
        help_text="Leave blank if the encounter is still unresolved"
    )

    # Which session this encounter took place in
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='encounters')

    def __str__(self):
        return f"{self.name} ({self.get_difficulty_display()})"

    class Meta:
        ordering = ['session', 'id']
