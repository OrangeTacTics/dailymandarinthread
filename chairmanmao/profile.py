from __future__ import annotations
import typing as t
from pymongo.database import Database
from datetime import datetime

from chairmanmao.types import Profile, Role

SCHEMA_VERSION = 4

Json = t.Any


def assert_username(username: str) -> None:
    assert username[0] != '@'
    assert username[-5] == '#'
    assert all(ch.isnumeric() for ch in username[-4:])


def create_profile(db: Database, username: str) -> Profile:
    assert_username(username)
    now = datetime.now().replace(microsecond=0)
    display_name = username[:-5]
    profile = Profile(
        username=username,
        memberid=None,
        created=now,
        last_message=now,
        display_name=username,
        credit=1000,
        roles=[],
        yuan=0,
        hanzi=[],
        mined_words=[],
    )
    assert len(list(db['Profiles'].find({'username': username}))) == 0
    db['Profiles'].insert_one(profile_to_json(profile))
    return profile


def get_profile(db: Database, username: str) -> t.Optional[Profile]:
    assert_username(username)
    profile_json = db['Profiles'].find_one({'username': username})
    if profile_json is not None:
        return profile_from_json(profile_json)
    else:
        return create_profile(db, username)


def set_profile(db: Database, username: str, profile: Profile) -> None:
    assert_username(username)
    query = { 'username': username }
    db['Profiles'].replace_one(query, profile_to_json(profile))


def get_all_profiles(db: Database) -> t.List[Profile]:
    return [profile_from_json(p) for p in db['Profiles'].find({})]


def set_profile_last_message(db: Database, username: str) -> None:
    now = datetime.now().replace(microsecond=0)

    profile = get_profile(db, username)
    assert profile is not None
    profile.last_message = now
    set_profile(db, username, profile)


def profile_to_json(profile: Profile) -> Json:
    roles = [role.value for role in profile.roles]
    return {
        'username': profile.username,
        'memberid': profile.memberid,
        'created': profile.created,
        'last_message': profile.last_message,
        'roles': roles,
        'display_name': profile.display_name,
        'credit': profile.credit,
        'yuan': profile.yuan,
        'hanzi': profile.hanzi,
        'mined_words': profile.mined_words,
        'schema_version': SCHEMA_VERSION,
    }


def profile_from_json(profile_json: Json) -> Profile:
    assert_username(profile_json['username'])
    assert profile_json['schema_version'] == SCHEMA_VERSION, f'schema_version of {profile_json} is not {SCHEMA_VERSION}'
    roles = [Role.from_str(role) for role in profile_json['roles']]
    return Profile(
        username=profile_json['username'],
        memberid=profile_json['memberid'],
        created=profile_json['created'],
        last_message=profile_json['last_message'],
        roles=roles,
        display_name=profile_json['display_name'],
        credit=profile_json['credit'],
        hanzi=profile_json['hanzi'],
        mined_words=profile_json['mined_words'],
        yuan=profile_json['yuan'],
    )
