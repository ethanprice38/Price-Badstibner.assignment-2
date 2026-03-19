# Assignment 2: QuestLog — Tabletop RPG Campaign Manager

We are providing you with a Django starter application for managing tabletop RPG campaigns. You can find more details in the `questlog` directory, along with the quick start
instructions (in `README.md`).

This assignment can be done by yourself or in a group.

## Your Tasks (READ CAREFULLY)

1. Recreate the E/R diagram for this application (see `models.py` file).

1. Extend this application in some non-trivial manner. You should add at least 2-3 new entities and 4-5 new relationships, and have additional functionality beyond what's
currently supported. 

1. The final E/R diagram for your extended application should be uploaded at the end.

1. This is an open-ended assignment -- we are not asking you to do anything specific. However, there is a list of ideas below that you can use or get inspiration from.

1. You are free to change the look and feel of this application. 

1. You are free to use any coding assistants; make sure to disclose at the end. More importantly, you need to ensure that you understand all the code that you have added.

1. It is expected that the changes you make are commensurate with how much you use the coding assistants; however, we will not enforce this.

1. There will an in-person interview where you will be asked to explain your design decisions, and the code. A large part of the grade will be based on this interview.

1. You will submit your modified code, modified E/R diagram, as well as a short video.

## Prompt to help understand code

The file `questlog/Prompt.md` contains a prompt that you can feed into a chatbot, to help you better understand the codebase. The codebase is relatively simple but, as noted above, you are expected to sufficiently understand the codebase to be able to answer questions about it.

## Suggestions

1. **Spell & Ability Tracking** — Characters in RPGs have spells and special abilities tied to their class and level. You could add a system where characters have a repertoire of spells or abilities, each with properties like level requirement, damage/effect description, and usage limits. Characters would be able to "prepare" a subset of their known spells for a given session, introducing a relationship that varies per session rather than being static.

1. **Quest Journal** — Campaigns typically have multiple quests running simultaneously — a main storyline plus side quests. You could add quests with objectives, status tracking (active, completed, failed), rewards, and connections to the sessions where quest progress actually happened. A quest might span many sessions and a single session might advance multiple quests, creating an interesting many-to-many relationship.

1. **NPC & Faction Registry** — The DM populates the world with non-player characters who belong to factions (the Thieves' Guild, the Town Guard, the Goblin Tribe). You could add NPCs with faction memberships, track which encounters NPCs appeared in, and record a party's reputation score with each faction that changes over time based on their actions.

1. **Character Progression Log** — Right now a character just has a level number. You could add a system that tracks how characters grow over time — recording when a character leveled up, which session it happened in, what stat changes occurred, and how much experience was earned per session. This turns a single integer field into a temporal history, requiring you to think about how to model change over time.

1. **Crafting & Item Relationships** — In many RPGs, items can be combined or transformed. A blacksmith might forge a magic sword from shimmer ore, a steel ingot, and a fire gem. You could add crafting recipes that define which items are consumed to produce a new item, along with skill requirements and success conditions. This introduces a self-referential relationship where items relate to other items through recipes.

1. **AI Dungeon Master Assistant** — Integrate an LLM API call (could be Claude's API) so the DM can generate encounter descriptions, NPC dialogue, or session recap summaries from rough notes. You would need to store prompt templates, generation history tied to campaigns/sessions, and possibly a rating system where the DM marks generated content as used/rejected. This touches on storing API interactions as data and linking generated content back to the entities it references.

1. **In-Game Economy with a Marketplace** — Characters can list items for trade with other characters, set prices, make offers, and complete transactions. The app tracks listings, bids, transaction history, and character gold balances. You could even add an auction mechanic with expiration times. This is essentially building a small exchange system with temporal state — items change ownership, gold changes hands, and the full ledger is queryable.

1. **Token-Based Reward System** — The DM awards tokens (think of them as a custom campaign currency) for good roleplaying, clever solutions, or showing up consistently. Players can spend tokens on in-game perks like re-rolling a failed check, introducing a plot element, or resurrecting a dead character. This requires tracking token issuance, balances, redemption history, and a catalog of purchasable perks — essentially a simple ledger/wallet system.

1. **Character Relationship Graph** — Track relationships *between* characters (and NPCs) — allies, rivals, mentors, siblings, romantic interests, debts owed. Each relationship has a type, a sentiment score that can shift after key encounters, and a history of events that changed it. This is a self-referential many-to-many on the character table with temporal attributes, which is a genuinely interesting data modeling challenge.

1. **Procedural Loot Generation** — Instead of the DM manually creating every item, build a system that randomly generates loot based on configurable rules — encounter difficulty determines rarity probabilities, item type pools are defined per setting, and magical properties are pulled from a modifiers table and combined. You need to model the generation rules, modifier tables, and the relationship between templates and concrete generated items. It's a rules engine stored in the database.
