"""
Views for the QuestLog campaign manager.

Each view function:
  1. Receives an HttpRequest object
  2. Does some work (reads from DB, processes a form, checks permissions)
  3. Returns an HttpResponse — either rendered HTML or a redirect

The @login_required decorator redirects unauthenticated users to the login page
(defined by LOGIN_URL in settings.py).
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Campaign, CampaignPlayer, Character, Session, Encounter, Item, CharacterItem
from .forms import (
    RegistrationForm,
    CampaignForm,
    CharacterForm,
    SessionForm,
    EncounterForm,
    ItemForm,
    AddExistingItemForm,
)


# ─────────────────────────────────────────────────────────────────────
# Authentication
# ─────────────────────────────────────────────────────────────────────

def register_view(request):
    """
    Registration page. Anyone (logged in or not) can visit, but if you're
    already logged in we redirect you to the dashboard.
    After a successful registration, the user is automatically logged in.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the new user in immediately so they don't have to sign in again
            login(request, user)
            messages.success(request, f"Welcome to QuestLog, {user.username}! Your account has been created.")
            return redirect('dashboard')
    else:
        form = RegistrationForm()

    return render(request, 'registration/register.html', {'form': form})


# ─────────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    """
    The home page for logged-in users.
    Shows campaigns they're in, characters they play, and recent sessions.
    """
    # Find all campaigns the current user is a member of
    memberships = CampaignPlayer.objects.filter(
        user=request.user
    ).select_related('campaign', 'campaign__dungeon_master')

    campaigns = [m.campaign for m in memberships]

    # All characters belonging to this user, across all campaigns
    characters = Character.objects.filter(
        player=request.user
    ).select_related('campaign')

    # Recent sessions from campaigns the user is part of
    campaign_ids = [c.id for c in campaigns]
    recent_sessions = Session.objects.filter(
        campaign__in=campaign_ids
    ).select_related('campaign').order_by('-date')[:5]

    return render(request, 'campaign_manager/dashboard.html', {
        'campaigns':       campaigns,
        'characters':      characters,
        'recent_sessions': recent_sessions,
    })


# ─────────────────────────────────────────────────────────────────────
# Campaign views
# ─────────────────────────────────────────────────────────────────────

@login_required
def campaign_list(request):
    """
    Lists all campaigns in the system.
    Supports filtering by status via ?status=active (or completed, on_hold).
    Also passes a set of campaign IDs the current user belongs to,
    so the template can show 'View' vs 'Join' buttons.
    """
    campaigns = Campaign.objects.all().select_related('dungeon_master')

    # Optional status filter from the query string (?status=active)
    status_filter = request.GET.get('status', '')
    if status_filter:
        campaigns = campaigns.filter(status=status_filter)

    # Build a set of campaign IDs this user is already a member of
    user_campaign_ids = set(
        CampaignPlayer.objects.filter(user=request.user).values_list('campaign_id', flat=True)
    )

    return render(request, 'campaign_manager/campaign_list.html', {
        'campaigns':        campaigns,
        'status_filter':    status_filter,
        'status_choices':   Campaign.STATUS_CHOICES,
        'user_campaign_ids': user_campaign_ids,
    })


@login_required
def campaign_detail(request, pk):
    """
    Shows full details for a single campaign:
    - Campaign info
    - Member list (from CampaignPlayer)
    - Characters in this campaign
    - Sessions (ordered chronologically)
    """
    campaign   = get_object_or_404(Campaign, pk=pk)
    memberships = CampaignPlayer.objects.filter(campaign=campaign).select_related('user')
    characters  = Character.objects.filter(campaign=campaign).select_related('player')
    sessions    = Session.objects.filter(campaign=campaign).order_by('session_number')

    # Context flags for the template to decide what buttons to show
    is_member = CampaignPlayer.objects.filter(campaign=campaign, user=request.user).exists()
    is_dm     = campaign.dungeon_master == request.user

    return render(request, 'campaign_manager/campaign_detail.html', {
        'campaign':    campaign,
        'memberships': memberships,
        'characters':  characters,
        'sessions':    sessions,
        'is_member':   is_member,
        'is_dm':       is_dm,
    })


@login_required
def campaign_create(request):
    """
    Creates a new campaign. The logged-in user is automatically set as the DM.
    After creation, the DM is also added to CampaignPlayer with role='dm'
    so they appear in the member list.
    """
    if request.method == 'POST':
        form = CampaignForm(request.POST)
        if form.is_valid():
            # commit=False gives us an unsaved Campaign object so we can
            # set dungeon_master before writing to the database
            campaign = form.save(commit=False)
            campaign.dungeon_master = request.user
            campaign.save()

            # Add the creator to the membership table as DM
            CampaignPlayer.objects.create(
                campaign=campaign,
                user=request.user,
                role='dm',
            )

            messages.success(request, f'Campaign "{campaign.name}" has been created!')
            return redirect('campaign_detail', pk=campaign.pk)
    else:
        form = CampaignForm()

    return render(request, 'campaign_manager/campaign_form.html', {
        'form':  form,
        'title': 'Create New Campaign',
    })


@login_required
def campaign_edit(request, pk):
    """
    Edits an existing campaign. Only the DM can do this.
    """
    campaign = get_object_or_404(Campaign, pk=pk)

    if campaign.dungeon_master != request.user:
        messages.error(request, "Only the Dungeon Master can edit this campaign.")
        return redirect('campaign_detail', pk=pk)

    if request.method == 'POST':
        # Pass instance=campaign to update the existing record instead of creating a new one
        form = CampaignForm(request.POST, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, f'Campaign "{campaign.name}" has been updated.')
            return redirect('campaign_detail', pk=pk)
    else:
        form = CampaignForm(instance=campaign)

    return render(request, 'campaign_manager/campaign_form.html', {
        'form':     form,
        'title':    f'Edit: {campaign.name}',
        'campaign': campaign,
    })


@login_required
def campaign_join(request, pk):
    """
    Lets a user join a campaign as a player.
    Only accepts POST requests (joining is a state-changing action).
    If the user is already a member, show a warning instead.
    """
    campaign = get_object_or_404(Campaign, pk=pk)

    if request.method == 'POST':
        already_member = CampaignPlayer.objects.filter(
            campaign=campaign, user=request.user
        ).exists()

        if already_member:
            messages.warning(request, "You are already a member of this campaign.")
        else:
            CampaignPlayer.objects.create(
                campaign=campaign,
                user=request.user,
                role='player',
            )
            messages.success(request, f'You have joined "{campaign.name}"!')

    return redirect('campaign_detail', pk=pk)


# ─────────────────────────────────────────────────────────────────────
# Character views
# ─────────────────────────────────────────────────────────────────────

@login_required
def character_create(request, campaign_pk):
    """
    Creates a new character in the specified campaign.
    The logged-in user must already be a member of the campaign.
    """
    campaign = get_object_or_404(Campaign, pk=campaign_pk)

    # Only members can create characters in a campaign
    is_member = CampaignPlayer.objects.filter(
        campaign=campaign, user=request.user
    ).exists()
    if not is_member:
        messages.error(request, "You must join this campaign before creating a character.")
        return redirect('campaign_detail', pk=campaign_pk)

    if request.method == 'POST':
        form = CharacterForm(request.POST)
        if form.is_valid():
            character = form.save(commit=False)
            character.campaign = campaign   # Attach to this campaign
            character.player   = request.user  # Owned by the current user
            character.save()
            messages.success(request, f'Character "{character.name}" has been created!')
            return redirect('character_detail', pk=character.pk)
    else:
        form = CharacterForm()

    return render(request, 'campaign_manager/character_form.html', {
        'form':     form,
        'campaign': campaign,
        'title':    f'New Character — {campaign.name}',
    })


@login_required
def character_detail(request, pk):
    """
    Shows a character's stats and their full inventory (items via CharacterItem).
    """
    character = get_object_or_404(Character, pk=pk)

    # Fetch the character's inventory. select_related('item') avoids N+1 queries
    # by loading item data in the same database query as the CharacterItem rows.
    inventory = CharacterItem.objects.filter(
        character=character
    ).select_related('item').order_by('item__name')

    is_owner = character.player == request.user
    is_dm    = character.campaign.dungeon_master == request.user

    return render(request, 'campaign_manager/character_detail.html', {
        'character': character,
        'inventory': inventory,
        'is_owner':  is_owner,
        'is_dm':     is_dm,
    })


@login_required
def character_edit(request, pk):
    """
    Edits a character's stats. Only the character's player or the campaign DM can do this.
    """
    character = get_object_or_404(Character, pk=pk)

    # Permission check
    if character.player != request.user and character.campaign.dungeon_master != request.user:
        messages.error(request, "You can only edit your own characters.")
        return redirect('character_detail', pk=pk)

    if request.method == 'POST':
        form = CharacterForm(request.POST, instance=character)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{character.name}" has been updated.')
            return redirect('character_detail', pk=pk)
    else:
        form = CharacterForm(instance=character)

    return render(request, 'campaign_manager/character_form.html', {
        'form':      form,
        'title':     f'Edit: {character.name}',
        'character': character,
    })


# ─────────────────────────────────────────────────────────────────────
# Session views
# ─────────────────────────────────────────────────────────────────────

@login_required
def session_create(request, campaign_pk):
    """
    Logs a new session for a campaign. Only the DM can do this.
    Pre-fills the session_number field with the next sequential number.
    """
    campaign = get_object_or_404(Campaign, pk=campaign_pk)

    if campaign.dungeon_master != request.user:
        messages.error(request, "Only the Dungeon Master can log sessions.")
        return redirect('campaign_detail', pk=campaign_pk)

    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            # Check for duplicate session number before saving
            session_number = form.cleaned_data['session_number']
            if Session.objects.filter(campaign=campaign, session_number=session_number).exists():
                form.add_error('session_number', f'Session #{session_number} already exists in this campaign.')
            else:
                session = form.save(commit=False)
                session.campaign = campaign
                session.save()
                messages.success(request, f'Session #{session.session_number} has been logged!')
                return redirect('session_detail', pk=session.pk)
    else:
        # Pre-fill the session number with the next available number
        next_number = Session.objects.filter(campaign=campaign).count() + 1
        form = SessionForm(initial={'session_number': next_number})

    return render(request, 'campaign_manager/session_form.html', {
        'form':     form,
        'campaign': campaign,
        'title':    f'Log New Session — {campaign.name}',
    })


@login_required
def session_detail(request, pk):
    """
    Shows a session's recap notes and all its encounters.
    """
    session    = get_object_or_404(Session, pk=pk)
    encounters = Encounter.objects.filter(session=session)
    is_dm      = session.campaign.dungeon_master == request.user

    return render(request, 'campaign_manager/session_detail.html', {
        'session':    session,
        'encounters': encounters,
        'is_dm':      is_dm,
    })


# ─────────────────────────────────────────────────────────────────────
# Encounter views
# ─────────────────────────────────────────────────────────────────────

@login_required
def encounter_create(request, session_pk):
    """
    Adds an encounter to a session. Only the campaign's DM can do this.
    """
    session = get_object_or_404(Session, pk=session_pk)

    if session.campaign.dungeon_master != request.user:
        messages.error(request, "Only the Dungeon Master can add encounters.")
        return redirect('session_detail', pk=session_pk)

    if request.method == 'POST':
        form = EncounterForm(request.POST)
        if form.is_valid():
            encounter = form.save(commit=False)
            encounter.session = session
            encounter.save()
            messages.success(request, f'Encounter "{encounter.name}" added to Session #{session.session_number}.')
            return redirect('session_detail', pk=session_pk)
    else:
        form = EncounterForm()

    return render(request, 'campaign_manager/encounter_form.html', {
        'form':    form,
        'session': session,
        'title':   f'Add Encounter — Session #{session.session_number}',
    })


# ─────────────────────────────────────────────────────────────────────
# Inventory views
# ─────────────────────────────────────────────────────────────────────

@login_required
def add_item_to_character(request, character_pk):
    """
    Adds an item to a character's inventory via CharacterItem.

    This page has TWO separate forms:
      1. "Add Existing Item" — pick from items already in the database
      2. "Create New Item"  — fill in details to create a brand-new item

    A hidden field named 'form_type' (value: 'existing' or 'new') tells
    the view which form was submitted.

    If the character already has the item, the quantity is increased instead
    of creating a duplicate row.
    """
    character = get_object_or_404(Character, pk=character_pk)

    # Only the character's player or the campaign DM can modify the inventory
    if character.player != request.user and character.campaign.dungeon_master != request.user:
        messages.error(request, "You can only modify your own character's inventory.")
        return redirect('character_detail', pk=character_pk)

    existing_form  = AddExistingItemForm()
    new_item_form  = ItemForm()

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'existing':
            # ── Path 1: User picked an existing item ──
            existing_form = AddExistingItemForm(request.POST)
            if existing_form.is_valid():
                item     = existing_form.cleaned_data['item']
                quantity = existing_form.cleaned_data['quantity']
                equipped = existing_form.cleaned_data['equipped']

                # get_or_create returns (object, created_bool).
                # If the character already has this item, just add to the quantity.
                char_item, created = CharacterItem.objects.get_or_create(
                    character=character,
                    item=item,
                    defaults={'quantity': quantity, 'equipped': equipped},
                )
                if not created:
                    char_item.quantity += quantity
                    char_item.save()

                messages.success(request, f'Added {item.name} to {character.name}\'s inventory.')
                return redirect('character_detail', pk=character_pk)

        elif form_type == 'new':
            # ── Path 2: User is creating a brand-new item ──
            new_item_form = ItemForm(request.POST)
            try:
                quantity = int(request.POST.get('quantity', 1))
            except (ValueError, TypeError):
                quantity = 1
            equipped = request.POST.get('equipped') == 'on'

            if new_item_form.is_valid():
                # Save the new Item to the database first
                item = new_item_form.save()
                # Then create the inventory entry linking character ↔ item
                CharacterItem.objects.create(
                    character=character,
                    item=item,
                    quantity=quantity,
                    equipped=equipped,
                )
                messages.success(request, f'Created "{item.name}" and added it to {character.name}\'s inventory.')
                return redirect('character_detail', pk=character_pk)

    return render(request, 'campaign_manager/add_item.html', {
        'character':     character,
        'existing_form': existing_form,
        'new_item_form': new_item_form,
    })
