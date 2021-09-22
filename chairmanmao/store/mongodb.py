from __future__ import annotations
import typing as t
import pymongo
from datetime import datetime, timezone

from .types import Profile, Role, Json, UserId
from .document_store import DocumentStore


SCHEMA_VERSION = 5


class MongoDbDocumentStore(DocumentStore):
    def __init__(self, mongo_url: str, mongo_db: str) -> None:
        self.mongo_client = pymongo.MongoClient(mongo_url)
        self.db = self.mongo_client[mongo_db]
        self.profiles = self.db['Profiles']

    def create_profile(self, user_id: UserId, discord_username: str) -> Profile:
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
        assert len(list(self.profiles.find({'user_id': user_id}))) == 0
        self.profiles.insert_one(profile_to_json(profile))
        return profile

    def load_profile(self, user_id: UserId) -> Profile:
        profile_json = self.profiles.find_one({'user_id': user_id})
        return profile_from_json(profile_json)

    def store_profile(self, profile: Profile) -> None:
        query = {'user_id': profile.user_id}
        self.profiles.replace_one(query, profile_to_json(profile))

    def get_all_profiles(self) -> t.List[Profile]:
        return [profile_from_json(p) for p in self.profiles.find({})]


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
