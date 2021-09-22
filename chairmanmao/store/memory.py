from __future__ import annotations
import typing as t
from pathlib import Path
import json

from .types import Profile, Role, Json, UserId
from .document_store import DocumentStore


SCHEMA_VERSION = 5


class MemoryDocumentStore(DocumentStore):
    def __init__(self) -> None:
        self.profiles: t.Dict[UserId, Profile] = {}

    def create_profile(self, user_id: UserId, discord_username: str) -> Profile:
        assert not self.profile_exists(user_id)
        profile = Profile.make(user_id, discord_username)
        self.profiles[profile.user_id] = profile
        return profile

    def profile_exists(self, user_id: UserId) -> bool:
        return user_id in self.profiles

    def load_profile(self, user_id: UserId) -> Profile:
        return self.profiles[user_id]

    def store_profile(self, profile: Profile) -> None:
        self.profiles[profile.user_id] = profile

    def get_all_profiles(self) -> t.List[Profile]:
        return list(self.profiles.values())

    def load(self, filepath: Path) -> None:
        self.profiles = {}
        with open(filepath, 'r') as infile:
            profiles = json.load(infile)

        for profile in profiles:
            self.profiles[profile['user_id']] = profile_from_json(profile)

    def save(self, filepath: Path) -> None:
        with open(filepath, 'w') as outfile:
            profiles = [profile_to_json(p) for p in self.profiles.values()]
            json.dump(profiles, outfile, indent=4, ensure_ascii=False)


def profile_to_json(profile: Profile) -> Json:
    roles = [role.value for role in profile.roles]
    return {
        'user_id': profile.user_id,
        'discord_username': profile.discord_username,
        'created': datetime_to_json(profile.created),
        'last_seen': datetime_to_json(profile.last_seen),
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
        created=datetime_from_json(profile_json['created']),
        last_seen=datetime_from_json(profile_json['last_seen']),
        roles=roles,
        display_name=profile_json['display_name'],
        credit=profile_json['credit'],
        hanzi=profile_json['hanzi'],
        mined_words=profile_json['mined_words'],
        yuan=profile_json['yuan'],
    )


def datetime_from_json(json_datetime: str) -> datetime:
    dt = datetime.fromisoformat(json_datetime)
    return dt


def datetime_to_json(dt: datetime) -> str:
    return dt.isoformat()
