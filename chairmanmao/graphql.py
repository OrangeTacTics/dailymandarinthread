from __future__ import annotations
import typing as t
import os
from dotenv import load_dotenv
import graphene as g
from graphene import ObjectType, Field, String, Schema, Int

from chairmanmao.profile import create_profile, get_profile, set_profile, profile_from_json, get_all_profiles, get_user_id
from chairmanmao.hanzi import get_seen_hanzi, see_hanzi
import chairmanmao.types as types


load_dotenv()

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')


class Role(g.Enum):
    Comrade = "Comrade"
    PartyMember = "PartyMember"
    Chairman = "Chairman"
    Learner = "Learner"


class Profile(g.ObjectType):
    user_id = g.Int()
    username = g.String()
    display_name = g.String()
    credit = g.Int()
    hanzi = g.List(g.String)
    mined_words = g.List(g.String)
    roles = g.List(Role)
    created = g.String()
    last_message = g.String()
    yuan = g.Int()


def profile_to_graphql(profile: types.Profile) -> Profile:
    roles = [role.value for role in profile.roles]
    return Profile(
        user_id=profile.user_id,
        username=profile.discord_username,
        display_name=profile.display_name,
        credit=profile.credit,
        hanzi=profile.hanzi,
        mined_words=profile.mined_words,
        roles=roles,
        created=profile.created,
        # last_seen=profile.last_seen,
        yuan=profile.yuan,
    )


class CreateProfile(g.Mutation):
    class Arguments:
        username = g.String()

    success = g.Boolean()
    profile = g.Field(Profile)

    def mutate(self, info, username):
        assert_admin(info)
        db = db_from_info(info)
        profile = create_profile(db, username)
        return {
            'success': True,
            'profile': profile_to_graphql(profile),
        }


class IncrementSocialCredit(g.Mutation):
    class Arguments:
        username = g.String()
        amount = g.Int()

    success = g.Boolean()
    old_credit = g.Int()
    new_credit = g.Int()

    def mutate(self, info, username, amount):
        assert_admin(info)
        db = db_from_info(info)
        profile = get_profile(db, username)

        old_credit = profile.credit
        new_credit = old_credit + amount

        profile.credit = new_credit
        set_profile(db, username, profile)

        return {
            'success': True,
            'old_credit': old_credit,
            'new_credit': new_credit,
        }


class AddRole(g.Mutation):
    class Arguments:
        username = g.String()
        role = g.Argument(Role)

    success = g.Boolean()

    def mutate(self, info, username, role):
        assert_admin(info)
        db = db_from_info(info)
        profile = get_profile(db, username)
        old_roles = set(profile.roles)
        new_roles = old_roles.union({types.Role.from_str(role)})

        profile.roles = new_roles
        set_profile(db, username, profile)

        return {
            'success': True,
        }


class RemoveRole(g.Mutation):
    class Arguments:
        username = g.String()
        role = g.Argument(Role)

    success = g.Boolean()

    def mutate(self, info, username, role):
        assert_admin(info)
        db = db_from_info(info)
        profile = get_profile(db, username)
        old_roles = set(profile.roles)
        new_roles = old_roles.difference({types.Role.from_str(role)})

        profile.roles = new_roles
        set_profile(db, username, profile)

        return {
            'success': True,
        }


class SeeHanzi(g.Mutation):
    class Arguments:
        username = g.String()
        hanzi = g.List(g.String)

    success = g.Boolean()

    def mutate(self, info, username, hanzi):
        assert_admin(info)
        db = db_from_info(info)
        see_hanzi(db, username, hanzi)
        return {
            'success': True,
        }


class LeaderboardEntry(g.ObjectType):
    name = g.String()
    credit = g.Int()


class Query(g.ObjectType):
    me = g.Field(Profile)
    leaderboard = g.List(LeaderboardEntry)
    profile = g.Field(Profile, username=g.String())
    all_usernames = g.List(g.String)
    all_hanzi = g.List(g.String)

    def resolve_me(root, info):
        profile = profile_from_info(info)
        if profile is not None:
            return profile_to_graphql(profile)
        return None

    def resolve_leaderboard(root, info):
        db = db_from_info(info)
        entries = []
        profiles = get_all_profiles(db)
        profiles.sort(reverse=True, key=lambda profile: profile.credit)
        for profile in profiles[:10]:
            entries.append(LeaderboardEntry(
                name=profile.display_name,
                credit=profile.credit,
            ))
        return entries

    def resolve_profile(root, info, username):
        assert_admin(info)
        profile = profile_from_info(info)

        db = db_from_info(info)
        profile = get_profile(db, username)

        if profile is not None:
            return profile_to_graphql(profile)
        else:
            return None

    def resolve_all_usernames(root, info):
        assert_admin(info)
        db = db_from_info(info)
        usernames = set()
        for profile in get_all_profiles(db):
            usernames.add(profile.discord_username)
        return sorted(usernames)

    def resolve_all_hanzi(root, info):
        assert_admin(info)
        db = db_from_info(info)
        return get_seen_hanzi(db)


class Mutation(g.ObjectType):
    create_profile = CreateProfile.Field()
    increment_social_credit = IncrementSocialCredit.Field()
    see_hanzi = SeeHanzi.Field()
    add_role = AddRole.Field()
    remove_role = RemoveRole.Field()


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


def profile_from_info(info) -> t.Optional[types.Profile]:
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


schema = g.Schema(query=Query, mutation=Mutation)
