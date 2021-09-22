from __future__ import annotations
import typing as t
from datetime import datetime

import pymongo

from .types import Profile, Role, Json, UserId, ServerSettings
from .document_store import DocumentStore


SCHEMA_VERSION = 5


class MongoDbDocumentStore(DocumentStore):
    def __init__(self, mongo_url: str, mongo_db: str) -> None:
        self.mongo_client = pymongo.MongoClient(mongo_url)
        self.db = self.mongo_client[mongo_db]
        self.profiles = self.db['Profiles']
        self.server_settings = self.db['ServerSettings']

    def create_profile(self, user_id: UserId, discord_username: str) -> Profile:
        profile = Profile.make(user_id, discord_username)

        assert not self.profile_exists(user_id)
        self.profiles.insert_one(profile_to_json(profile))
        return profile

    def profile_exists(self, user_id: UserId) -> bool:
        return len(list(self.profiles.find({'user_id': user_id}))) > 0

    def load_profile(self, user_id: UserId) -> Profile:
        profile_json = self.profiles.find_one({'user_id': user_id})
        return profile_from_json(profile_json)

    def store_profile(self, profile: Profile) -> None:
        query = {'user_id': profile.user_id}
        self.profiles.replace_one(query, profile_to_json(profile))

    def get_all_profiles(self) -> t.List[Profile]:
        return [profile_from_json(p) for p in self.profiles.find({})]

    def load_server_settings(self) -> ServerSettings:
        json_data = self.profiles.find_one({})
        return ServerSettings(
            last_bump=datetime.fromisoformat(json_data['last_bump'])
        )

    def store_server_settings(self, server_settings: ServerSettings) -> None:
        doc = {
            'last_bump': server_settings.last_bump.isoformat(),
        }
        self.server_settings.replace_one({}, doc)


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
