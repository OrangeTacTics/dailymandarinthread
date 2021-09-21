import graphene as g

from chairmanmao.profile import get_all_profiles, get_profile
from chairmanmao.hanzi import get_seen_hanzi

from .utils import db_from_info, username_from_info, profile_from_info, assert_admin, profile_to_graphql
from .types import (
    Role,
    Profile,
    CreateProfile,
    IncrementSocialCredit,
    AddRole,
    RemoveRole,
    SeeHanzi,
    LeaderboardEntry,
)


class Query(g.ObjectType):
    me = g.Field(Profile)
    leaderboard = g.List(LeaderboardEntry)
    profile = g.Field(Profile, user_id=g.String())
    all_usernames = g.List(g.String)
    all_hanzi = g.List(g.String)
    find_profile = g.Field(Profile, query=g.String())

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

    def resolve_profile(root, info, user_id):
        assert_admin(info)
        profile = profile_from_info(info)

        db = db_from_info(info)
        profile = get_profile(db, int(user_id))

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

    def resolve_find_profile(root, info, query):
        assert_admin(info)
        print('query: ', query)

        db = db_from_info(info)
        for profile in get_all_profiles(db):
            if str(profile.user_id).startswith(query):
                return profile
            elif profile.discord_username.lower().startswith(query.lower()):
                return profile
            elif profile.display_name.lower().startswith(query.lower()):
                return profile

        return None


class Mutation(g.ObjectType):
    create_profile = CreateProfile.Field()
    increment_social_credit = IncrementSocialCredit.Field()
    see_hanzi = SeeHanzi.Field()
    add_role = AddRole.Field()
    remove_role = RemoveRole.Field()


schema = g.Schema(query=Query, mutation=Mutation)
