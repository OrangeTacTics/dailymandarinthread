import typing as t

import os

from dotenv import load_dotenv

from chairmanmao.types import Profile, Role
from chairmanmao.profile import get_profile, get_user_id


load_dotenv()

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')


def db_from_info(info):
    request = info.context['request']
    return request.state.db


def username_from_info(info) -> t.Optional[str]:
    request = info.context['request']
    if request.state.token is not None:
        username = request.state.token['username']
        return username
    else:
        return None


def profile_from_info(info) -> t.Optional[Profile]:
    db = db_from_info(info)
    username = username_from_info(info)
    if username is not None:
        user_id = get_user_id(db, username)
        profile = get_profile(db, user_id)
        return profile
    else:
        return None


def assert_admin(info):
    assert username_from_info(info) == ADMIN_USERNAME


def profile_role_to_graphql_role(role: Role) -> t.Optional[str]:
    role_map = {
        Role.Comrade: "Comrade",
        Role.Party: "Party",
        Role.Learner: "Learner",
        Role.Jailed: "Jailed",
    }

    return role_map.get(role)


def profile_to_graphql(profile: Profile) -> t.Dict:
    graphql_roles = []
    for profile_role in profile.roles:
        graphql_role = profile_role_to_graphql_role(profile_role)
        if graphql_role is not None:
            graphql_roles.append(graphql_role)

    return {
        'user_id': str(profile.user_id),
        'username': profile.discord_username,
        'display_name': profile.display_name,
        'credit': profile.credit,
        'hanzi': profile.hanzi,
        'mined_words': profile.mined_words,
        'roles': graphql_roles,
        'created': profile.created,
        # 'last_seen': profile.last_seen,
        'yuan': profile.yuan,
    }
