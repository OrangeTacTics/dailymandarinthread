import typing as t
from datetime import datetime
from enum import Enum

import strawberry as s

import server.store.types as types


@s.enum
class Role(Enum):
    Party = "Party"
    Learner = "Learner"
    Jailed = "Jailed"


@s.type
class Profile:
    user_id: str
    discord_username: str
    display_name: str
    credit: int
    hanzi: t.List[str]
    mined_words: t.List[str]
    roles: t.List[Role]
    created: datetime
    last_seen: datetime
    yuan: int
    hsk: t.Optional[int]
    defected: bool


async def get_me(info) -> Profile:
    discord_username = info.context.discord_username
    return await info.context.dataloaders.profile_by_discord_username.load(discord_username)


def add_role(profile: types.Profile, role: types.Role) -> bool:
    """
    Returns whether the profile was changed.
    """
    roles_set = set(profile.roles)
    if role not in roles_set:
        roles_set.add(role)
        profile.roles = sorted(roles_set)
        changed = True
    else:
        changed = False

    return changed


def remove_role(profile: types.Profile, role: types.Role) -> bool:
    """
    Returns whether the profile was changed.
    """
    roles_set = set(profile.roles)
    if role in roles_set:
        roles_set.remove(role)
        profile.roles = sorted(roles_set)
        changed = True
    else:
        changed = False

    return changed


def set_hsk(profile: types.Profile, hsk_level: t.Optional[int]) -> None:
    role_by_level = {
        1: types.Role.Hsk1,
        2: types.Role.Hsk2,
        3: types.Role.Hsk3,
        4: types.Role.Hsk4,
        5: types.Role.Hsk5,
        6: types.Role.Hsk6,
    }

    # Remove all roles
    for role in role_by_level.values():
        remove_role(profile, role)

    if hsk_level is not None:
        # Then add the right one
        role_to_add = role_by_level[hsk_level]
        add_role(profile, role_to_add)
