from __future__ import annotations
import graphene as g

from chairmanmao.profile import create_profile, get_profile, set_profile
from chairmanmao.hanzi import see_hanzi
import chairmanmao.types as types

from .utils import db_from_info, assert_admin, profile_to_graphql


class Role(g.Enum):
    Comrade = "Comrade"
    Party = "Party"
    Learner = "Learner"
    Jailed = "Jailed"


class Profile(g.ObjectType):
    user_id = g.String()
    username = g.String()
    display_name = g.String()
    credit = g.Int()
    hanzi = g.List(g.String)
    mined_words = g.List(g.String)
    roles = g.List(Role)
    created = g.String()
    last_message = g.String()
    yuan = g.Int()


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
