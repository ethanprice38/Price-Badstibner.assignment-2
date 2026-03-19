"""
Forms for the QuestLog campaign manager.

Django forms handle two things:
  1. Rendering HTML input fields in templates ({{ form.as_p }})
  2. Validating user-submitted data before saving to the database

ModelForm is the most common form type — it automatically generates fields
from a model's field definitions, so you don't repeat yourself.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Campaign, Character, Session, Encounter, Item, CharacterItem


class RegistrationForm(UserCreationForm):
    """
    Extends Django's built-in UserCreationForm to add an optional email field.
    UserCreationForm already includes: username, password1, password2 (confirm).
    """
    email = forms.EmailField(
        required=False,
        help_text="Optional. Used for account recovery."
    )

    class Meta:
        model  = User
        fields = ['username', 'email', 'password1', 'password2']


class CampaignForm(forms.ModelForm):
    """Form for creating and editing campaigns."""

    class Meta:
        model  = Campaign
        # dungeon_master is set automatically in the view, so we exclude it here
        fields = ['name', 'description', 'world_name', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class CharacterForm(forms.ModelForm):
    """Form for creating and editing a character's stats."""

    class Meta:
        model  = Character
        # campaign and player are set automatically in the view
        fields = ['name', 'race', 'character_class', 'level', 'hit_points', 'background_story']
        widgets = {
            'background_story': forms.Textarea(attrs={'rows': 4}),
        }


class SessionForm(forms.ModelForm):
    """Form for logging a new session under a campaign."""

    class Meta:
        model  = Session
        # campaign is set automatically in the view
        fields = ['session_number', 'date', 'duration_hours', 'summary']
        widgets = {
            # type="date" gives a native date-picker in modern browsers
            'date':    forms.DateInput(attrs={'type': 'date'}),
            'summary': forms.Textarea(attrs={'rows': 5}),
        }


class EncounterForm(forms.ModelForm):
    """Form for adding an encounter to a session."""

    class Meta:
        model  = Encounter
        # session is set automatically in the view
        fields = ['name', 'description', 'difficulty', 'outcome']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ItemForm(forms.ModelForm):
    """Form for creating a brand-new item."""

    class Meta:
        model  = Item
        fields = ['name', 'description', 'item_type', 'rarity', 'weight', 'value_gold']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class AddExistingItemForm(forms.ModelForm):
    """
    Form for adding an already-existing item to a character's inventory.
    The user picks from items already in the database, then sets quantity and equipped.
    """
    item = forms.ModelChoiceField(
        queryset=Item.objects.all().order_by('name'),
        empty_label="— Select an item —",
    )

    class Meta:
        model  = CharacterItem
        # character is set automatically in the view
        fields = ['item', 'quantity', 'equipped']
