from __future__ import annotations
import typing as t
from pymongo.database import Database
from datetime import datetime, timezone

from chairmanmao.types import Profile, Role, UserId, Json

SCHEMA_VERSION = 5


def create_profile(db: Database, user_id: UserId, discord_username: str) -> Profile:
    assert discord_username[-5] == '#'
    now = datetime.now(timezone.utc).replace(microsecond=0)
    display_name = discord_username[:-5]
    profile = Profile(
        discord_username=discord_username,
        user_id=user_id,
        created=now,
        last_seen=now,
        display_name=display_name,
        credit=1000,
        roles=[Role.Comrade],
        yuan=0,
        hanzi=[],
        mined_words=[],
    )
    assert len(list(db['Profiles'].find({'user_id': user_id}))) == 0
    db['Profiles'].insert_one(profile_to_json(profile))
    return profile


def profile_exists(db: Database, user_id: UserId) -> bool:
    return len(list(db['Profiles'].find({'user_id': user_id}))) > 0


def get_profile(db: Database, user_id: UserId) -> Profile:
    profile_json = db['Profiles'].find_one({'user_id': user_id})
    return profile_from_json(profile_json)


def set_profile(db: Database, user_id: UserId, profile: Profile) -> None:
    query = {'user_id': user_id}
    db['Profiles'].replace_one(query, profile_to_json(profile))


def get_all_profiles(db: Database) -> t.List[Profile]:
    return [profile_from_json(p) for p in db['Profiles'].find({})]


def set_profile_last_seen(db: Database, user_id: UserId) -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    with open_profile(db, user_id) as profile:
        profile.last_seen = now


def profile_to_json(profile: Profile) -> Json:
    roles = [role.value for role in profile.roles]
    return {
        'user_id': profile.user_id,
        'discord_username': profile.discord_username,
        'created': profile.created,
        'last_seen': profile.last_seen,
        'roles': roles,
        'display_name': profile.display_name,
        'credit': profile.credit,
        'yuan': profile.yuan,
        'hanzi': [],
        'mined_words': profile.mined_words,
        'schema_version': SCHEMA_VERSION,
    }


def profile_from_json(profile_json: Json) -> Profile:
    assert profile_json['schema_version'] == SCHEMA_VERSION, f'schema_version of {profile_json} is not {SCHEMA_VERSION}'
    roles = [Role.from_str(role) for role in profile_json['roles']]
    return Profile(
        user_id=profile_json['user_id'],
        discord_username=profile_json['discord_username'],
        created=profile_json['created'],
        last_seen=profile_json['last_seen'],
        roles=roles,
        display_name=profile_json['display_name'],
        credit=profile_json['credit'],
        hanzi=profile_json['hanzi'],
        mined_words=profile_json['mined_words'],
        yuan=profile_json['yuan'],
    )


class open_profile:
    def __init__(self, db, user_id: UserId) -> None:
        self.db = db
        self.user_id = user_id
        self.profile: t.Optional[Profile] = None

    def __enter__(self) -> Profile:
        profile = get_profile(self.db, self.user_id)
        assert profile is not None, f"No profile exists for {self.user_id}"
        self.profile = profile
        return self.profile

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        assert self.profile is not None
        set_profile(self.db, self.user_id, self.profile)


def get_user_id(db: Database, discord_username: str) -> UserId:
    profile_json = db['Profiles'].find_one({'discord_username': discord_username})
    return t.cast(UserId, profile_json['user_id'])
