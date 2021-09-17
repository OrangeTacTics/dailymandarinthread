from __future__ import annotations
import typing as t
from dataclasses import dataclass

import os
from datetime import datetime, timezone

from dotenv import load_dotenv
import jwt
import pymongo

from chairmanmao.types import Profile, Role
from chairmanmao.profile import get_profile, create_profile, get_all_profiles, open_profile, get_user_id

from chairmanmao.hanzi import get_seen_hanzi
#from chairmanmao.draw import draw, get_font_names
#from chairmanmao.fourchan import get_dmt_thread, is_url_seen, see_url


UserId = int


@dataclass
class LeaderboardEntry:
    display_name: str
    credit: int


@dataclass
class Api:
    db: pymongo.MongoClient

    @staticmethod
    def connect(mongo_url: str, mongo_db: str) -> Api:
        mongo_client = pymongo.MongoClient(mongo_url)
        db = mongo_client[mongo_db]
        return Api(
            db=db,
        )

    def get_user_id(self, discord_username: str) -> UserId:
        return get_user_id(self.db, discord_username)

    def as_chairman(self) -> ChairmanApi:
        return ChairmanApi(
            db=self.db,
        )

    def as_party(self, user_id: UserId) -> PartyApi:
        return PartyApi(
            db=self.db,
            user_id=user_id,
        )
    def as_comrade(self, user_id: UserId) -> ComradeApi:
        return ComradeApi(
            db=self.db,
            user_id=user_id,
        )


@dataclass
class ChairmanApi:
    db: pymongo.MongoClient

    def get_profile(self, user_id: UserId) -> Profile:
        profile = get_profile(self.db, user_id)
        return profile

    def get_all_profiles(self) -> t.List[Profile]:
        profiles = get_all_profiles(self.db)
        return profiles

    def honor(self, user_id: UserId, credit: int) -> int:
        assert credit > 0
        with open_profile(self.db, user_id) as profile:
            profile.credit += credit
            return profile.credit

    def dishonor(self, user_id: UserId, credit: int) -> int:
        assert credit > 0
        with open_profile(self.db, user_id) as profile:
            profile.credit -= credit
            return profile.credit

    def set_name(self, user_id: UserId, name: str) -> None:
        assert len(name) < 32, 'Name must be 32 characters or less.'
        with open_profile(self.db, user_id) as profile:
            profile.display_name = name

    def list_users(self) -> t.List[UserId]:
        user_ids = []
        for profile in get_all_profiles(self.db):
            user_ids.append(profile.user_id)
        return user_ids

    def promote(self, user_id: UserId) -> None:
        with open_profile(self.db, user_id) as profile:
            if Role.Party not in profile.roles:
                profile.roles.append(Role.Party)
                profile.roles.sort()
            else:
                raise Exception("Already a party member")

    def demote(self, user_id: UserId) -> None:
        with open_profile(self.db, user_id) as profile:
            if Role.Party in profile.roles:
                profile.roles.remove(Role.Party)
                profile.roles.sort()
            else:
                raise Exception("Not a party member")

    def get_hsk(self, user_id: UserId) -> t.Optional[int]:
        level_by_role = {
            Role.Hsk1: 1,
            Role.Hsk2: 2,
            Role.Hsk3: 3,
            Role.Hsk4: 4,
            Role.Hsk5: 5,
            Role.Hsk6: 6,
        }

        profile = get_profile(self.db, user_id)
        for role, level in level_by_role.items():
            if role in profile.roles:
                return level

        return None

    def set_hsk(self, user_id: UserId, hsk_level: t.Optional[int]) -> None:
        role_by_level = {
            1: Role.Hsk1,
            2: Role.Hsk2,
            3: Role.Hsk3,
            4: Role.Hsk4,
            5: Role.Hsk5,
            6: Role.Hsk6,
        }

        with open_profile(self.db, user_id) as profile:
            # Remove all roles
            for role in role_by_level.values():
                remove_role(profile, role)

            if hsk_level is not None:
                # Then add the right one
                role_to_add = role_by_level[hsk_level]
                add_role(profile, role_to_add)


@dataclass
class PartyApi:
    db: pymongo.MongoClient
    user_id: UserId

    def recognize(self, user_id: UserId, discord_username: str):
        create_profile(self.db, user_id, discord_username)

    def jail(self, user_id: UserId) -> None:
        with open_profile(self.db, user_id) as profile:
            if Role.Jailed not in profile.roles:
                profile.roles.append(Role.Jailed)
                profile.roles.sort()
            else:
                raise Exception("Already jailed")

    def unjail(self, user_id: UserId) -> None:
        with open_profile(self.db, user_id) as profile:
            if Role.Jailed in profile.roles:
                profile.roles = sorted(role for role in profile.roles if role != Role.Jailed)
            else:
                raise Exception("Not jailed")

    def stepdown(self) -> None:
        with open_profile(self.db, self.user_id) as profile:
            if Role.Party in profile.roles:
                profile.roles = sorted(role for role in profile.roles if role != Role.Party)
            else:
                raise Exception("Not a party member")


@dataclass
class ComradeApi:
    db: pymongo.MongoClient
    user_id: UserId

    def get_discord_username(self, user_id: UserId) -> str:
        profile = get_profile(self.db, user_id)
        return profile.discord_username

    def get_display_name(self, user_id: UserId) -> str:
        profile = get_profile(self.db, user_id)
        return profile.display_name

    def social_credit(self, user_id: UserId) -> int:
        profile = get_profile(self.db, user_id)
        assert profile is not None
        return profile.credit

    def set_learner(self, flag: bool) -> None:
        with open_profile(self.db, self.user_id) as profile:
            if flag:
                profile.roles.append(Role.Learner)
            else:
                profile.roles = [role for role in profile.roles if role != Role.Learner]

            profile.roles = sorted(set(profile.roles))

    def draw(self, font_name: str, text: str) -> None:
        ...

    def upload_font(self, font_name: str, font_data: bytes) -> None:
        ...

    def mine(self, word: str) -> None:
        with open_profile(self.db, self.user_id) as profile:
            profile.mined_words.append(word)
            profile.mined_words = sorted(set(profile.mined_words))

    def get_mined(self) -> t.List[str]:
        profile = get_profile(self.db, self.user_id)
        assert profile is not None, f"No profile exists for {self.user_id}"
        return profile.mined_words

    def get_hanzis(self, user_id: UserId) -> t.List[str]:
        profile = get_profile(self.db, user_id)
        assert profile is not None, f"No profile exists for {user_id}"
        return profile.hanzi

    def yuan(self) -> int:
        profile = get_profile(self.db, self.user_id)
        assert profile is not None, f"No profile exists for {self.user_id}"
        return profile.yuan

    def leaderboard(self) -> t.List[LeaderboardEntry]:
        entries = []
        profiles = get_all_profiles(self.db)
        profiles.sort(reverse=True, key=lambda profile: profile.credit)

        for profile in profiles[:10]:
            entries.append(LeaderboardEntry(
                display_name=profile.display_name,
                credit=profile.credit,
            ))
        return entries

    def set_name(self, name: str) -> None:
        assert len(name) < 32, 'Name must be 32 characters or less.'
        with open_profile(self.db, self.user_id) as profile:
            profile.display_name = name

    def get_name(self) -> str:
        profile = get_profile(self.db, self.user_id)
        assert profile is not None, f"No profile exists for {self.user_id}"
        return profile.display_name

    def last_seen(self, user_id: UserId) -> datetime:
        profile = get_profile(self.db, user_id)
        assert profile is not None, f"No profile exists for {self.user_id}"
        last_seen = profile.last_seen
        last_seen = last_seen.replace(tzinfo=timezone.utc)
        last_seen = last_seen.replace(microsecond=0)
        return last_seen

    def see_hanzis(self, hanzis: t.List[str]) -> t.List[str]:
        seen_hanzis = get_seen_hanzi(self.db)
        new_hanzis = set(hanzis).difference(seen_hanzis)

        with open_profile(self.db, self.user_id) as profile:
            existing_hanzi = set(profile.hanzi)
            profile.hanzi = sorted(existing_hanzi.union(new_hanzis))
            return profile.hanzi

    def alert_activity(self) -> None:
        with open_profile(self.db, self.user_id) as profile:
            profile.last_seen = datetime.now(timezone.utc).replace(microsecond=0)


def add_role(profile: Profile, role: Role) -> bool:
    '''
        Returns whether the profile was changed.
    '''
    roles_set = set(profile.roles)
    if not role in roles_set:
        roles_set.add(role)
        profile.roles = sorted(roles_set)
        changed = True
    else:
        changed = False

    return changed



def remove_role(profile: Profile, role: Role) -> bool:
    '''
        Returns whether the profile was changed.
    '''
    roles_set = set(profile.roles)
    if role in roles_set:
        roles_set.remove(role)
        profile.roles = sorted(roles_set)
        changed = True
    else:
        changed = False

    return changed


def main():
    load_dotenv()

    MONGODB_URL = os.getenv('MONGODB_TEST_URL', '')
    MONGODB_DB = os.getenv('MONGODB_TEST_DB', '')

    api = Api.connect(MONGODB_URL, MONGODB_DB)

    user_id =  api.get_user_id('OrangeTacTics#0949')
    snickers_id = api.get_user_id('Snickers#0486')

    chairman_api = api.as_chairman()
    comrade_api = api.as_comrade(snickers_id)

    print('hanzis before', comrade_api.get_hanzis(snickers_id))
    comrade_api.see_hanzis(['喘', '猫'])
    print('hanzis after', comrade_api.get_hanzis(snickers_id))

    print(comrade_api.last_seen(snickers_id))
    comrade_api.alert_activity()
    print(comrade_api.last_seen(snickers_id))

    print('credit:', comrade_api.social_credit(user_id))

    comrade_api.mine('猫')

    for word in comrade_api.get_mined():
        print('-', word)

    print()
    print('Yuan:', comrade_api.yuan())

    for hanzi in comrade_api.get_hanzis(user_id)[:3]:
        print('-', hanzi)

    print('Display name:', comrade_api.get_name())
    comrade_api.set_name('Snick')
    print('Display name:', comrade_api.get_name())
    comrade_api.set_name('Snickers')
    print('Display name:', comrade_api.get_name())
    print()

    lines = [
        "The DMT Leaderboard",
        "```",
    ]
    for entry in comrade_api.leaderboard():
        line = f'{entry.credit} ... {entry.display_name}'
        lines.append(line)

    lines.append("```")
    print('\n'.join(lines))
    print()


    print('Snickers credit:', comrade_api.social_credit(snickers_id))
    print('dishonor 10...')
    chairman_api.dishonor(snickers_id, 10)
    print('Snickers credit:', comrade_api.social_credit(snickers_id))
    print('honor 11...')
    chairman_api.honor(snickers_id, 11)
    print('Snickers credit:', comrade_api.social_credit(snickers_id))
    print()

    for word in api.as_comrade(snickers_id).get_mined():
        print('-', word)
    print()

    last_seen = api.as_comrade(snickers_id).last_seen(snickers_id)
    last_seen = last_seen.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    havent_seen_in = now - last_seen
    print(snickers_id, 'was last seen', int(havent_seen_in.total_seconds() / 60), 'minutes ago')
    print('at', last_seen)
    print()


if __name__ == '__main__':
    main()
