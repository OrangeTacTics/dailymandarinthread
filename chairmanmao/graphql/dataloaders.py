import typing as t
from datetime import datetime

from strawberry.dataloader import DataLoader

import chairmanmao.graphql.schema as schema
from chairmanmao.store import DocumentStore
import chairmanmao.store.types as types


async def load_profiles(store: DocumentStore, user_ids: t.List[str]) -> t.List[schema.Profile]:
    results = []
    for user_id in user_ids:
        profile = store.load_profile(int(user_id))
        results.append(store_profile_to_graphql_profile(profile))

    return results


async def load_profiles_by_discord_usernames(store: DocumentStore, discord_usernames: t.List[str]) -> t.List[schema.Profile]:
    results = []
    for discord_username in discord_usernames:
        profile = store.load_profile_by_discord_username(discord_username)
        results.append(store_profile_to_graphql_profile(profile))
    return results


def store_profile_to_graphql_profile(profile: types.Profile) -> schema.Profile:
    roles = []
    for store_role in profile.roles:
        schema_role = store_role_to_graphql_role(store_role)
        if schema_role is not None:
            roles.append(schema_role)

    hsk = calc_hsk_level(profile)
    hsk_role = types.Role.__members__.get(f'Hsk{hsk}')
    if hsk_role is not None:
        roles.append(hsk_role)

    return schema.Profile(
        user_id=str(profile.user_id),
        discord_username=profile.discord_username,
        display_name=profile.display_name,
        credit=profile.credit,
        hanzi=profile.hanzi,
        mined_words=profile.mined_words,
        roles=roles,
        created=profile.created,
        last_seen=profile.last_seen,
        yuan=profile.yuan,
        hsk=hsk,
    )


def calc_hsk_level(profile: types.Profile) -> t.Optional[int]:
    if types.Role.Hsk6 in profile.roles:
        return 6
    if types.Role.Hsk5 in profile.roles:
        return 5
    if types.Role.Hsk4 in profile.roles:
        return 4
    if types.Role.Hsk3 in profile.roles:
        return 3
    if types.Role.Hsk2 in profile.roles:
        return 2
    if types.Role.Hsk1 in profile.roles:
        return 1
    return None


def store_role_to_graphql_role(role: types.Role) -> t.Optional[schema.Role]:
    if role == types.Role.Party:
        return schema.Role.Party
    if role == types.Role.Learner:
        return schema.Role.Learner
    if role == types.Role.Jailed:
        return schema.Role.Jailed
    return None
