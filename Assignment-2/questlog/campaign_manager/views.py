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

from .models import (
    Campaign,
    CampaignPlayer,
    Character,
    Session,
    Encounter,
    Item,
    CharacterItem,
    NPC,
    Quest,
    QuestObjective,
    SessionQuest,
)
from .forms import (
    RegistrationForm,
    CampaignForm,
    CharacterForm,
    SessionForm,
    NPCForm,
    QuestForm,
    QuestObjectiveForm,
    EncounterForm,
    SessionQuestForm,
    ItemForm,
    AddExistingItemForm,
)


def _is_campaign_member(campaign, user):
    return CampaignPlayer.objects.filter(campaign=campaign, user=user).exists()


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

    active_quests = Quest.objects.filter(
        campaign__in=campaign_ids,
        status__in=['not_started', 'active'],
    ).select_related('campaign', 'given_by').order_by('campaign__name', 'name')[:6]

    recent_quest_progress = SessionQuest.objects.filter(
        session__campaign__in=campaign_ids
    ).select_related('session', 'session__campaign', 'quest').order_by('-session__date')[:5]

    return render(request, 'campaign_manager/dashboard.html', {
        'campaigns':       campaigns,
        'characters':      characters,
        'recent_sessions': recent_sessions,
        'active_quests': active_quests,
        'recent_quest_progress': recent_quest_progress,
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
    npcs        = NPC.objects.filter(campaign=campaign).order_by('name')
    quests      = Quest.objects.filter(campaign=campaign).select_related('given_by').order_by('name')

    # Context flags for the template to decide what buttons to show
    is_member = CampaignPlayer.objects.filter(campaign=campaign, user=request.user).exists()
    is_dm     = campaign.dungeon_master == request.user

    return render(request, 'campaign_manager/campaign_detail.html', {
        'campaign':    campaign,
        'memberships': memberships,
        'characters':  characters,
        'sessions':    sessions,
        'npcs':        npcs,
        'quests':      quests,
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
@login_required
def npc_create(request, campaign_pk):
    """Creates a new NPC under a campaign. Only the DM can do this."""
    campaign = get_object_or_404(Campaign, pk=campaign_pk)

    if campaign.dungeon_master != request.user:
        messages.error(request, "Only the Dungeon Master can add NPCs.")
        return redirect('campaign_detail', pk=campaign_pk)

    if request.method == 'POST':
        form = NPCForm(request.POST)
        if form.is_valid():
            npc = form.save(commit=False)
            npc.campaign = campaign
            npc.save()
            messages.success(request, f'NPC "{npc.name}" added to {campaign.name}.')
            return redirect('campaign_detail', pk=campaign_pk)
    else:
        form = NPCForm()

    return render(request, 'campaign_manager/npc_form.html', {
        'form': form,
        'campaign': campaign,
        'title': f'New NPC - {campaign.name}',
    })


@login_required
def quest_create(request, campaign_pk):
    """Creates a new quest under a campaign. Only the DM can do this."""
    campaign = get_object_or_404(Campaign, pk=campaign_pk)

    if campaign.dungeon_master != request.user:
        messages.error(request, "Only the Dungeon Master can create quests.")
        return redirect('campaign_detail', pk=campaign_pk)

    if request.method == 'POST':
        form = QuestForm(request.POST, campaign=campaign)
        if form.is_valid():
            quest = form.save(commit=False)
            quest.campaign = campaign
            quest.save()
            messages.success(request, f'Quest "{quest.name}" has been created.')
            return redirect('quest_detail', pk=quest.pk)
    else:
        form = QuestForm(campaign=campaign)

    return render(request, 'campaign_manager/quest_form.html', {
        'form': form,
        'campaign': campaign,
        'title': f'New Quest - {campaign.name}',
    })


@login_required
def quest_detail(request, pk):
    """Shows a quest, its objectives, and the sessions where it progressed."""
    quest = get_object_or_404(Quest.objects.select_related('campaign', 'given_by'), pk=pk)
    objectives = QuestObjective.objects.filter(quest=quest).order_by('id')
    session_logs = SessionQuest.objects.filter(quest=quest).select_related(
        'session', 'session__campaign'
    ).order_by('session__date', 'session__session_number')
    is_member = _is_campaign_member(quest.campaign, request.user)
    is_dm = quest.campaign.dungeon_master == request.user
    completed_objectives = objectives.filter(is_completed=True).count()

    return render(request, 'campaign_manager/quest_detail.html', {
        'quest': quest,
        'objectives': objectives,
        'session_logs': session_logs,
        'is_member': is_member,
        'is_dm': is_dm,
        'completed_objectives': completed_objectives,
    })


@login_required
def quest_edit(request, pk):
    """Edits an existing quest. Only the DM can do this."""
    quest = get_object_or_404(Quest.objects.select_related('campaign'), pk=pk)

    if quest.campaign.dungeon_master != request.user:
        messages.error(request, "Only the Dungeon Master can edit quests.")
        return redirect('quest_detail', pk=pk)

    if request.method == 'POST':
        form = QuestForm(request.POST, instance=quest, campaign=quest.campaign)
        if form.is_valid():
            form.save()
            messages.success(request, f'Quest "{quest.name}" has been updated.')
            return redirect('quest_detail', pk=pk)
    else:
        form = QuestForm(instance=quest, campaign=quest.campaign)

    return render(request, 'campaign_manager/quest_form.html', {
        'form': form,
        'campaign': quest.campaign,
        'quest': quest,
        'title': f'Edit Quest - {quest.name}',
    })


@login_required
def objective_create(request, quest_pk):
    """Adds a quest objective. Only the DM can do this."""
    quest = get_object_or_404(Quest.objects.select_related('campaign'), pk=quest_pk)

    if quest.campaign.dungeon_master != request.user:
        messages.error(request, "Only the Dungeon Master can add objectives.")
        return redirect('quest_detail', pk=quest_pk)

    if request.method == 'POST':
        form = QuestObjectiveForm(request.POST)
        if form.is_valid():
            objective = form.save(commit=False)
            objective.quest = quest
            objective.save()
            messages.success(request, "Objective added.")
            return redirect('quest_detail', pk=quest_pk)
    else:
        form = QuestObjectiveForm()

    return render(request, 'campaign_manager/objective_form.html', {
        'form': form,
        'quest': quest,
        'title': f'Add Objective - {quest.name}',
    })


@login_required
def objective_toggle(request, pk):
    """Toggles the completion state of a quest objective. Only the DM can do this."""
    objective = get_object_or_404(QuestObjective.objects.select_related('quest', 'quest__campaign'), pk=pk)

    if objective.quest.campaign.dungeon_master != request.user:
        messages.error(request, "Only the Dungeon Master can update objectives.")
        return redirect('quest_detail', pk=objective.quest.pk)

    if request.method == 'POST':
        objective.is_completed = not objective.is_completed
        objective.save()
        messages.success(request, "Objective status updated.")

    return redirect('quest_detail', pk=objective.quest.pk)


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
    session_quests = SessionQuest.objects.filter(session=session).select_related('quest').order_by('quest__name')
    is_dm      = session.campaign.dungeon_master == request.user

    return render(request, 'campaign_manager/session_detail.html', {
        'session':    session,
        'encounters': encounters,
        'session_quests': session_quests,
        'is_dm':      is_dm,
    })


# ─────────────────────────────────────────────────────────────────────
@login_required
def session_quest_create(request, session_pk):
    """Logs quest progress for a session. Only the DM can do this."""
    session = get_object_or_404(Session.objects.select_related('campaign'), pk=session_pk)

    if session.campaign.dungeon_master != request.user:
        messages.error(request, "Only the Dungeon Master can add quest progress.")
        return redirect('session_detail', pk=session_pk)

    if request.method == 'POST':
        form = SessionQuestForm(request.POST, session=session)
        if form.is_valid():
            quest = form.cleaned_data['quest']
            if SessionQuest.objects.filter(session=session, quest=quest).exists():
                form.add_error('quest', 'That quest already has progress logged for this session.')
            else:
                session_quest = form.save(commit=False)
                session_quest.session = session
                session_quest.save()
                messages.success(request, f'Quest progress for "{quest.name}" has been recorded.')
                return redirect('session_detail', pk=session_pk)
    else:
        form = SessionQuestForm(session=session)

    return render(request, 'campaign_manager/session_quest_form.html', {
        'form': form,
        'session': session,
        'title': f'Add Quest Progress - Session #{session.session_number}',
    })


@login_required
def session_quest_edit(request, pk):
    """Edits quest progress notes for a session. Only the DM can do this."""
    session_quest = get_object_or_404(
        SessionQuest.objects.select_related('session', 'session__campaign', 'quest'),
        pk=pk,
    )

    if session_quest.session.campaign.dungeon_master != request.user:
        messages.error(request, "Only the Dungeon Master can edit quest progress.")
        return redirect('session_detail', pk=session_quest.session.pk)

    if request.method == 'POST':
        form = SessionQuestForm(
            request.POST,
            instance=session_quest,
            session=session_quest.session,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Quest progress updated.")
            return redirect('session_detail', pk=session_quest.session.pk)
    else:
        form = SessionQuestForm(instance=session_quest, session=session_quest.session)

    return render(request, 'campaign_manager/session_quest_form.html', {
        'form': form,
        'session': session_quest.session,
        'session_quest': session_quest,
        'title': f'Edit Quest Progress - Session #{session_quest.session.session_number}',
    })


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
